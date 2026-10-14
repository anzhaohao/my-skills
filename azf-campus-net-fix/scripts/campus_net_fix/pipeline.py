# -*- coding: utf-8 -*-
"""L0 日常入口：profile → apply → verify。

退出码语义（技能据此分支）：
    0  成功（验证通过）
    3  环境缺失或漂移，需要先 probe
    4  画像不支持当前网络，或验证未通过 —— 需要人工 / AI 诊断
    5  依赖缺失
"""
from __future__ import annotations

import json

from . import envprobe, override, profiling, strategy, verify
from .cli import EXIT_DEPENDENCY, EXIT_ENV, EXIT_OK, EXIT_UNSUPPORTED


def _log(args, msg):
    if not args.json:
        print(msg)


def cli_run(args):
    # 1) 环境
    env = envprobe.load_env()
    if not env:
        if args.json:
            print(json.dumps({"ok": False, "stage": "env",
                              "error": "机器档案不存在"}, ensure_ascii=False))
        else:
            print("机器档案不存在，请先运行：probe")
        return EXIT_ENV

    ok, issues, env = envprobe.doctor(env)
    if not ok:
        if args.json:
            print(json.dumps({"ok": False, "stage": "doctor", "issues": issues},
                             ensure_ascii=False))
        else:
            print("环境漂移，需要重新探测：")
            for i in issues:
                print("  - %s" % i)
            print("→ 请运行：probe")
        return EXIT_ENV

    # 2) 画像
    _log(args, "[1/3] 网络画像")
    def plog(m):
        _log(args, m)

    prof = profiling.build(env, log=plog)
    profiling.save_profile(prof)
    decision = strategy.choose(prof)

    if args.json:
        result = {"profile": prof, "decision": decision}

    # 3) 实施
    _log(args, "")
    _log(args, "[2/3] 策略：%s —— %s" % (decision["action"], decision["title"]))

    apply_result = {"skipped": True, "reason": "策略无需实施"}
    applied = False
    if decision["implementable"]:
        ok_apply, apply_result = override.apply(
            env, prof, decision, dry_run=getattr(args, "dry_run", False))
        applied = ok_apply and not apply_result.get("dry_run")
        _log(args, override.summarize_result(ok_apply, apply_result))
        if not ok_apply:
            if args.json:
                result["apply"] = apply_result
                result["ok"] = False
                print(json.dumps(result, indent=2, ensure_ascii=False))
            return EXIT_UNSUPPORTED
    else:
        _log(args, "  未实施：%s" % decision["why"])
        for a in decision.get("advice") or []:
            _log(args, "    - %s" % a)
        for b in decision.get("blockers") or []:
            _log(args, "  阻碍：%s" % b)

    # 4) 验证
    _log(args, "")
    _log(args, "[3/3] 端到端验证")
    vres = verify.run(env)
    _log(args, verify.summarize(vres))

    if args.json:
        result["apply"] = apply_result
        result["verify"] = vres
        result["ok"] = bool(vres.get("ok"))
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if vres.get("ok"):
        return EXIT_OK

    # 实施过但验证不通过 → 交 L1
    if not args.json:
        print()
        if applied:
            print("已实施但验证未通过。请把画像 JSON 交给 AI 诊断（L1）：")
            print("  %s" % profiling.profile_path(env.get("host")))
        elif not decision["implementable"]:
            print("当前网络形态超出本技能策略范围。请把画像 JSON 交给 AI 诊断（L1）：")
            print("  %s" % profiling.profile_path(env.get("host")))
    return EXIT_UNSUPPORTED
