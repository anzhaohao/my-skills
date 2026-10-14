# -*- coding: utf-8 -*-
"""网络画像：判定封锁发生在哪一层。

这一层是「换校园网也能用」的关键 —— 输出**事实与判定**，而不是绑定某个
校园网的结论。策略选择由 strategy.py 依据 verdict 完成。

## TUN 污染自检（本模块最关键的设计）

当用户的 Clash 开启 TUN 时，OS 路由被接管，本地 socket 的一切测量都会失真：
实测所有 DNS 服务器返回同一个 fake-ip、确认被丢包的 IP 也「连得上」。
因此本模块：

  1. 所有原始测量都通过 util 绑定物理网卡（IP_UNICAST_IF）
  2. `probe_channel()` 做**差分自检**：比较探测实例出口与本地 OS 出口
  3. 若自检失败（两者相同且 TUN 开启），画像标记 degraded 并拒绝给出可信判定
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from . import cfnets
from . import clashverge as cv
from . import envprobe
from . import netif
from .util import (ProbeCore, doh_query, hostname, http_get_body, http_probe_no_redirect,
                   icmp_ok, iso_now, quic_vn_probe, resolve, tcp_connect, tls_probe,
                   udp_dns_query)

SCHEMA_VERSION = 1

UDP53_CANDIDATES = ["119.29.29.29", "223.5.5.5", "223.6.6.6", "114.114.114.114",
                    "180.76.76.76", "1.1.1.1", "8.8.8.8"]

# Cloudflare 提供 HTTP/3 的端口集合 —— 用于刻画 UDP 端口策略，无需第三方服务
QUIC_PROBE_PORTS = [443, 8443, 2053, 2083, 2087, 2096]

DNS_TEST_DOMAIN = "www.baidu.com"
TRACE_URL = "https://www.cloudflare.com/cdn-cgi/trace"


def profile_path(host: str = None) -> str:
    return os.path.join(envprobe.DATA_DIR, "profile.%s.json" % (host or hostname()))


def load_profile(host: str = None, max_age_sec: float = 0.0):
    p = profile_path(host)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return None
    if max_age_sec and (time.time() - data.get("_saved_at", 0)) > max_age_sec:
        return None
    return data


def save_profile(prof: dict) -> str:
    os.makedirs(envprobe.DATA_DIR, exist_ok=True)
    prof["_saved_at"] = time.time()
    p = profile_path(prof.get("host"))
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(prof, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return p


def _trace_via(proxy=None, timeout: float = 20.0):
    status, _h, body, _u = http_get_body(TRACE_URL, proxy=proxy, timeout=timeout)
    if not status or not body:
        return None
    out = {}
    for line in body.decode("utf-8", "replace").splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            if k in ("ip", "loc", "colo"):
                out[k] = v
    return out or None


# ---------------------------------------------------------------------------
# 测量通道自检
# ---------------------------------------------------------------------------
def probe_channel(core_exe: str, workdir: str, tun_enabled: bool):
    """自检：确认原始测量真的绕过了用户 TUN。

    判据设计（实测依据，2026-10-14）：

      TUN 开启且未绑定时，任何 UDP/53 查询都返回**同一个 fake-ip**（198.18.0.75），
      被丢包的 IP 也「连得上」。绑定物理网卡后，223.5.5.5 / 8.8.8.8 恢复为
      **无响应**（与真实封锁一致），119.29.29.29 返回真实 IP。

    因此主判据 = 绑定后的 UDP/53 是否拿到**真实**（非 fake-ip）地址。
    次判据（主判据无响应时）= 绑定与不绑定的 QUIC 探测差分。

    注意：**不能**用「探测出口 ≠ 本地出口」作判据 —— 本地路径也可能恰好走
    DIRECT，两条通道同为真实出口时是正常的（会误判）。
    """
    out = {
        "physical_interface": netif.default_ifname(),
        "physical_ifindex": netif.default_ifindex(),
        "tun_enabled": bool(tun_enabled),
        "dns_bound": {},
        "dns_unbound_fakeip": None,
        "probe_exit": None,
        "os_exit": None,
        "raw_channel_ok": None,
        "basis": None,
        "note": None,
    }
    if not out["physical_interface"]:
        out["note"] = "未识别到物理网卡，无法绑定，测量不可信"
        out["raw_channel_ok"] = False
        out["basis"] = "no-physical-interface"
        return out

    # --- 主判据：绑定后的 UDP/53 是否返回真实地址 ---
    for srv in ("119.29.29.29", "114.114.114.114", "223.6.6.6"):
        out["dns_bound"][srv] = udp_dns_query(DNS_TEST_DOMAIN, srv, timeout=4)
    real = [s for s, ips in out["dns_bound"].items()
            if ips and not any(i.startswith("198.18.") or i.startswith("198.19.")
                               for i in ips)]
    fake = [s for s, ips in out["dns_bound"].items()
            if ips and any(i.startswith("198.18.") or i.startswith("198.19.")
                           for i in ips)]
    if real:
        out["raw_channel_ok"] = True
        out["basis"] = "dns-bound-real"
        out["note"] = "绑定生效：UDP/53 拿到真实地址（%s）" % ", ".join(real)
    elif fake:
        out["raw_channel_ok"] = False
        out["basis"] = "dns-bound-fakeip"
        out["note"] = ("绑定未生效：UDP/53 仍返回 fake-ip（%s）—— 测量不可信"
                       % ", ".join(fake))
        return out

    # --- 次判据：QUIC 绑定与不绑定差分 ---
    if out["raw_channel_ok"] is None:
        bound = quic_vn_probe("188.114.96.1", 443, timeout=4)
        s = netif.new_socket(socket.AF_INET, socket.SOCK_DGRAM, None)
        unbound = False
        try:
            import struct as _s
            dcid, scid = os.urandom(8), os.urandom(8)
            pkt = bytearray([0xC0]) + _s.pack("!I", 0xFF00001D)
            pkt.append(len(dcid)); pkt += dcid
            pkt.append(len(scid)); pkt += scid
            pkt.append(0x00); pkt += _s.pack("!I", 0)
            pkt += b"\x00" * 32
            pkt += b"\x00" * (1200 - len(pkt))
            s.settimeout(4)
            s.sendto(bytes(pkt), ("188.114.96.1", 443))
            s.recvfrom(4096)
            unbound = True
        except Exception:
            unbound = False
        finally:
            s.close()
        out["quic_bound"] = bound
        out["quic_unbound"] = unbound
        if bound and not unbound:
            out["raw_channel_ok"] = True
            out["basis"] = "quic-differential"
            out["note"] = "绑定生效（QUIC 差分：绑定通、不绑定不通）"
        elif bound and unbound:
            out["raw_channel_ok"] = None
            out["basis"] = "quic-inconclusive"
            out["note"] = "QUIC 两条通道都通，无法区分 —— 结果按保守处理"
        else:
            out["raw_channel_ok"] = False
            out["basis"] = "quic-bound-fail"
            out["note"] = "绑定通道也不通，测量不可信"

    # --- 附带信息：两条通道的出口（仅供人工参考，不作判据）---
    cfg = {"allow-lan": False, "mode": "rule", "log-level": "warning", "ipv6": False,
           "proxies": [{"name": "D", "type": "direct"}],
           "proxy-groups": [{"name": "G", "type": "select", "proxies": ["D"]}],
           "rules": ["MATCH,G"]}
    try:
        with ProbeCore(core_exe, os.path.join(workdir, "channel"), cfg) as core:
            out["probe_exit"] = _trace_via(core.proxy_url, timeout=20)
    except Exception as e:  # noqa: BLE001
        out["probe_exit"] = {"error": str(e)[:80]}
    out["os_exit"] = _trace_via(None, timeout=20)
    return out


# ---------------------------------------------------------------------------
# 单项探测
# ---------------------------------------------------------------------------
def probe_baseline():
    """外网基线 + portal 检测（全部走绑定通道）。"""
    out = {"internet": False, "portal_redirect": False, "portal_url": None,
           "domestic_ok": False, "overseas_ok": False, "icmp_ok": None}

    s, _h, _b, _u = http_get_body("http://www.baidu.com", timeout=8)
    out["domestic_ok"] = bool(s)
    s2, _h2, _b2, _u2 = http_get_body("https://github.com", timeout=12)
    out["overseas_ok"] = bool(s2)
    out["internet"] = out["domestic_ok"] or out["overseas_ok"]

    for url in ("http://connect.rom.miui.com/generate_204", "http://www.baidu.com"):
        status, loc = http_probe_no_redirect(url, timeout=6)
        if status in (301, 302, 303, 307, 308) and loc:
            host = loc.split("/")[2].lower() if "//" in loc else loc.lower()
            if not any(k in host for k in ("baidu", "miui", "xiaomi")):
                out["portal_redirect"] = True
                out["portal_url"] = loc
                break

    out["icmp_ok"] = icmp_ok("223.6.6.6")
    return out


def probe_dns():
    """UDP53 与 DoH 候选池实测；检测 fake-ip 劫持。

    不硬编码「哪个 DNS 可用」——今日实测 223.5.5.5 被校园网丢弃而 223.6.6.6
    正常，换个校园网可能正好相反。
    """
    out = {"udp53_ok": [], "udp53_blocked": [], "doh_ok": [], "doh_failed": [],
           "fakeip_hijack": False, "answers": {}, "hijack_suspect": False}

    def _udp(server):
        return server, udp_dns_query(DNS_TEST_DOMAIN, server, timeout=4)

    with ThreadPoolExecutor(max_workers=7) as ex:
        results = list(ex.map(_udp, UDP53_CANDIDATES))

    for server, ips in results:
        if ips:
            out["answers"][server] = ips
            if any(i.startswith("198.18.") or i.startswith("198.19.") for i in ips):
                out["fakeip_hijack"] = True
            else:
                out["udp53_ok"].append(server)
        else:
            out["udp53_blocked"].append(server)

    # 劫持特征：多个不同服务器返回完全相同的答案
    distinct = {tuple(v) for v in out["answers"].values()}
    if len(out["answers"]) >= 3 and len(distinct) == 1:
        sample = next(iter(distinct))
        if all(i.startswith("198.18.") or i.startswith("198.19.") for i in sample):
            out["hijack_suspect"] = True

    def _doh(ep):
        return ep, doh_query(DNS_TEST_DOMAIN, ep)

    from .util import DOH_ENDPOINTS
    with ThreadPoolExecutor(max_workers=4) as ex:
        for ep, ips in ex.map(_doh, DOH_ENDPOINTS):
            (out["doh_ok"] if ips else out["doh_failed"]).append(ep)
    return out


def probe_cf(workers: int = 16):
    """抽样 Cloudflare anycast IP 的 TCP 443 可达率（绑定通道）。"""
    def one(ip):
        return ip, tcp_connect(ip, 443, timeout=4)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(one, cfnets.CF_CANDIDATES))
    good = [ip for ip, ok in res if ok]
    return {"sampled": len(res), "reachable": len(good),
            "ratio": round(len(good) / max(len(res), 1), 3),
            "working_ips": good,
            "blocked_ips": [ip for ip, ok in res if not ok]}


def probe_udp_ports(hosts=None, timeout: float = 3.0):
    """用 Cloudflare 的 HTTP/3 端口集合刻画 UDP 端口策略。"""
    hosts = hosts or ["188.114.96.1", "162.159.192.1", "104.16.0.1"]
    tasks = [(h, p) for h in hosts for p in QUIC_PROBE_PORTS]

    def one(t):
        h, p = t
        return t, quic_vn_probe(h, p, timeout=timeout)

    with ThreadPoolExecutor(max_workers=10) as ex:
        res = dict(ex.map(one, tasks))

    by_port = {str(p): sum(1 for h in hosts if res.get((h, p)))
               for p in QUIC_PROBE_PORTS}
    return {"hosts": hosts, "ports_tested": QUIC_PROBE_PORTS,
            "open_count_by_port": by_port,
            "udp443_ok": by_port.get("443", 0) > 0,
            "detail": {"%s:%d" % k: v for k, v in res.items()}}


def probe_sni(working_ips):
    """**通用** SNI 层过滤探测（信息性，不单独决定 verdict）。

    对照组：同一 IP + 正常 SNI 应当有 TLS 响应。
    实验组：同一 IP + 知名被封 SNI（google / youtube）。

    重要：这一项测到「blocked」通常反映的是**国家级 SNI 过滤**，它在热点上
    同样存在，**不代表机场节点不可用**（节点用的是自己的 SNI）。因此本项只作
    为事实记录，verdict 由 `probe_sni_node` 与优选 IP 实测共同决定。
    """
    control_sni = "www.cloudflare.com"
    test_snis = ["www.google.com", "www.youtube.com"]
    out = {"verdict": "unknown", "scope": "generic-wellknown-sni", "evidence": []}

    candidates = list(working_ips or [])[:4]
    if not candidates:
        out["evidence"].append("没有可达的境外 IP 作对照，无法判定")
        return out

    for ip in candidates:
        c_status, _ = tls_probe(ip, control_sni, timeout=6)
        if c_status not in ("ok", "tls_error"):
            out["evidence"].append("%s + %s → %s（对照不成立，跳过）"
                                   % (ip, control_sni, c_status))
            continue
        for sni in test_snis:
            t_status, _ = tls_probe(ip, sni, timeout=6)
            out["evidence"].append("%s + %s → %s（对照 %s → %s）"
                                   % (ip, sni, t_status, control_sni, c_status))
            if t_status in ("reset", "timeout"):
                out["verdict"] = "blocked"
                out["blocked_sni"] = sni
                out["control"] = {"ip": ip, "sni": control_sni, "status": c_status}
                return out
        out["verdict"] = "clean"
        return out

    out["evidence"].append("所有候选 IP 的 TLS 对照均不成立，判定为 unknown")
    return out


def probe_sni_node(subs, working_ips):
    """按**节点真实 SNI** 探测 TLS 层是否被阻断 —— 这才是与策略相关的信号。

    对每个 Cloudflare 前置节点，取其真实 SNI，对一个**可达的 CF IP** 发起
    TLS 握手：若对照 SNI 正常而节点 SNI 被 reset/超时，说明该节点入口在
    TLS 层被阻断，换 IP 也救不回来。
    """
    control_sni = "www.cloudflare.com"
    out = {"verdict": "unknown", "scope": "node-real-sni", "tested": [], "evidence": []}

    ips = list(working_ips or [])[:3]
    if not ips:
        out["evidence"].append("没有可达的 CF IP 作对照，无法判定节点 SNI")
        return out

    # 收集去重后的节点 SNI
    snis = []
    for sub in subs:
        for p in sub.get("proxies") or []:
            if not cfnets.looks_cdn_fronted(p):
                continue
            sni = p.get("servername") or p.get("sni") or ""
            if sni and sni not in snis:
                snis.append(sni)
    if not snis:
        out["evidence"].append("订阅里没有 Cloudflare 前置节点，无需判定")
        return out

    for ip in ips:
        c_status, _ = tls_probe(ip, control_sni, timeout=6)
        if c_status not in ("ok", "tls_error"):
            continue
        blocked, clean = [], []
        for sni in snis[:8]:
            st, _ = tls_probe(ip, sni, timeout=6)
            out["tested"].append({"ip": ip, "sni": sni, "status": st})
            (blocked if st in ("reset", "timeout") else clean).append(sni)
        out["evidence"].append("via %s：对照 %s → %s；节点 SNI 正常 %d 个 / 异常 %d 个"
                               % (ip, control_sni, c_status, len(clean), len(blocked)))
        if blocked and not clean:
            out["verdict"] = "blocked"
            out["blocked_sni"] = blocked[:5]
        elif clean:
            out["verdict"] = "clean"
        return out

    out["evidence"].append("所有候选 IP 的 TLS 对照均不成立，判定为 unknown")
    return out


def probe_ipv6():
    """IPv6 可用性：有无全局地址 + 能否走通。

    注意：IPv6 不走物理网卡绑定（TUN 通常只接管 IPv4），因此结果仅供参考。
    """
    out = {"global_addresses": [], "reachable": False, "binding": "none"}
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6):
            ip = info[4][0].split("%")[0]
            if ip and not ip.startswith("fe80") and ip != "::1":
                out["global_addresses"].append(ip)
    except Exception:
        pass
    out["global_addresses"] = sorted(set(out["global_addresses"]))
    if out["global_addresses"]:
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(("2400:3200::1", 53))       # AliDNS IPv6
            s.close()
            out["reachable"] = True
        except Exception:
            out["reachable"] = False
    return out


# ---------------------------------------------------------------------------
# verdict
# ---------------------------------------------------------------------------
def decide_verdict(p: dict) -> str:
    """把画像事实归约为一个主判定。

    A  IP 层黑名单（部分）—— 换入口 IP 已被实测证明可行
    B  SNI/TLS 层阻断    —— 换 IP 无效
    C  协议/端口层封锁   —— 需要换协议
    D  portal 认证       —— 超出本技能范围
    E  未发现封锁        —— 幂等退出
    X  未知（含测量通道不可信）

    判定顺序的关键（实测教训）：**必须先用「优选 IP 实测是否可行」来决定 A**，
    而不能用「知名被封 SNI 是否被拦」来决定 B —— 后者反映的是国家级 SNI 过滤，
    在手机热点上同样存在，与机场节点能否使用无关（节点用的是自己的 SNI）。
    """
    ch = p.get("channel") or {}
    if ch.get("raw_channel_ok") is False:
        return "X"          # 测量通道不可信，不给判定

    base = p.get("baseline") or {}
    if base.get("portal_redirect"):
        return "D"
    if not base.get("internet"):
        return "X"

    nodes = p.get("nodes") or {}
    total = nodes.get("total") or 0
    reach = nodes.get("reachable") or 0
    if total and reach / total >= 0.9:
        return "E"

    layers = p.get("layers") or {}
    cf = p.get("cf") or {}
    pref = p.get("cf_preferred") or {}
    has_cf_nodes = bool(p.get("cf_fronted_domains"))

    # 策略 A 的可行性：实测确实存在可用的优选 IP，且订阅里有可换的 CF 前置节点
    if (pref.get("working") or 0) > 0 and has_cf_nodes:
        return "A"

    # A 不可行时，再判断封锁形态（此时 SNI 探针才有区分意义）
    if (layers.get("sni_node") or {}).get("verdict") == "blocked":
        return "B"
    if (layers.get("sni") or {}).get("verdict") == "blocked" and not has_cf_nodes:
        return "B"
    if (cf.get("reachable") or 0) == 0:
        udp = layers.get("udp_ports") or {}
        if udp and not udp.get("udp443_ok"):
            return "C"
    return "X"


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def build(env: dict, do_cfip: bool = True, do_reach: bool = True, log=print) -> dict:
    from . import cfip as cfip_mod
    from . import reach as reach_mod

    t0 = time.time()
    core_exe = env["core"]["exe"]
    workdir = os.path.join(envprobe.DATA_DIR, "probe-work")
    tun_enabled = bool(env["client"].get("tun_enabled"))

    subs = []
    for s in env["subscriptions"]:
        loaded = cv.read_subscription(s["path"])
        if loaded:
            subs.append({"name": s["name"], "uid": s["uid"], "path": s["path"],
                         "proxies": loaded["proxies"]})

    log("  [1/7] 测量通道自检（TUN 是否污染测量）")
    channel = probe_channel(core_exe, workdir, tun_enabled)
    if not channel["raw_channel_ok"]:
        log("        ⚠ %s" % channel["note"])
    else:
        log("        通道正常：%s" % channel["note"])

    log("  [2/7] 基线连通性与 portal 检测")
    baseline = probe_baseline()

    log("  [3/7] DNS 候选池实测")
    dns = probe_dns()

    log("  [4/7] Cloudflare anycast 抽样")
    cf = probe_cf()

    log("  [5/7] UDP 端口策略 / SNI 层 / IPv6")
    layers = {
        "udp_ports": probe_udp_ports(),
        # 通用知名 SNI 探测：反映国家级 SNI 过滤，信息性，不单独决定 verdict
        "sni": probe_sni(cf.get("working_ips")),
        # 节点真实 SNI 探测：与策略直接相关
        "sni_node": probe_sni_node(subs, cf.get("working_ips")),
        "ipv6": probe_ipv6(),
        "icmp": {"ok": baseline.get("icmp_ok"), "measured_via": "os-path",
                 "contaminated_by_tun": tun_enabled},
        # 无对端时 WireGuard 对非法握手静默丢弃，端口封锁**不可观测** —— 明确标未测，
        # 而不是用推测填充（诚实降级）。
        "wireguard": {"status": "untested",
                      "reason": "无对端时 WireGuard 对非法握手静默丢弃，不可观测"},
    }

    cf_domains = []
    for sub in subs:
        for p in sub["proxies"]:
            if cfnets.looks_cdn_fronted(p):
                srv = p.get("server")
                if srv and srv not in cf_domains:
                    cf_domains.append(srv)

    cf_ips, cfip_result = [], None
    if do_cfip and channel["raw_channel_ok"]:
        template = cfip_mod.find_cf_template(subs)
        if template:
            log("  [6/7] Cloudflare 优选 IP 实测（模板 %s）" % template.get("server"))
            try:
                scanned = cfip_mod.scan(core_exe, template, workdir)
                cf_ips = [ip for ip, _ in scanned]
                cfip_result = {"tested": len(cfnets.CF_CANDIDATES),
                               "working": len(cf_ips),
                               "results": [{"ip": ip, "delay": d} for ip, d in scanned]}
            except Exception as e:  # noqa: BLE001
                log("        优选 IP 实测失败：%s" % e)
                cfip_result = {"error": str(e)}
        else:
            log("  [6/7] 跳过优选 IP 实测：订阅里没有 Cloudflare 前置节点")
    else:
        log("  [6/7] 跳过优选 IP 实测（通道不可信或已关闭）")

    node_result = None
    if do_reach and subs and channel["raw_channel_ok"]:
        log("  [7/7] 节点可达性实测（%d 个节点）"
            % sum(len(s["proxies"]) for s in subs))
        try:
            node_result = reach_mod.scan(core_exe, subs, cf_domains, cf_ips, workdir)
        except Exception as e:  # noqa: BLE001
            log("        节点实测失败：%s" % e)
            node_result = {"error": str(e), "total": 0, "reachable": 0, "subs": {}}
    else:
        log("  [7/7] 跳过节点可达性实测（通道不可信或已关闭）")

    prof = {
        "schema_version": SCHEMA_VERSION,
        "host": env.get("host") or hostname(),
        "at": iso_now(),
        "elapsed_sec": round(time.time() - t0, 1),
        "channel": channel,
        "client": {"variant": env["client"]["variant"],
                   "version": env["client"]["version"],
                   "tun_enabled": env["client"].get("tun_enabled"),
                   "system_proxy_enabled": env["client"].get("system_proxy_enabled")},
        "core": {"kind": env["core"]["kind"], "version": env["core"]["version"]},
        "baseline": baseline,
        "dns": dns,
        "cf": cf,
        "cf_preferred": cfip_result,
        "cf_fronted_domains": cf_domains,
        "nodes": node_result or {"total": 0, "reachable": 0, "subs": {}},
        "layers": layers,
    }
    prof["verdict"] = decide_verdict(prof)
    return prof


def summarize(prof: dict) -> str:
    L = []
    ch = prof.get("channel") or {}
    L.append("测量通道")
    L.append("  物理网卡       : %s (index=%s)"
             % (ch.get("physical_interface"), ch.get("physical_ifindex")))
    L.append("  TUN 模式       : %s" % ("开启" if ch.get("tun_enabled") else "关闭"))
    L.append("  探测实例出口   : %s"
             % ((ch.get("probe_exit") or {}).get("ip") or "未知"))
    L.append("  本地 OS 出口   : %s"
             % ((ch.get("os_exit") or {}).get("ip") or "未知"))
    L.append("  通道可信       : %s%s"
             % ("是" if ch.get("raw_channel_ok") else "否",
                "  ← " + ch["note"] if not ch.get("raw_channel_ok") else ""))
    L.append("")

    b = prof["baseline"]
    L.append("基线")
    L.append("  国内可达       : %s" % ("是" if b["domestic_ok"] else "否"))
    L.append("  境外可达       : %s" % ("是" if b["overseas_ok"] else "否"))
    L.append("  portal 重定向  : %s%s"
             % ("是" if b["portal_redirect"] else "否",
                " → %s" % b["portal_url"] if b.get("portal_url") else ""))
    L.append("")

    d = prof["dns"]
    L.append("DNS")
    L.append("  UDP53 真实可用 : %s" % (", ".join(d["udp53_ok"]) or "无"))
    L.append("  UDP53 被丢/劫持: %s" % (", ".join(d["udp53_blocked"]) or "无"))
    if d.get("hijack_suspect"):
        L.append("  ⚠ 多个服务器返回相同 fake-ip —— 53 端口被劫持")
    L.append("  DoH 可用       : %d / %d"
             % (len(d["doh_ok"]), len(d["doh_ok"]) + len(d["doh_failed"])))
    L.append("")

    c = prof["cf"]
    L.append("Cloudflare")
    L.append("  anycast 可达   : %d / %d（%.0f%%）"
             % (c["reachable"], c["sampled"], c["ratio"] * 100))
    pref = prof.get("cf_preferred") or {}
    if pref.get("working") is not None:
        L.append("  优选 IP 可用   : %d / %d" % (pref["working"], pref.get("tested", 0)))
    L.append("  CF 前置入口    : %d 个域名" % len(prof.get("cf_fronted_domains") or []))
    L.append("")

    n = prof["nodes"]
    L.append("节点")
    L.append("  可达           : %d / %d" % (n.get("reachable", 0), n.get("total", 0)))
    for name, s in (n.get("subs") or {}).items():
        L.append("    %-14s %d / %d" % (name, s["reachable"], s["total"]))
    L.append("")

    ly = prof["layers"]
    L.append("分层判定")
    L.append("  节点 SNI/TLS   : %s   ← 与策略相关"
             % (ly.get("sni_node") or {}).get("verdict", "unknown"))
    L.append("  通用知名 SNI   : %s   ← 反映国家级过滤，与节点无关"
             % (ly.get("sni") or {}).get("verdict", "unknown"))
    udp = ly["udp_ports"]
    L.append("  UDP 443 (QUIC) : %s" % ("通" if udp["udp443_ok"] else "不通"))
    L.append("  UDP 端口开放数 : %s"
             % ", ".join("%s:%d" % (p, n) for p, n in udp["open_count_by_port"].items()))
    v6 = ly["ipv6"]
    L.append("  IPv6           : %s"
             % ("可用" if v6["reachable"] else
                ("有地址但不通" if v6["global_addresses"] else "无全局地址")))
    L.append("  ICMP           : %s%s"
             % ("通" if (ly.get("icmp") or {}).get("ok") else "不通",
                "（走 OS 路径，TUN 开启时可能失真）"
                if (ly.get("icmp") or {}).get("contaminated_by_tun") else ""))
    L.append("  WireGuard      : %s（%s）"
             % (ly["wireguard"]["status"], ly["wireguard"]["reason"]))
    L.append("")
    L.append("判定: %s" % prof["verdict"])
    return "\n".join(L)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cli_profile(args):
    from .cli import EXIT_ENV, EXIT_OK
    env = envprobe.load_env()
    if not env:
        msg = "机器档案不存在，请先运行 probe。"
        print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False)
              if args.json else msg)
        return EXIT_ENV

    reuse = getattr(args, "reuse", 0.0) or 0.0
    if reuse:
        cached = load_profile(env.get("host"), max_age_sec=reuse * 60)
        if cached:
            if args.json:
                print(json.dumps(cached, indent=2, ensure_ascii=False))
            else:
                print(summarize(cached))
                print("\n（复用 %.0f 分钟内的画像）" % reuse)
            return EXIT_OK

    def log(m):
        print(m, file=sys.stderr, flush=True)

    prof = build(env, log=(lambda m: None) if args.json else log)
    p = save_profile(prof)
    if args.json:
        print(json.dumps(prof, indent=2, ensure_ascii=False))
    else:
        print(summarize(prof))
        print("\n画像已保存 → %s" % p)
        print("（耗时 %.1f 秒）" % prof["elapsed_sec"])
    return EXIT_OK
