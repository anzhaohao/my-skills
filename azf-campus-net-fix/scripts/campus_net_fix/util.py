# -*- coding: utf-8 -*-
"""通用工具：动态端口、无 shell 进程管理、**绕过 TUN 的**网络探测原语。

## 为什么所有测量都必须绑定物理网卡

当 Clash 的 TUN 模式开启时，OS 路由被 0.0.0.0/1 + 128.0.0.0/1 接管，实测后果：

  · 任何 UDP/53 查询都返回**同一个 fake-ip**（198.18.0.75）→ DNS 测量全废
  · 早先确认被丢包的 IP（108.162.198.60 / 54.249.62.143）也「连得上」→ TCP 测量全废
  · 出口 IP 变成代理出口（203.27.106.146 / SG），而不是校园网出口

因此本模块用 `IP_UNICAST_IF` 把所有探测 socket 绑到物理网卡。实测绑定后：
  · 本地地址从 198.18.0.1（TUN）变为 192.168.1.110（WLAN）
  · QUIC Version Negotiation 从「无回应」变为「OPEN 27 bytes」
  · mihomo 探测实例配 `interface-name` 后出口从 SG 变回 CN

约束：只依赖 Python 标准库（ctypes + socket + ssl），不调任何 shell。
"""
from __future__ import annotations

import json
import os
import platform
import socket
import ssl
import struct
import subprocess
import sys
import time
import urllib.parse

from . import netif

IS_WINDOWS = platform.system() == "Windows"
_CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0


def hostname() -> str:
    """稳定且可读的机器标识，用作机器档案文件名。"""
    raw = (platform.node() or "").strip()
    unsafe = '<>:"/\\|?*'
    safe = "".join("_" if (c in unsafe or ord(c) < 32) else c for c in raw)
    safe = " ".join(safe.split()).strip(" .")
    if not safe:
        import hashlib
        safe = "host-" + hashlib.sha1((raw or "unknown").encode("utf-8")).hexdigest()[:8]
    return safe


def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def is_ipv4(s: str) -> bool:
    parts = (s or "").split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# DNS over HTTPS（IP 直连，因此不依赖被劫持的 53 端口）
# ---------------------------------------------------------------------------
DOH_ENDPOINTS = [
    "https://223.6.6.6/resolve?name=%s&type=A",
    "https://1.12.12.12/resolve?name=%s&type=A",
    "https://120.53.53.53/resolve?name=%s&type=A",
    "https://223.5.5.5/resolve?name=%s&type=A",
]

_resolve_cache = {}


def _doh_endpoint_ip(endpoint: str):
    host = urllib.parse.urlsplit(endpoint).hostname
    if not host:
        return None, None
    if is_ipv4(host):
        return host, urllib.parse.urlsplit(endpoint).port or 443
    ips = _os_resolve(host)          # 域名的 DoH 端点只能先借系统解析引导
    return (ips[0] if ips else None), 443


def _os_resolve(host):
    try:
        return sorted({ai[4][0] for ai in socket.getaddrinfo(host, None, socket.AF_INET)})
    except Exception:
        return []


def resolve(host: str, use_cache: bool = True):
    """把域名解析成真实 IPv4 列表，**优先 DoH**（绕过 TUN 的 53 端口劫持）。"""
    if not host:
        return []
    if is_ipv4(host):
        return [host]
    if use_cache and host in _resolve_cache:
        return _resolve_cache[host]

    for endpoint in DOH_ENDPOINTS:
        ips = doh_query(host, endpoint)
        if ips:
            _resolve_cache[host] = ips
            return ips
    ips = _os_resolve(host)
    _resolve_cache[host] = ips
    return ips


