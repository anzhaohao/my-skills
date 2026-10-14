# -*- coding: utf-8 -*-
"""端到端验证。

网络修复的验收对象是**运行时行为**，不是代码 diff（见计划）。
因此这里经用户 Clash 的实际代理端口发起真实请求。

判定标准（来自计划的验收条件）：
  · google.com/generate_204 → HTTP 204
  · youtube.com → HTTP 200 且响应体 > 100KB
  · 能读出出口 IP 与国家
"""
from __future__ import annotations

import json
import os

from . import clashverge as cv
from . import envprobe
from .util import http_get_body

CHECKS = [
    {"name": "google204", "url": "https://www.google.com/generate_204",
     "expect_status": [204, 200], "min_bytes": 0, "desc": "Google 204 探针"},
    {"name": "youtube", "url": "https://www.youtube.com",
     "expect_status": [200], "min_bytes": 100 * 1024, "desc": "YouTube 首页"},
    {"name": "trace", "url": "https://www.cloudflare.com/cdn-cgi/trace",
     "expect_status": [200], "min_bytes": 20, "desc": "出口信息"},
]


def mixed_port(env: dict):
    """读用户 Clash 的混合端口（从 verge.yaml，不猜）。"""
    data_dir = env["client"]["data_dir"]
    verge = cv.read_verge_yaml(data_dir)
    p = verge.get("verge_mixed_port")
    if p:
        return int(p)
    core_cfg = None
    try:
        core_cfg = cv.yamlcompat.load_file(
            __import__("os").path.join(data_dir, "config.yaml"))
    except Exception:
        core_cfg = None
    if isinstance(core_cfg, dict) and core_cfg.get("mixed-port"):
        return int(core_cfg["mixed-port"])
    return None


def run(env: dict, timeout: float = 30.0):
    port = mixed_port(env)
    if not port:
        return {"ok": False, "error": "无法确定 Clash Verge 的混合代理端口", "checks": []}

    proxy = "http://127.0.0.1:%d" % port
    results = []
    for spec in CHECKS:
        status, headers, body, _u = http_get_body(
            spec["url"], proxy=proxy, timeout=timeout)
        ok = (status in spec["expect_status"]) and (len(body) >= spec["min_bytes"])
        item = {"name": spec["name"], "desc": spec["desc"], "url": spec["url"],
                "status": status, "bytes": len(body), "ok": bool(ok)}
        if spec["name"] == "trace" and body:
            for line in body.decode("utf-8", "replace").splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    if k in ("ip", "loc", "colo"):
                        item[k] = v
        results.append(item)

    passed = sum(1 for r in results if r["ok"])
    return {
        "ok": passed == len(results),
        "passed": passed,
        "total": len(results),
        "proxy": proxy,
        "checks": results,
    }


