# -*- coding: utf-8 -*-
"""节点可达性实测。

关键设计（见计划）：**只把实测确认连不通的节点判为死节点**，
绝不按「非 Cloudflare 前置即死」来推断 —— 否则会误杀能用的非 CF 节点
（今日实测：一元机场 24 个节点里有 5 个是活的，旧逻辑会全部误杀）。

测试对象是「换过入口 IP 之后」的节点，这样结论反映修复后的真实可用性。
"""
from __future__ import annotations

import copy
import os

from . import cfnets
from .util import ProbeCore

TEST_URL = "http://www.gstatic.com/generate_204"

# 机场常见的「剩余流量 / 套餐到期」之类信息节点，不参与实测
def _is_pseudo(proxy: dict) -> bool:
    srv = str(proxy.get("server") or "")
    return (not srv) or srv in ("127.0.0.1", "localhost", "0.0.0.0")


def apply_cf_fix(proxies, cf_domains, cf_ips):
    """按与扩展脚本一致的规则预演入口 IP 替换，返回 (新列表, 改写数)。

    仅替换入口 IP；SNI / ws-opts / reality-opts / 名称一律不动。
    """
    out = []
    idx = 0
    fixed = 0
    for p in proxies:
        q = dict(p)
        srv = str(q.get("server") or "")
        is_cf = (q.get("type") in cfnets.TLS_TYPES
                 and (srv in cf_domains or cfnets.looks_cdn_fronted(q)))
        if is_cf and cf_ips:
            q["server"] = cf_ips[idx % len(cf_ips)]
            idx += 1
            fixed += 1
        out.append(q)
    return out, fixed


def scan(core_exe: str, subscriptions, cf_domains, cf_ips, workdir: str,
         timeout_ms: int = 5000, workers: int = 12):
    """实测所有订阅的节点。

    参数 subscriptions: [{"name": str, "proxies": [...]}]
    返回 {"subs": {name: {...}}, "total": n, "reachable": k}
    """
    proxies, mapping = [], []
    seq = 0
    for sub in subscriptions:
        fixed_proxies, _ = apply_cf_fix(sub.get("proxies") or [], cf_domains, cf_ips)
        for p in fixed_proxies:
            if _is_pseudo(p):
                continue
            q = copy.deepcopy(p)
            alias = "n%04d" % seq
            q["name"] = alias
            q.pop("dialer-proxy", None)
            proxies.append(q)
            mapping.append((alias, sub["name"], p.get("name") or alias))
            seq += 1

    if not proxies:
        return {"subs": {}, "total": 0, "reachable": 0}

    cfg = {
        "allow-lan": False, "mode": "rule", "log-level": "warning",
        "ipv6": False, "unified-delay": True,
        "proxies": proxies,
        "proxy-groups": [{"name": "SCAN", "type": "select",
                          "proxies": [a for a, _, _ in mapping] + ["DIRECT"]}],
        "rules": ["MATCH,SCAN"],
    }
    os.makedirs(workdir, exist_ok=True)

    with ProbeCore(core_exe, workdir, cfg) as core:
        if core.delay("DIRECT", url="http://www.baidu.com", timeout_ms=5000) is None:
            raise RuntimeError("探测实例未能连通国内基线，节点实测结果不可信")
        res = core.delay_many([a for a, _, _ in mapping], url=TEST_URL,
                              timeout_ms=timeout_ms, workers=workers)

    subs = {}
    for alias, sub_name, node_name in mapping:
        d = res.get(alias)
        s = subs.setdefault(sub_name, {"total": 0, "reachable": 0,
                                       "alive": [], "dead": [], "delays": {}})
        s["total"] += 1
        if d:
            s["reachable"] += 1
            s["alive"].append(node_name)
            s["delays"][node_name] = d
        else:
            s["dead"].append(node_name)

    total = sum(s["total"] for s in subs.values())
    reachable = sum(s["reachable"] for s in subs.values())
    return {"subs": subs, "total": total, "reachable": reachable}