def doh_query(domain: str, endpoint_tpl: str, timeout: float = 8.0):
    """DoH 查询。返回去重后的真实 A 记录（过滤 fake-ip 段）。"""
    url = endpoint_tpl % urllib.parse.quote(domain)
    ip, port = _doh_endpoint_ip(endpoint_tpl)
    if not ip:
        return []
    path = urllib.parse.urlsplit(url).path or "/"
    query = urllib.parse.urlsplit(url).query
    if query:
        path += "?" + query
    sni = urllib.parse.urlsplit(endpoint_tpl).hostname
    status, _headers, body = _http_exchange(
        ip, port, sni, path, host_header=sni, timeout=timeout, tls=True)
    if status != 200 or not body:
        return []
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return []
    ips = [a.get("data") for a in data.get("Answer", []) if a.get("type") == 1]
    return sorted({i for i in ips
                   if is_ipv4(i) and not i.startswith("198.18.") and not i.startswith("198.19.")})


# ---------------------------------------------------------------------------
# 底层：绑定物理网卡的 socket
# ---------------------------------------------------------------------------
def _connect(host, port, timeout):
    """在物理网卡上建立 TCP 连接（域名会先经 DoH 解析）。"""
    ips = resolve(host)
    if not ips:
        raise socket.gaierror("无法解析 %s" % host)
    last = None
    for ip in ips:
        s = netif.new_socket(socket.AF_INET, socket.SOCK_STREAM, netif.default_ifindex())
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            return s
        except Exception as e:  # noqa: BLE001
            last = e
            s.close()
    raise last or OSError("connect failed")


def tcp_connect(host: str, port: int, timeout: float = 4.0) -> bool:
    """TCP 握手是否成功（在物理网卡上，因此不受 TUN 影响）。"""
    try:
        _connect(host, port, timeout).close()
        return True
    except Exception:
        return False


def udp_exchange(host: str, port: int, payload: bytes, timeout: float = 4.0):
    """绑定物理网卡的 UDP 收发。返回响应 bytes；无响应返回 None。"""
    s = netif.new_socket(socket.AF_INET, socket.SOCK_DGRAM, netif.default_ifindex())
    s.settimeout(timeout)
    try:
        s.sendto(payload, (host, port))
        data, _ = s.recvfrom(4096)
        return data
    except Exception:
        return None
    finally:
        s.close()


def udp_dns_query(domain: str, server: str, port: int = 53, timeout: float = 4.0):
    """裸 UDP DNS 查询（绑定物理网卡）。

    注意：TUN 开启且未绑定时，**所有**服务器都会返回同一个 fake-ip —— 绑定后
    才反映真实可达性。
    """
    tid = os.urandom(2)
    pkt = tid + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    for part in domain.split("."):
        pkt += bytes([len(part)]) + part.encode()
    pkt += b"\x00\x00\x01\x00\x01"

    data = udp_exchange(server, port, pkt, timeout=timeout)
    if not data or len(data) < 12:
        return []
    try:
        i = _skip_name(data, 12) + 4
    except Exception:
        return []
    ips = []
    while i + 10 <= len(data):
        i = _skip_name(data, i)
        if i + 10 > len(data):
            break
        rtype, _cls, _ttl, rdlen = struct.unpack("!HHIH", data[i:i + 10])
        i += 10
        if rtype == 1 and rdlen == 4 and i + 4 <= len(data):
            ips.append(".".join(str(b) for b in data[i:i + 4]))
        i += rdlen
    return ips


def _skip_name(data: bytes, i: int) -> int:
    while i < len(data):
        if data[i] & 0xC0 == 0xC0:
            return i + 2
        if data[i] == 0:
            return i + 1
        i += data[i] + 1
    return i


def quic_vn_probe(host: str, port: int = 443, timeout: float = 4.0) -> bool:
    """QUIC 版本协商探测：发服务器不支持的版本，期待 Version Negotiation。

    收到任何 UDP 回应即证明该 IP:port 的 UDP 通道通畅（绑定物理网卡后有效）。
    """
    dcid, scid = os.urandom(8), os.urandom(8)
    pkt = bytearray([0xC0]) + struct.pack("!I", 0xFF00001D)
    pkt.append(len(dcid)); pkt += dcid
    pkt.append(len(scid)); pkt += scid
    pkt.append(0x00)
    pkt += struct.pack("!I", 0)
    pkt += b"\x00" * 32
    if len(pkt) < 1200:
        pkt += b"\x00" * (1200 - len(pkt))
    return udp_exchange(host, port, bytes(pkt), timeout=timeout) is not None


