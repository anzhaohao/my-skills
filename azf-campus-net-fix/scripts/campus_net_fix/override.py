# -*- coding: utf-8 -*-
"""实施：生成并写入 Clash Verge 全局扩展脚本。

沿用今日已在真实订阅上验证过的逻辑：
  · 只换入口 IP，SNI / ws-opts / reality-opts / 节点名一律不动
  · 只剔除**实测确认连不通**的节点，绝不按「非 CF 即死」误杀
  · 订阅名匹配不上时不做任何剔除（安全默认）
  · 脚本全程 try/catch，异常时原样返回配置，不会让订阅加载失败
  · 写前自动备份 Script.js.bak

支持的客户端能力：仅当 env 探测到 supports_global_script 时才走全局脚本路径。
"""
from __future__ import annotations

import json
import os
import shutil
import time

from . import envprobe
from . import strategy

SCRIPT_TEMPLATE = r"""// ============================================================================
//  Clash Verge 全局扩展脚本 —— 校园网环境自动修复
//  【由 azf-campus-net-fix 自动生成，请勿手动编辑】
//
//  生成时间 : %(stamp)s
//  机器     : %(host)s
//  网络判定 : %(verdict)s (%(verdict_title)s)
//  覆盖订阅 : %(subs)s
// ============================================================================
//
//  核心动作（已验证）：把 Cloudflare 前置节点的入口 IP 换成**本网络实测可达**
//  的优选 IP。判定顺序：先查精确名单（由 DoH 解析得出），未命中再用静态启发式
//  规则兜底，这样以后新增的订阅也能立刻生效。
//
//  可选动作：把实测确认连不通的节点从代理组里剔除（ENABLE_DEAD_FILTER）。
//  ⚠ 该功能默认**关闭**。2026-10-14 出现过一次事故：线上运行时所有代理组被清空、
//    流量全部走直连，而同样的输入在独立 JS 引擎里无法复现，根因未定位。
//    在查清之前保持关闭 —— url-test 组本来就会自动跳过不可用节点，
//    这个功能的收益不足以承担它的事故半径。
//
//  注意：CF_IPS 是**本网络实测结果**，换校园网后必须重新运行 apply 生成。
// ============================================================================

function main(config, profileName) {
  try {
    if (!config || !config.proxies || !config.proxies.length) return config;

    // ---- 开关：剔除实测连不通的节点（默认关闭，见文件头说明）-------------
    var ENABLE_DEAD_FILTER = %(enable_filter)s;

    // ---- 本网络实测可达的 Cloudflare anycast IP（按延迟排序，轮询使用）----
    var CF_IPS = %(ips)s;

    // ---- DoH 精确判定出的 Cloudflare 前置入口域名 --------------------------
    var CF_FRONTED = %(domains)s;

    // ---- 各订阅里实测连不通的节点（只剔除这些）----------------------------
    var DEAD = %(dead)s;

    var TLS_TYPES = ['vless', 'vmess', 'trojan'];
    var CDN_PORTS = [80, 8080, 8880, 2052, 2082, 2086, 2095,
                     443, 2053, 2083, 2087, 2096, 8443];
    var BUILTIN = ['DIRECT', 'REJECT', 'REJECT-DROP', 'PASS', 'COMPATIBLE', 'GLOBAL'];
    var IPV4 = /^\d{1,3}(\.\d{1,3}){3}$/;

    // 静态启发式：给尚未进入精确名单的新订阅兜底。
    // REALITY / 裸 IP / SNI 与入口相同 / 非 CDN 端口 一律排除
    // （reality-opts 借 SNI，换入口 IP 必坏）
    function looksCdnFronted(p) {
      if (!p.server) return false;
      if (p['reality-opts']) return false;
      if (TLS_TYPES.indexOf(p.type) === -1) return false;
      if (p.tls !== true) return false;
      var net = p.network || (p['ws-opts'] ? 'ws' : '');
      if (net !== 'ws' && net !== 'grpc' && net !== 'h2') return false;
      if (IPV4.test(p.server)) return false;
      var sni = p.servername || p.sni || '';
      if (!sni || sni === p.server) return false;
      if (CDN_PORTS.indexOf(Number(p.port)) === -1) return false;
      return true;
    }

    var i, j, p, g, n;
    var groups = config['proxy-groups'] || [];
    var groupNames = {};
    for (i = 0; i < groups.length; i++) {
      if (groups[i] && groups[i].name) groupNames[groups[i].name] = true;
    }

    // ---- 1. 修复入口 IP -----------------------------------------------------
    var fixedCount = 0;
    for (i = 0; i < config.proxies.length; i++) {
      p = config.proxies[i];
      if (!p || !p.name || !p.server) continue;
      if (TLS_TYPES.indexOf(p.type) === -1) continue;
      if (CF_FRONTED.indexOf(p.server) === -1 && !looksCdnFronted(p)) continue;

      p.server = CF_IPS[fixedCount %% CF_IPS.length];   // 只换入口 IP
      fixedCount++;
    }

    // ---- 2. 剔除实测连不通的节点（默认关闭）--------------------------------
    // 启用时的安全设计：
    //   · 订阅名匹配不上时不做任何剔除
    //   · 某个组被剔空时**保持原样**，绝不回退成 ['DIRECT']
    //     （2026-10-14 事故：回退成 DIRECT 会让全部流量走直连）
    //   · 全局兜底：若所有组加起来一个节点都没保住，判定 DEAD 名单异常，整体放弃
    var deadList = ENABLE_DEAD_FILTER ? DEAD[profileName] : null;
    var dropped = 0;
    var keptTotal = 0;
    if (deadList && deadList.length) {
      var deadSet = {};
      for (i = 0; i < deadList.length; i++) deadSet[deadList[i]] = true;

      var planned = [];
      for (i = 0; i < groups.length; i++) {
        g = groups[i];
        if (!g || !g.proxies || !g.proxies.length) { planned.push(null); continue; }
        var kept = [];
        var hadNode = false;
        for (j = 0; j < g.proxies.length; j++) {
          n = g.proxies[j];
          if (typeof n !== 'string') { kept.push(n); continue; }
          if (BUILTIN.indexOf(n) !== -1 || groupNames[n]) { kept.push(n); continue; }
          hadNode = true;
          if (deadSet[n]) { dropped++; continue; }
          kept.push(n);
        }
        // 只有「本来有节点、剔除后还剩节点」才替换；否则保持该组原样
        if (hadNode && kept.length === 0) { planned.push(null); continue; }
        planned.push(kept);
        keptTotal += kept.length;
      }

      if (keptTotal > 0) {
        for (i = 0; i < groups.length; i++) {
          if (planned[i]) groups[i].proxies = planned[i];
        }
      } else {
        dropped = 0;   // 兜底触发，视作没有剔除
      }
    }

    if (typeof console !== 'undefined' && console.log) {
      console.log('[campus-fix] ' + profileName + ' | 修复入口IP: ' + fixedCount +
                  ' | 组内剔除: ' + dropped);
    }
    return config;
  } catch (e) {
    return config;   // 任何异常都不影响订阅正常加载
  }
}
"""


