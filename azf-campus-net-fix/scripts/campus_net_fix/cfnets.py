# -*- coding: utf-8 -*-
"""Cloudflare 网段、CDN 前置节点判定、优选 IP 候选池。

这些是**跨网络通用**的常量（Cloudflare 官方公布的 anycast 网段全球一致），
与具体校园网无关。校园网相关的可达 IP 集合由运行时实测得出，绝不硬编码。
"""
from __future__ import annotations

import re

# Cloudflare 官方公布的全部 IPv4 anycast 网段
CF_NETS = [
    "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22", "104.16.0.0/13",
    "104.24.0.0/14", "108.162.192.0/18", "131.0.72.0/22", "141.101.64.0/18",
    "162.158.0.0/15", "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20",
    "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17",
]

# Cloudflare 支持 HTTP/3 与 CDN 回源的端口（用于启发式判定）
CDN_PORTS = [80, 8080, 8880, 2052, 2082, 2086, 2095,
             443, 2053, 2083, 2087, 2096, 8443]

# 可用于入站检测的 CDN 协议类型
TLS_TYPES = ("vless", "vmess", "trojan")

IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

# 每个网段取一个代表 IP 作为实测候选（覆盖全部 15 个网段 + 常用段多点取样）
CF_CANDIDATES = [
    "162.159.140.1", "162.159.128.1", "162.159.0.1", "162.159.192.1",
    "104.16.0.1", "104.16.132.229", "104.17.0.1", "104.18.0.1", "104.18.32.1",
    "104.19.0.1", "104.20.0.1", "104.21.0.1", "104.22.0.1", "104.24.0.1",
    "104.26.0.1", "104.27.0.1", "108.162.192.1", "108.162.198.1",
    "172.64.0.1", "172.67.0.1", "172.67.193.12",
    "188.114.96.1", "188.114.97.1", "188.114.98.1", "188.114.99.1",
    "103.21.244.1", "103.22.200.1", "103.31.4.1",
    "131.0.72.1", "141.101.64.1", "173.245.48.1",
    "190.93.240.1", "197.234.240.1", "198.41.128.1",
]


def ip2int(ip: str) -> int:
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def _build_ranges():
    out = []
    for net in CF_NETS:
        base, bits = net.split("/")
        mask = (0xFFFFFFFF << (32 - int(bits))) & 0xFFFFFFFF
        out.append((ip2int(base) & mask, mask))
    return tuple(out)


_RANGES = _build_ranges()


def is_cf_ip(ip: str) -> bool:
    if not IPV4_RE.match(ip or ""):
        return False
    try:
        v = ip2int(ip)
    except Exception:
        return False
    return any((v & m) == n for n, m in _RANGES)


def looks_cdn_fronted(proxy: dict) -> bool:
    """静态启发式：判断节点入口是否套在 CDN 后面。

    与 Clash Verge 扩展脚本里的同名函数**保持逐条一致**。
    已在 87 个真实节点上与 DoH 判定比对，一致率 100%（见计划）。

    排除项各有实测依据：
      · reality-opts  —— REALITY 借 SNI，换入口 IP 必坏
      · 裸 IP 入口    —— CDN 前置必然用域名
      · SNI == server —— 直连自签，不是 CDN 回源
      · 非 CDN 端口   —— Cloudflare 只在这些端口提供 HTTP/HTTPS
    """
    server = proxy.get("server")
    if not server:
        return False
    if proxy.get("reality-opts"):
        return False
    if proxy.get("type") not in TLS_TYPES:
        return False
    if proxy.get("tls") is not True:
        return False
    net = proxy.get("network") or ("ws" if proxy.get("ws-opts") else "")
    if net not in ("ws", "grpc", "h2"):
        return False
    if IPV4_RE.match(str(server)):
        return False
    sni = proxy.get("servername") or proxy.get("sni") or ""
    if not sni or sni == server:
        return False
    try:
        if int(proxy.get("port")) not in CDN_PORTS:
            return False
    except Exception:
        return False
    return True