def tls_probe(host: str, sni: str, port: int = 443, timeout: float = 6.0):
    """对 host:port 发起带指定 SNI 的 TLS 握手（绑定物理网卡）。

    返回 (outcome, detail)：
      ok / tls_error / reset / timeout / dns_error / error
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    raw = None
    try:
        raw = _connect(host, port, timeout)
        with ctx.wrap_socket(raw, server_hostname=sni) as s:
            return "ok", s.version() or "connected"
    except ssl.SSLError as e:
        return "tls_error", str(e)[:120]
    except ConnectionResetError:
        return "reset", "connection reset"
    except socket.timeout:
        return "timeout", "no response"
    except socket.gaierror as e:
        return "dns_error", str(e)[:120]
    except OSError as e:
        msg = str(e)
        low = msg.lower()
        if "10053" in msg or "10054" in msg or "aborted" in low or "reset" in low:
            return "reset", msg[:120]
        return "error", msg[:120]
    except Exception as e:  # noqa: BLE001
        return "error", str(e)[:120]
    finally:
        if raw is not None:
            try:
                raw.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 极简 HTTP 客户端（绑定物理网卡；支持走本地代理）
# ---------------------------------------------------------------------------
def _http_exchange(ip, port, sni, path, host_header, timeout=15.0, tls=True,
                   method="GET", extra_headers=None):
    """返回 (status, headers_dict, body_bytes)。失败返回 (None, {}, b"")。"""
    s = None
    try:
        s = netif.new_socket(socket.AF_INET, socket.SOCK_STREAM, netif.default_ifindex())
        s.settimeout(timeout)
        s.connect((ip, port))
        if tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(s, server_hostname=sni)
        req = ["%s %s HTTP/1.1" % (method, path),
               "Host: %s" % host_header,
               "User-Agent: azf-campus-net-fix/1.0",
               "Accept: */*",
               "Connection: close"]
        for k, v in (extra_headers or {}).items():
            req.append("%s: %s" % (k, v))
        s.sendall(("\r\n".join(req) + "\r\n\r\n").encode())

        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if len(buf) > 4 * 1024 * 1024:
                break
    except Exception:
        return None, {}, b""
    finally:
        if s is not None:
            try:
                s.close()
            except Exception:
                pass

    head, _, body = buf.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    if not lines:
        return None, {}, b""
    try:
        status = int(lines[0].split(b" ")[1])
    except Exception:
        return None, {}, b""
    headers = {}
    for ln in lines[1:]:
        if b":" in ln:
            k, _, v = ln.partition(b":")
            headers[k.decode("latin-1").strip().lower()] = v.decode("latin-1").strip()
    if headers.get("transfer-encoding", "").lower() == "chunked":
        body = _dechunk(body)
    return status, headers, body


def _dechunk(data: bytes) -> bytes:
    out = b""
    i = 0
    while i < len(data):
        j = data.find(b"\r\n", i)
        if j < 0:
            break
        try:
            n = int(data[i:j].split(b";")[0], 16)
        except Exception:
            break
        if n == 0:
            break
        out += data[j + 2:j + 2 + n]
        i = j + 2 + n + 2
    return out


def _parse_url(url):
    u = urllib.parse.urlsplit(url)
    tls = u.scheme == "https"
    path = u.path or "/"
    if u.query:
        path += "?" + u.query
    return u.hostname, (u.port or (443 if tls else 80)), path, tls, u.netloc


def _via_proxy(proxy: str, url: str, timeout: float):
    """经本地 HTTP 代理请求（HTTPS 走 CONNECT 隧道）。返回 (status, headers, body)。"""
    pu = urllib.parse.urlsplit(proxy)
    phost, pport = pu.hostname, (pu.port or 80)
    host, port, path, tls, netloc = _parse_url(url)
    s = None
    try:
        s = socket.create_connection((phost, pport), timeout=timeout)
        s.settimeout(timeout)
        if tls:
            s.sendall(("CONNECT %s:%d HTTP/1.1\r\nHost: %s:%d\r\n\r\n"
                       % (host, port, host, port)).encode())
            head = _read_head(s)
            if not head or b" 200" not in head.split(b"\r\n")[0]:
                return None, {}, b""
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(s, server_hostname=netloc)
            target = path
        else:
            target = url
        req = ["GET %s HTTP/1.1" % target, "Host: %s" % netloc,
               "User-Agent: azf-campus-net-fix/1.0", "Accept: */*",
               "Connection: close"]
        s.sendall(("\r\n".join(req) + "\r\n\r\n").encode())
        buf = b""
        while len(buf) < 4 * 1024 * 1024:
            try:
                chunk = s.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            buf += chunk
    except Exception:
        return None, {}, b""
    finally:
        if s is not None:
            try:
                s.close()
            except Exception:
                pass

    head, _, body = buf.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    if not lines:
        return None, {}, b""
    try:
        status = int(lines[0].split(b" ")[1])
    except Exception:
        return None, {}, b""
    headers = {}
    for ln in lines[1:]:
        if b":" in ln:
            k, _, v = ln.partition(b":")
            headers[k.decode("latin-1").strip().lower()] = v.decode("latin-1").strip()
    if headers.get("transfer-encoding", "").lower() == "chunked":
        body = _dechunk(body)
    return status, headers, body


def _read_head(sock, limit: int = 65536):
    buf = b""
    while b"\r\n\r\n" not in buf and len(buf) < limit:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            break
        if not chunk:
            break
        buf += chunk
    return buf


def http_get_body(url: str, proxy: str = None, timeout: float = 15.0):
    """返回 (status, headers, body, final_url)。

    未指定 proxy 时**绑定物理网卡**直连（不受 TUN 影响）；
    指定 proxy 时走本地代理端口（用于验证用户 Clash 的实际效果）。
    """
    if proxy:
        status, headers, body = _via_proxy(proxy, url, timeout)
        return status, headers, body, url

    host, port, path, tls, netloc = _parse_url(url)
    if not host:
        return None, {}, b"", None
    for ip in resolve(host):
        status, headers, body = _http_exchange(
            ip, port, netloc, path, host_header=netloc, timeout=timeout, tls=tls)
        if status is not None:
            return status, headers, body, url
    return None, {}, b"", None


def http_get(url: str, proxy: str = None, timeout: float = 15.0):
    """返回 (status, length, headers, final_url)。"""
    status, headers, body, final = http_get_body(url, proxy=proxy, timeout=timeout)
    return status, len(body), headers, final


def http_probe_no_redirect(url: str, timeout: float = 8.0):
    """不跟随重定向，用于 portal 检测。返回 (status, location)。"""
    host, port, path, tls, netloc = _parse_url(url)
    ips = resolve(host)
    for ip in ips:
        status, headers, _body = _http_exchange(
            ip, port, netloc, path, host_header=netloc, timeout=timeout, tls=tls)
        if status is not None:
            return status, headers.get("location")
    return None, None


def icmp_ok(host: str, timeout: int = 2):
    """ICMP 可达性。

    注意：走系统 ping，**不受我们的接口绑定约束**，因此 TUN 开启时结果可能被
    代理路径影响。画像里会标注 measured_via=os-path。
    """
    cmd = (["ping", "-n", "1", "-w", str(timeout * 1000), host] if IS_WINDOWS
           else ["ping", "-c", "1", "-W", str(timeout), host])
    try:
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=timeout + 3, creationflags=_CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception:
        return None


# ---------------------------------------------------------------------------
# mihomo 探测实例
# ---------------------------------------------------------------------------
class ProbeCore:
    """独立的 mihomo 实测实例。

    两个关键点：
      1. 配 `interface-name` 绑定物理网卡 —— 否则连它自己也会被用户 TUN 接管
         （实测：绑定前出口 SG，绑定后出口 CN）
      2. 按 Popen 句柄直接终止 —— 不调 PowerShell，换机器后无 shell 依赖
    """

    def __init__(self, exe: str, workdir: str, config: dict, bind_interface: bool = True):
        self.exe = exe
        self.workdir = workdir
        self.api_port = free_port()
        self.mixed_port = free_port()
        self._proc = None
        self._config_path = os.path.join(workdir, "config.yaml")
        self.ifname = netif.default_ifname() if bind_interface else None

        os.makedirs(workdir, exist_ok=True)
        cfg = dict(config)
        cfg["mixed-port"] = self.mixed_port
        cfg["external-controller"] = "127.0.0.1:%d" % self.api_port
        if self.ifname:
            cfg["interface-name"] = self.ifname
        cfg.setdefault("dns", {})
        cfg["dns"].update({
            "enable": True, "ipv6": False, "enhanced-mode": "normal",
            "nameserver": ["119.29.29.29", "223.6.6.6", "114.114.114.114"],
        })

        from . import yamlcompat
        yamlcompat.dump(cfg, self._config_path)

    @property
    def api(self) -> str:
        return "http://127.0.0.1:%d" % self.api_port

    @property
    def proxy_url(self) -> str:
        return "http://127.0.0.1:%d" % self.mixed_port

    def __enter__(self) -> "ProbeCore":
        log = open(os.path.join(self.workdir, "probe.log"), "w", encoding="utf-8",
                   errors="replace")
        self._proc = subprocess.Popen(
            [self.exe, "-d", self.workdir, "-f", self._config_path],
            stdout=log, stderr=subprocess.STDOUT, creationflags=_CREATE_NO_WINDOW)
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                import urllib.request
                with urllib.request.urlopen(self.api + "/version", timeout=2) as r:
                    if r.status == 200:
                        json.loads(r.read().decode())
                        return self
            except Exception:
                time.sleep(0.4)
        self.__exit__(None, None, None)
        raise RuntimeError("mihomo 探测实例启动失败（API 未就绪），日志见 %s"
                           % os.path.join(self.workdir, "probe.log"))

    def __exit__(self, *exc):
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=6)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None
        return False

    def _api_get(self, path, timeout=25.0):
        import urllib.request
        with urllib.request.urlopen(self.api + path, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def delay(self, proxy_name: str, url: str = "http://www.gstatic.com/generate_204",
              timeout_ms: int = 6000, http_timeout: float = 25.0):
        q = "/proxies/%s/delay?url=%s&timeout=%d" % (
            urllib.parse.quote(proxy_name, safe=""),
            urllib.parse.quote(url, safe=""), timeout_ms)
        try:
            return self._api_get(q, timeout=http_timeout).get("delay")
        except Exception:
            return None

    def delay_many(self, names, url: str = "http://www.gstatic.com/generate_204",
                   timeout_ms: int = 5000, workers: int = 12):
        from concurrent.futures import ThreadPoolExecutor

        def one(n):
            return n, self.delay(n, url=url, timeout_ms=timeout_ms,
                                 http_timeout=timeout_ms / 1000.0 + 14)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            return dict(ex.map(one, names))

    def select(self, group: str, name: str) -> bool:
        import urllib.request
        try:
            req = urllib.request.Request(
                "%s/proxies/%s" % (self.api, urllib.parse.quote(group, safe="")),
                method="PUT", data=json.dumps({"name": name}).encode(),
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=8).read()
            return True
        except Exception:
            return False

    def version(self):
        try:
            return self._api_get("/version", timeout=5).get("version")
        except Exception:
            return None

    def outbound_exit(self, timeout: float = 20.0):
        """读探测实例的出口信息，用于验证它真的绕过了用户 TUN。

        这是画像可信度的**自检**：若出口 loc 与本地代理出口相同，
        说明绑定没生效，此时所有实测都不可信。
        """
        status, _h, body, _u = http_get_body(
            "https://www.cloudflare.com/cdn-cgi/trace",
            proxy=self.proxy_url, timeout=timeout)
        if not status or not body:
            return None
        out = {}
        for line in body.decode("utf-8", "replace").splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                if k in ("ip", "loc", "colo", "warp"):
                    out[k] = v
        return out or None