def render(env: dict, profile: dict, decision: dict, enable_filter: bool = False) -> str:
    ips = [r["ip"] for r in ((profile.get("cf_preferred") or {}).get("results") or [])]
    if not ips:
        ips = ((profile.get("cf") or {}).get("working_ips") or [])[:12]
    domains = profile.get("cf_fronted_domains") or []
    dead = {name: (s.get("dead") or [])
            for name, s in ((profile.get("nodes") or {}).get("subs") or {}).items()}

    return SCRIPT_TEMPLATE % {
        "stamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "host": env.get("host", "?"),
        "verdict": decision.get("verdict", "?"),
        "verdict_title": decision.get("title", ""),
        "subs": "、".join(s.get("name", "?") for s in env.get("subscriptions") or []),
        "enable_filter": "true" if enable_filter else "false",
        "ips": json.dumps(ips, indent=6).replace("\n", "\n    "),
        "domains": json.dumps(domains, indent=6).replace("\n", "\n    "),
        "dead": json.dumps(dead, indent=6, ensure_ascii=False).replace("\n", "\n    "),
    }


def preview(env: dict, profile: dict, decision: dict, enable_filter: bool = False):
    """返回 (脚本文本, 变更摘要 dict)。"""
    text = render(env, profile, decision, enable_filter=enable_filter)
    dead = {name: len(s.get("dead") or [])
            for name, s in ((profile.get("nodes") or {}).get("subs") or {}).items()}
    ips = [r["ip"] for r in ((profile.get("cf_preferred") or {}).get("results") or [])]
    summary = {
        "target": env["client"].get("global_script"),
        "cf_ips": len(ips),
        "cf_fronted_domains": len(profile.get("cf_fronted_domains") or []),
        "dead_filter_enabled": bool(enable_filter),
        "dead_available": dead,
        "dead_total": sum(dead.values()) if enable_filter else 0,
        "script_bytes": len(text.encode("utf-8")),
    }
    return text, summary


