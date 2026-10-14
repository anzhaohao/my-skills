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


def summarize(res: dict) -> str:
    if res.get("error"):
        return "验证失败：%s" % res["error"]
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
    from .cli import EXIT_ENV, EXIT_OK, EXIT_UNSUPPORTED

    env = envprobe.load_env()
    if not env:
        print("机器档案不存在，请先运行 probe。")
        return EXIT_ENV

    res = run(env)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(summarize(res))
    return EXIT_OK if res["ok"] else EXIT_UNSUPPORTED
