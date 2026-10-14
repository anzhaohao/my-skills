# -*- coding: utf-8 -*-
"""物理网卡探测与接口绑定。

**为什么必须有这一层**：当 Clash 的 TUN 模式开启时，操作系统的路由表被
0.0.0.0/1 + 128.0.0.0/1 接管，此时：

  · 本地 socket 的一切测量都会被 TUN 劫持（实测：所有 DNS 返回同一个 fake-ip，
    被丢包的 IP 也「连得上」）—— 画像会完全失真
  · mihomo 自己的出站连接若未绑定物理网卡，同样会被劫持

所以本工具的所有原始网络测量都必须先**绑定物理网卡**。实测验证：
绑定后出口 IP 从代理的新加坡出口变回校园网 CN 出口。

实现全部走 Python 标准库（ctypes），不依赖 psutil，不调用任何 shell。
"""
from __future__ import annotations

import ctypes
import platform
import socket
import sys

IS_WINDOWS = platform.system() == "Windows"

# Windows socket option：指定出站单播包使用的接口（值为接口索引，网络字节序）
IP_UNICAST_IF = 31
IPV6_UNICAST_IF = 31

GAA_FLAG_SKIP_ANYCAST = 0x0002
GAA_FLAG_SKIP_MULTICAST = 0x0004
GAA_FLAG_SKIP_DNS_SERVER = 0x0008
GAA_FLAG_INCLUDE_GATEWAYS = 0x0080

IF_TYPE_SOFTWARE_LOOPBACK = 24
IF_TYPE_TUNNEL = 131
IF_OPER_STATUS_UP = 1

# 明显是虚拟/隧道网卡的友好名关键字（大小写不敏感）
_VIRTUAL_HINTS = ("meta", "clash", "mihomo", "tun", "tap", "wintun", "wireguard",
                  "vmware", "virtualbox", "hyper-v", "vethernet", "loopback",
                  "docker", "vpn", "zerotier", "tailscale", "radmin", "npcap")