def simulate(env: dict, profile: dict, timeout: float = 25.0):
    """**自主验证**：不依赖用户去 GUI 刷新，直接验证生成的脚本是否真的产出可用配置。

    做法：把当前订阅配置按与扩展脚本**完全相同的语义**处理一遍
    （换入口 IP + 剔除实测死节点），交给一个临时 mihomo 实例，经它真实请求外网。

    这解决了两个问题：
      1. 用户还没点「刷新」时也能确认修复有效（apply 之后即可验证）
      2. 把「配置是否可用」与「GUI 是否已重载」两件事分开，避免误判
    """
    from . import clashverge as cv
    from . import reach as reach_mod
    from .util import ProbeCore

    uid = cv.current_profile_uid(env["client"]["data_dir"])
    sub = next((s for s in env["subscriptions"] if s["uid"] == uid), None)
    if sub is None:
        sub = next((s for s in env["subscriptions"] if s.get("exists")), None)
    if sub is None:
        return {"ok": False, "error": "找不到当前订阅"}

    loaded = cv.read_subscription(sub["path"])
    if not loaded:
        return {"ok": False, "error": "无法解析订阅：%s" % sub["path"]}

    cf_ips = [r["ip"] for r in ((profile.get("cf_preferred") or {}).get("results") or [])]
    domains = profile.get("cf_fronted_domains") or []
    dead = set((((profile.get("nodes") or {}).get("subs") or {})
                .get(sub["name"], {}) or {}).get("dead") or [])

    proxies, _n = reach_mod.apply_cf_fix(loaded["proxies"], domains, cf_ips)

    # 用「活着的 CF 前置节点」建一个选择组（优先延迟最低的优选 IP 那个）
    alive = [p["name"] for p in proxies
             if p.get("name") and p["name"] not in dead
             and p.get("type") in ("vless", "vmess", "trojan")]
    if not alive:
        return {"ok": False, "error": "修复后没有可用的出口节点"}

    cfg = {
        "allow-lan": False, "mode": "rule", "log-level": "warning", "ipv6": False,
        "unified-delay": True,
        "proxies": proxies,
        "proxy-groups": [{"name": "SIM", "type": "select",
                          "proxies": alive + ["DIRECT"]}],
        "rules": ["MATCH,SIM"],
    }

    workdir = os.path.join(envprobe.DATA_DIR, "probe-work", "simulate")
    try:
        with ProbeCore(env["core"]["exe"], workdir, cfg) as core:
            core.select("SIM", alive[0])
            checks = []
            for spec in CHECKS:
                status, _h, body, _u = http_get_body(
                    spec["url"], proxy=core.proxy_url, timeout=timeout)
                ok = (status in spec["expect_status"]) and (len(body) >= spec["min_bytes"])
                item = {"name": spec["name"], "desc": spec["desc"], "url": spec["url"],
                        "status": status, "bytes": len(body), "ok": bool(ok)}
                if spec["name"] == "trace" and body:
                    for line in body.decode("utf-8", "replace").splitlines():
                        if "=" in line:
                            k, _, v = line.partition("=")
                            if k in ("ip", "loc", "colo"):
                                item[k] = v
                checks.append(item)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": "模拟实例启动或请求失败：%s" % e}

    passed = sum(1 for c in checks if c["ok"])
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "mode": "simulate",
        "subscription": sub["name"],
        "exit_node": alive[0],
        "cf_ips_used": len(cf_ips),
        "dead_removed": len(dead),
        "checks": checks,
    }


def summarize(res: dict) -> str:
    if res.get("error"):
        return "验证失败：%s" % res["error"]
    mode = res.get("mode")
    if mode == "simulate":
        L = ["端到端验证（模拟模式：不经用户 Clash，直接跑修复后的配置）"]
        L.append("  订阅          : %s" % res.get("subscription"))
        L.append("  出口节点      : %s" % res.get("exit_node"))
        L.append("  使用优选 IP   : %d 个" % res.get("cf_ips_used", 0))
        L.append("  测试组排除死节点: %d 个（仅为让模拟出口可用，正式配置里是否剔除由 --filter-dead 决定）"
                 % res.get("dead_removed", 0))
    else:
        L = ["端到端验证（经 %s）" % res["proxy"]]
    for c in res["checks"]:
        mark = "✓" if c["ok"] else "✗"
        detail = "HTTP %s, %d 字节" % (c["status"], c["bytes"])
        if c.get("loc"):
            detail += "  出口 %s (%s/%s)" % (c.get("ip"), c.get("loc"), c.get("colo"))
        L.append("  %s %-28s %s" % (mark, c["desc"], detail))
    L.append("")
    L.append("结果: %d / %d 通过" % (res["passed"], res["total"]))
    return "\n".join(L)


def cli_verify(args):
    from . import profiling
    from .cli import EXIT_ENV, EXIT_OK, EXIT_UNSUPPORTED

    env = envprobe.load_env()
    if not env:
        print("机器档案不存在，请先运行 probe。")
        return EXIT_ENV

    if getattr(args, "simulate", False):
        prof = profiling.load_profile(env.get("host"))
        if not prof:
            print("网络画像不存在，请先运行 profile。")
            return EXIT_ENV
        res = simulate(env, prof)
    else:
        res = run(env)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(summarize(res))
    return EXIT_OK if res["ok"] else EXIT_UNSUPPORTED
