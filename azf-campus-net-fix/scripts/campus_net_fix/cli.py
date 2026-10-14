# -*- coding: utf-8 -*-
"""CLI 契约。

退出码（技能据此分支，是 AI 与确定性内核之间的接口）：
    0  成功
    3  环境缺失 / 漂移 → 需要重新 probe（必要时由 AI 补缺口）
    4  画像不支持当前网络 → 需要人工或 AI 诊断
    5  依赖缺失（Python / PyYAML / 内核）
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import envprobe
from .util import hostname

EXIT_OK = 0
EXIT_ENV = 3
EXIT_UNSUPPORTED = 4
EXIT_DEPENDENCY = 5


def _print(obj, as_json: bool):
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    return obj


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------
def cmd_doctor(args):
    env = envprobe.load_env()
    ok, issues, env = envprobe.doctor(env)
    out = {"ok": ok, "issues": issues, "host": hostname(),
           "env_path": envprobe.env_path()}
    if env:
        c = env.get("client") or {}
        out["client"] = {"variant": c.get("variant"), "version": c.get("version"),
                         "install_dir": c.get("install_dir"),
                         "data_dir": c.get("data_dir"),
                         "supports_global_script": c.get("supports_global_script")}
        out["core"] = env.get("core")
        out["runtime"] = env.get("runtime")
        out["subscriptions"] = [{"name": s["name"], "nodes": s.get("nodes")}
                                for s in (env.get("subscriptions") or [])]

    if args.json:
        _print(out, True)
    else:
        if not env:
            print("机器档案不存在：%s" % out["env_path"])
            print("→ 需要先运行：probe")
        else:
            print("机器: %s" % out["host"])
            print("客户端: %s %s" % (out["client"]["variant"], out["client"]["version"]))
            print("  安装目录: %s" % out["client"]["install_dir"])
            print("  数据目录: %s" % out["client"]["data_dir"])
            print("  全局扩展脚本: %s"
                  % ("支持" if out["client"]["supports_global_script"] else "不支持"))
            print("内核: %s %s" % (out["core"].get("kind"), out["core"].get("version")))
            print("运行时: Python %s / PyYAML %s (%s)"
                  % (out["runtime"]["python_version"], out["runtime"]["yaml_version"],
                     out["runtime"]["yaml_source"]))
            print("订阅: %s" % ", ".join("%s(%d)" % (s["name"], s.get("nodes") or 0)
                                        for s in out["subscriptions"]))
            print()
            if ok:
                print("状态: 就绪")
            else:
                print("状态: 发现 %d 个问题" % len(issues))
                for i in issues:
                    print("  - %s" % i)
                print("→ 需要运行：probe")
    return EXIT_OK if ok else EXIT_ENV


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------
def cmd_probe(args):
    try:
        env = envprobe.probe(install_dir=args.install_dir, data_dir=args.data_dir)
    except FileNotFoundError as e:
        if args.json:
            _print({"ok": False, "stage": "locate", "error": str(e)}, True)
        else:
            print("环境探测失败：%s" % e)
        return EXIT_DEPENDENCY
    except Exception as e:  # noqa: BLE001
        if args.json:
            _print({"ok": False, "stage": "probe", "error": str(e)}, True)
        else:
            print("环境探测失败：%s" % e)
        return EXIT_DEPENDENCY

    p = envprobe.save_env(env)
    if args.json:
        _print({"ok": True, "env_path": p, "env": env}, True)
    else:
        c = env["client"]
        print("环境探测完成 → %s" % p)
        print("  客户端   : %s %s（%s）" % (c["variant"], c["version"], c["version_source"]))
        print("  安装目录 : %s（来源 %s）" % (c["install_dir"], c["install_dir_method"]))
        print("  数据目录 : %s" % c["data_dir"])
        print("  内核     : %s %s（%s）" % (env["core"]["kind"], env["core"]["version"],
                                            env["core"]["source"]))
        print("  扩展脚本 : %s（%s）"
              % ("支持全局" if c["supports_global_script"] else "不支持全局",
                 c["capability_basis"]))
        print("  订阅     : %d 个，共 %d 个节点"
              % (len(env["subscriptions"]), sum(s["nodes"] for s in env["subscriptions"])))
        print("  运行时   : Python %s / PyYAML %s（%s）"
              % (env["runtime"]["python_version"], env["runtime"]["yaml_version"],
                 env["runtime"]["yaml_source"]))
    return EXIT_OK


# ---------------------------------------------------------------------------
# env（供 AI 与其他 agent 读取已探明事实）
# ---------------------------------------------------------------------------
def cmd_env(args):
    env = envprobe.load_env()
    if not env:
        if args.json:
            _print({"ok": False, "error": "no env"}, True)
        else:
            print("机器档案不存在，先运行 probe。")
        return EXIT_ENV
    if args.key:
        node = env
        for part in args.key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                print("未找到键：%s" % args.key, file=sys.stderr)
                return EXIT_ENV
        if args.json or isinstance(node, (dict, list)):
            _print(node, True)
        else:
            print(node)
        return EXIT_OK
    _print(env, True)
    return EXIT_OK


# ---------------------------------------------------------------------------
# dump：把当前订阅导出为 JSON，供外部工具/测试消费
# ---------------------------------------------------------------------------
def cmd_dump(args):
    from . import clashverge as cv
    env = envprobe.load_env()
    if not env:
        print("机器档案不存在，请先运行 probe。")
        return EXIT_ENV

    prof = None
    try:
        from . import profiling
        prof = profiling.load_profile(env.get("host"))
    except Exception:
        prof = None
    dead_by_sub = ((prof or {}).get("nodes") or {}).get("subs") or {}

    out = []
    for s in env["subscriptions"]:
        loaded = cv.read_subscription(s["path"])
        if not loaded:
            continue
        out.append({
            "uid": s["uid"], "name": s["name"], "path": s["path"],
            "config": {"proxies": loaded["proxies"],
                       "proxy-groups": loaded["proxy-groups"]},
            "dead": (dead_by_sub.get(s["name"]) or {}).get("dead") or [],
        })

    path = args.out
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    if args.json:
        print(json.dumps({"ok": True, "out": path, "subscriptions": len(out)},
                         ensure_ascii=False))
    else:
        print("已导出 %d 个订阅 → %s" % (len(out), path))
    return EXIT_OK


# ---------------------------------------------------------------------------
# 其余子命令在后续模块里实现，这里做惰性分发
# ---------------------------------------------------------------------------
def cmd_profile(args):
    from . import profiling
    return profiling.cli_profile(args)


def cmd_apply(args):
    from . import override
    return override.cli_apply(args)


def cmd_verify(args):
    from . import verify
    return verify.cli_verify(args)


def cmd_run(args):
    from . import pipeline
    return pipeline.cli_run(args)


def build_parser():
    p = argparse.ArgumentParser(
        prog="campus-net-fix",
        description="校园网 Clash Verge 代理连通性诊断与适配")
    p.add_argument("--json", action="store_true", help="以 JSON 输出（供 AI/脚本消费）")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="环境体检 + 漂移检测")
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_doctor)

    pr = sub.add_parser("probe", help="探测本机环境并写出机器档案")
    pr.add_argument("--install-dir", default=None, help="显式指定 Clash Verge 安装目录")
    pr.add_argument("--data-dir", default=None, help="显式指定 Clash Verge 数据目录")
    pr.add_argument("--json", action="store_true")
    pr.set_defaults(func=cmd_probe)

    e = sub.add_parser("env", help="打印已探测的本机事实")
    e.add_argument("key", nargs="?", default=None, help="点号路径，如 client.install_dir")
    e.add_argument("--json", action="store_true")
    e.set_defaults(func=cmd_env)

    pf = sub.add_parser("profile", help="网络画像：判定封锁发生在哪一层")
    pf.add_argument("--json", action="store_true")
    pf.add_argument("--reuse", type=float, default=0.0,
                    help="复用 N 分钟内的画像（0 = 不重用）")
    pf.set_defaults(func=cmd_profile)

    ap = sub.add_parser("apply", help="按画像选策略并实施")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="只生成，不写入 Clash Verge")
    ap.set_defaults(func=cmd_apply)

    vf = sub.add_parser("verify", help="端到端验证（经真实代理请求）")
    vf.add_argument("--json", action="store_true")
    vf.set_defaults(func=cmd_verify)

    rn = sub.add_parser("run", help="profile → apply → verify（日常入口）")
    rn.add_argument("--json", action="store_true")
    rn.add_argument("--dry-run", action="store_true")
    rn.set_defaults(func=cmd_run)

    du = sub.add_parser("dump", help="把当前订阅导出为 JSON（供外部工具/测试消费）")
    du.add_argument("--out", default=os.path.join(envprobe.DATA_DIR, "subscriptions.json"))
    du.add_argument("--json", action="store_true")
    du.set_defaults(func=cmd_dump)

    return p


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n已中断。", file=sys.stderr)
        return 130
    except ModuleNotFoundError as e:
        print("依赖缺失：%s" % e, file=sys.stderr)
        return EXIT_DEPENDENCY