# ---------------------------------------------------------------------------
# Windows：GetAdaptersAddresses
# ---------------------------------------------------------------------------
def _win_adapters():
    """返回 [{index, name, description, iftype, up, has_gateway, ipv4:[...]}]。"""
    from ctypes import wintypes

    class SOCKET_ADDRESS(ctypes.Structure):
        _fields_ = [("lpSockaddr", ctypes.c_void_p),
                    ("iSockaddrLength", ctypes.c_int)]

    class IP_ADAPTER_UNICAST_ADDRESS(ctypes.Structure):
        pass

    IP_ADAPTER_UNICAST_ADDRESS._fields_ = [
        ("Length", wintypes.ULONG),
        ("Flags", wintypes.DWORD),
        ("Next", ctypes.POINTER(IP_ADAPTER_UNICAST_ADDRESS)),
        ("Address", SOCKET_ADDRESS),
        ("PrefixOrigin", ctypes.c_int),
        ("SuffixOrigin", ctypes.c_int),
        ("DadState", ctypes.c_int),
        ("ValidLifetime", wintypes.ULONG),
        ("PreferredLifetime", wintypes.ULONG),
        ("LeaseLifetime", wintypes.ULONG),
        ("OnLinkPrefixLength", ctypes.c_ubyte),
    ]

    class IP_ADAPTER_GATEWAY_ADDRESS(ctypes.Structure):
        pass

    IP_ADAPTER_GATEWAY_ADDRESS._fields_ = [
        ("Length", wintypes.ULONG),
        ("Reserved", wintypes.DWORD),
        ("Next", ctypes.POINTER(IP_ADAPTER_GATEWAY_ADDRESS)),
        ("Address", SOCKET_ADDRESS),
    ]

    class IP_ADAPTER_ADDRESSES(ctypes.Structure):
        pass

    IP_ADAPTER_ADDRESSES._fields_ = [
        ("Length", wintypes.ULONG),
        ("IfIndex", wintypes.DWORD),
        ("Next", ctypes.POINTER(IP_ADAPTER_ADDRESSES)),
        ("AdapterName", ctypes.c_char_p),
        ("FirstUnicastAddress", ctypes.POINTER(IP_ADAPTER_UNICAST_ADDRESS)),
        ("FirstAnycastAddress", ctypes.c_void_p),
        ("FirstMulticastAddress", ctypes.c_void_p),
        ("FirstDnsServerAddress", ctypes.c_void_p),
        ("DnsSuffix", ctypes.c_wchar_p),
        ("Description", ctypes.c_wchar_p),
        ("FriendlyName", ctypes.c_wchar_p),
        ("PhysicalAddress", ctypes.c_ubyte * 8),
        ("PhysicalAddressLength", wintypes.ULONG),
        ("Flags", wintypes.ULONG),
        ("Mtu", wintypes.ULONG),
        ("IfType", wintypes.DWORD),
        ("OperStatus", ctypes.c_int),
        ("Ipv6IfIndex", wintypes.DWORD),
        ("ZoneIndices", wintypes.ULONG * 16),
        ("FirstPrefix", ctypes.c_void_p),
        ("TransmitLinkSpeed", ctypes.c_ulonglong),
        ("ReceiveLinkSpeed", ctypes.c_ulonglong),
        ("FirstWinsServerAddress", ctypes.c_void_p),
        ("FirstGatewayAddress", ctypes.POINTER(IP_ADAPTER_GATEWAY_ADDRESS)),
        ("Ipv4Metric", wintypes.ULONG),
        ("Ipv6Metric", wintypes.ULONG),
        ("Luid", ctypes.c_ulonglong),
        ("Dhcpv4Server", SOCKET_ADDRESS),
        ("CompartmentId", wintypes.DWORD),
        ("NetworkGuid", ctypes.c_ubyte * 16),
        ("ConnectionType", ctypes.c_int),
        ("TunnelType", ctypes.c_int),
        ("Dhcpv6Server", SOCKET_ADDRESS),
        ("Dhcpv6ClientDuid", ctypes.c_ubyte * 130),
        ("Dhcpv6ClientDuidLength", wintypes.ULONG),
        ("Dhcpv6ClientIaid", wintypes.ULONG),
        ("FirstDnsSuffix", ctypes.c_void_p),
    ]

    iphlpapi = ctypes.WinDLL("iphlpapi", use_last_error=True)
    size = ctypes.c_ulong(16 * 1024)
    flags = (GAA_FLAG_SKIP_ANYCAST | GAA_FLAG_SKIP_MULTICAST
             | GAA_FLAG_SKIP_DNS_SERVER | GAA_FLAG_INCLUDE_GATEWAYS)
    for _ in range(4):
        buf = ctypes.create_string_buffer(size.value)
        ret = iphlpapi.GetAdaptersAddresses(
            socket.AF_INET, flags, None, buf, ctypes.byref(size))
        if ret == 0:
            break
        if ret != 111:          # ERROR_BUFFER_OVERFLOW
            return []
    else:
        return []

    out = []
    node = ctypes.cast(buf, ctypes.POINTER(IP_ADAPTER_ADDRESSES))
    while node:
        a = node.contents
        ips = []
        ua = a.FirstUnicastAddress
        while ua:
            sa = ua.contents.Address
            if sa.lpSockaddr and sa.iSockaddrLength >= 16:
                raw = ctypes.string_at(sa.lpSockaddr, 16)
                if raw[0] == 2 or raw[1] == 2:      # AF_INET
                    ips.append("%d.%d.%d.%d" % (raw[4], raw[5], raw[6], raw[7]))
            ua = ua.contents.Next
        out.append({
            "index": int(a.IfIndex),
            "name": a.FriendlyName or "",
            "description": a.Description or "",
            "iftype": int(a.IfType),
            "up": int(a.OperStatus) == IF_OPER_STATUS_UP,
            "has_gateway": bool(a.FirstGatewayAddress),
            "ipv4": ips,
        })
        node = a.Next
    return out