def apply(env: dict, profile: dict, decision: dict, dry_run: bool = False,
          enable_filter: bool = False):
    """写入全局扩展脚本。返回 (ok, result)。"""
    if not env["client"].get("supports_global_script"):
        return False, {
            "error": "当前 Clash Verge 不支持全局扩展脚本",
            "basis": env["client"].get("capability_basis"),
            "hint": "需手动把脚本绑定到订阅级「扩展脚本」，或升级 Clash Verge",
        }
    if not decision.get("implementable"):
        return False, {
            "error": "策略 %s 不可自动实施" % decision.get("action"),
            "blockers": decision.get("blockers"),
            "advice": decision.get("advice"),
        }

    text, summary = preview(env, profile, decision, enable_filter=enable_filter)
    target = env["client"]["global_script"]

    out_local = os.path.join(envprobe.DATA_DIR, "Script.latest.js")
    os.makedirs(os.path.dirname(out_local), exist_ok=True)
    with open(out_local, "w", encoding="utf-8") as fh:
        fh.write(text)
    summary["preview_path"] = out_local

    if dry_run:
        summary["dry_run"] = True
        return True, summary

    if not target or not os.path.isdir(os.path.dirname(target)):
        return False, {"error": "全局扩展脚本路径无效：%s" % target}

    if os.path.isfile(target):
        backup = target + ".bak"
        shutil.copy2(target, backup)
        summary["backup"] = backup
        with open(target, "r", encoding="utf-8", errors="replace") as fh:
            summary["previous_bytes"] = len(fh.read().encode("utf-8"))

    with open(target, "w", encoding="utf-8") as fh:
        fh.write(text)
    summary["written"] = target
    return True, summary


def summarize_result(ok: bool, result: dict) -> str:
    if not ok:
        L = ["实施失败：%s" % result.get("error")]
        for b in result.get("blockers") or []:
            L.append("  阻碍: %s" % b)
        for a in result.get("advice") or []:
            L.append("  建议: %s" % a)
        if result.get("basis"):
            L.append("  能力判定依据: %s" % result["basis"])
        if result.get("hint"):
            L.append("  %s" % result["hint"])
        return "\n".join(L)

    L = []
    if result.get("dry_run"):
        L.append("干跑完成（未写入 Clash Verge）")
    else:
        L.append("已写入全局扩展脚本 → %s" % result.get("written"))
    if result.get("backup"):
        L.append("原文件已备份 → %s" % result["backup"])
    L.append("  优选 IP        : %d 个" % result.get("cf_ips", 0))
    L.append("  CF 前置域名    : %d 个" % result.get("cf_fronted_domains", 0))
    if result.get("dead_filter_enabled"):
        L.append("  剔除死节点     : 已启用，%d 个 %s"
                 % (result.get("dead_total", 0), result.get("dead_available") or {}))
    else:
        avail = result.get("dead_available") or {}
        L.append("  剔除死节点     : 已关闭（可剔除 %d 个：%s；用 --filter-dead 启用）"
                 % (sum(avail.values()), avail))
    L.append("  脚本大小       : %d 字节" % result.get("script_bytes", 0))
    L.append("  预演副本       : %s" % result.get("preview_path"))
    return "\n".join(L)


def cli_apply(args):
    from . import profiling
    from .cli import EXIT_ENV, EXIT_OK, EXIT_UNSUPPORTED

    env = envprobe.load_env()
    if not env:
        print("机器档案不存在，请先运行 probe。")
        return EXIT_ENV

    prof = profiling.load_profile(env.get("host"))
    if not prof:
        print("网络画像不存在，请先运行 profile。")
        return EXIT_ENV

    decision = strategy.choose(prof)
    ok, result = apply(env, prof, decision,
                       dry_run=getattr(args, "dry_run", False),
                       enable_filter=getattr(args, "filter_dead", False))

    if args.json:
        print(json.dumps({"ok": ok, "decision": decision, "result": result},
                         indent=2, ensure_ascii=False))
    else:
        print(strategy.summarize(decision))
        print()
        print(summarize_result(ok, result))
        if ok and not result.get("dry_run"):
            print()
            print("接着在 Clash Verge 里：订阅卡片右键 →「刷新」（或重启 Clash Verge）")

    if not ok:
        return EXIT_UNSUPPORTED
    return EXIT_OK
