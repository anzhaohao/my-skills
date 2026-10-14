# -*- coding: utf-8 -*-
"""Cloudflare 优选 IP 实测。

**候选池是全球通用的（CF_CANDIDATES）**；可达集合由本机本网络实测得出，
绝不硬编码 —— 这是本技能能换校园网运行的关键之一。
"""
from __future__ import annotations

import copy
import os

from . import cfnets
from .util import ProbeCore, free_port


def find_cf_template(subscriptions):
    """从订阅里挑一个「Cloudflare 前置」节点作为实测模板。"""
    for sub in subscriptions:
        for p in sub.get("proxies") or []:
            if p.get("type") in cfnets.TLS_TYPES and cfnets.looks_cdn_fronted(p):
                return p
        for p in sub.get("proxies") or []:
            ips = p.get("_cf_ips")
            if ips:
                return p
    return None


def scan(core_exe: str, template: dict, workdir: str,
         candidates=None, timeout_ms: int = 6000, workers: int = 8):
    """实测候选 IP，返回 [(ip, delay_ms)]，按延迟升序。

    用真实节点做延迟测试，而不是裸 TCP 连通 —— 今日实测证明两者不等价
    （TCP 通但节点不可用的情况存在）。
    """
    candidates = candidates or cfnets.CF_CANDIDATES
    proxies, pairs = [], []
    for i, ip in enumerate(candidates):
        q = copy.deepcopy(template)
        q["name"] = "cfip%03d" % i
        q["server"] = ip
        q.pop("dialer-proxy", None)
        q.pop("_cf_ips", None)
        proxies.append(q)
        pairs.append((q["name"], ip))

    cfg = {
        "allow-lan": False, "mode": "rule", "log-level": "warning",
        "ipv6": False, "unified-delay": True,
        "proxies": proxies,
        "proxy-groups": [{"name": "SCAN", "type": "select",
                          "proxies": [n for n, _ in pairs] + ["DIRECT"]}],
        "rules": ["MATCH,SCAN"],
    }
    os.makedirs(workdir, exist_ok=True)
    with ProbeCore(core_exe, workdir, cfg) as core:
        if core.delay("DIRECT", url="http://www.baidu.com", timeout_ms=5000) is None:
            return []
        res = core.delay_many([n for n, _ in pairs], timeout_ms=timeout_ms,
                              workers=workers)
    good = [(ip, res.get(name)) for name, ip in pairs if res.get(name)]
    good.sort(key=lambda x: x[1])
    return good