def _posix_adapters():
    out = []
    for idx, name in socket.if_nameindex():
        if name.startswith("lo"):
            continue
        ips = []
        try:
            for info in socket.getaddrinfo(name, None, socket.AF_INET):
                ips.append(info[4][0])
        except Exception:
            pass
        out.append({"index": idx, "name": name, "description": name,
                    "iftype": 6, "up": True, "has_gateway": True, "ipv4": ips})
    return out


def list_adapters():
    try:
        return _win_adapters() if IS_WINDOWS else _posix_adapters()
    except Exception:
        return []


def _looks_virtual(adapter) -> bool:
    hay = (adapter.get("name", "") + " " + adapter.get("description", "")).lower()
    return any(h in hay for h in _VIRTUAL_HINTS)


def physical_interface():
    """挑出承载默认路由的物理网卡。

    评分优先级（分数越低越优先）：
      0  有默认网关 + 非隧道类型 + 不是虚拟网卡关键字 + 有 IPv4
      1  有默认网关 + 有 IPv4（允许关键字命中，作为兜底）
      2  其余
    返回 dict 或 None。
    """
    adapters = [a for a in list_adapters()
                if a.get("up") and a.get("ipv4")
                and a.get("iftype") != IF_TYPE_SOFTWARE_LOOPBACK]
    if not adapters:
        return None

    def score(a):
        if a.get("has_gateway") and a.get("iftype") != IF_TYPE_TUNNEL \
                and not _looks_virtual(a):
            return 0
        if a.get("has_gateway"):
            return 1
        return 2

    return sorted(adapters, key=score)[0]


# ---------------------------------------------------------------------------
# socket 绑定
# ---------------------------------------------------------------------------
def bind_socket_to_interface(sock: socket.socket, ifindex: int, family=None) -> bool:
    """把已创建的 socket 绑定到指定接口（Windows: IP_UNICAST_IF）。

    这是绕过 TUN 的关键：绑定后出站包走物理网卡，不经过 TUN 设备。
    """
    if not IS_WINDOWS or not ifindex:
        return False
    fam = family or sock.family
    try:
        if fam == socket.AF_INET6:
            sock.setsockopt(socket.IPPROTO_IPV6, IPV6_UNICAST_IF,
                            socket.htonl(ifindex) if hasattr(socket, "htonl")
                            else ifindex)
        else:
            sock.setsockopt(socket.IPPROTO_IP, IP_UNICAST_IF,
                            socket.htonl(ifindex) if hasattr(socket, "htonl")
                            else ifindex)
        return True
    except Exception:
        return False


def new_socket(family=socket.AF_INET, type=socket.SOCK_STREAM, ifindex=None):
    """创建一个可选绑定到物理接口的 socket。

    注意：socket.htonl 在部分平台不存在，这里用 struct 手工转换，
    保证接口索引以网络字节序传入 IP_UNICAST_IF。
    """
    import struct as _struct
    s = socket.socket(family, type)
    if IS_WINDOWS and ifindex:
        try:
            s.setsockopt(socket.IPPROTO_IP, IP_UNICAST_IF,
                         _struct.pack("!I", ifindex))
        except Exception:
            try:
                s.setsockopt(socket.IPPROTO_IP, IP_UNICAST_IF, ifindex)
            except Exception:
                pass
    return s


# 进程级缓存：一次探测里接口不会变
_CACHE = {}


def default_ifindex():
    """当前默认物理网卡的接口索引（带缓存）。返回 int 或 None。"""
    if "ifindex" not in _CACHE:
        a = physical_interface()
        _CACHE["adapter"] = a
        _CACHE["ifindex"] = a["index"] if a else None
    return _CACHE["ifindex"]


def default_ifname():
    """当前默认物理网卡的友好名（mihomo 的 interface-name 用）。"""
    if "ifname" not in _CACHE:
        a = physical_interface()
        _CACHE["adapter"] = a
        _CACHE["ifname"] = a["name"] if a else None
    return _CACHE["ifname"]


def describe() -> str:
    a = physical_interface()
    if not a:
        return "未找到物理网卡"
    return "%s (index=%d, ipv4=%s, gateway=%s)" % (
        a["name"], a["index"], ",".join(a["ipv4"]), a["has_gateway"])
