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
//
//  附带：Tailscale 共存补丁（2026-11-11 加入，默认开启）
//    开 TUN 时：tailnet 网段不被接管、`*.tailscale.com` 解析成真实 IP、
//    ts.net 域名交给 MagicDNS、Clash 不把 Tailscale 虚拟网卡当出口。
//    ⚠ 不要默认让 tailscaled 直连：校园网通常直连不通控制面，只有已注册的
//      节点能靠缓存 DERP 撑住，一需要重新注册就卡死。TS_DIRECT_PROCESS 默认 false。
//    ⚠ 路由层的网段排除（tun.route-exclude-address）**不在这个脚本里生效**：
//      Verge 的 TUN 设置层会把它顶回 config.yaml 的值，所以由 apply() 直接改
//      config.yaml。脚本里那份只是给不覆盖该字段的版本兜底。
//    四个开关见 main() 顶部的 TS_* 变量。
// ============================================================================

function main(config, profileName) {
  try {
    // ========================================================================
    //  Tailscale 共存补丁（2026-11-11 并入模板）
    //  作用：Clash 开着 TUN 时，tailnet(100.64.0.0/10) 流量不被接管、
    //        Tailscale 进程的外网连接走直连、ts.net 域名交给 MagicDNS。
    //  独立 try/catch：本段出错只跳过本段，绝不影响下面的入口 IP 修复。
    //  要关某一项，把对应开关改成 false 即可。
    // ========================================================================
    try {
      var TS_ROUTE_EXCLUDE  = true;  // 兜底；2.5.x 会被 Verge 设置层覆盖（见 apply 写 config.yaml）
      var TS_DIRECT_PROCESS = false; // 默认 false：让 tailscaled 走正常规则（校园网直连控制面常不通）
      var TS_MAGIC_DNS      = true;  // ts.net 交给 MagicDNS(100.100.100.100)
      var TS_EXCLUDE_IFACE  = true;  // 不让 Clash 把 Tailscale 虚拟网卡当出口
      var TS_V4 = '100.64.0.0/10';
      var TS_V6 = 'fd7a:115c:a1e0::/48';

      var tsPush = function (arr, val) {
        if (!Array.isArray(arr)) arr = [];
        if (arr.indexOf(val) === -1) arr.push(val);
        return arr;
      };
      var tsLog = [];

      if (config && typeof config === 'object') {
        config.tun = config.tun || {};

        if (TS_ROUTE_EXCLUDE) {
          var excl = tsPush(config.tun['route-exclude-address'], TS_V4);
          excl = tsPush(excl, TS_V6);
          config.tun['route-exclude-address'] = excl;
          tsLog.push('route-exclude');
        }

        if (TS_EXCLUDE_IFACE) {
          var inc = config.tun['include-interface'];
          if (inc && inc.length) {
            tsLog.push('skip-iface(已有include-interface)');
          } else {
            config.tun['exclude-interface'] =
              tsPush(config.tun['exclude-interface'], 'Tailscale');
            tsLog.push('exclude-iface');
          }
        }

        if (TS_DIRECT_PROCESS) {
          var tsRules = [
            'PROCESS-NAME,tailscaled.exe,DIRECT',
            'PROCESS-NAME,tailscale.exe,DIRECT',
            'PROCESS-NAME,tailscale-ipn.exe,DIRECT',
            'IP-CIDR,' + TS_V4 + ',DIRECT,no-resolve',
            'IP-CIDR6,' + TS_V6 + ',DIRECT,no-resolve'
          ];
          var rules = Array.isArray(config.rules) ? config.rules : [];
          var kept = [];
          for (var k = 0; k < rules.length; k++) {
            if (tsRules.indexOf(rules[k]) === -1) kept.push(rules[k]);   // 去重，重复应用不堆积
          }
          config.rules = tsRules.concat(kept);
          if (!config['find-process-mode']) config['find-process-mode'] = 'strict';
          tsLog.push('rules');
        }

        if (TS_MAGIC_DNS) {
          config.dns = config.dns || {};
          var fif = tsPush(config.dns['fake-ip-filter'], '+.ts.net');
          fif = tsPush(fif, '*.ts.net');
          fif = tsPush(fif, 'ts.net');
          // 控制面 / DERP 必须解析成真实 IP：这些域名若拿到 fake-ip(198.18.x)，
          // 走 DIRECT 的 tailscaled 会把包发到只存在于 Clash 内部的地址，注册必超时。
          fif = tsPush(fif, '+.tailscale.com');
          fif = tsPush(fif, '*.tailscale.com');
          fif = tsPush(fif, '+.tailscale.io');
          config.dns['fake-ip-filter'] = fif;

          var np = config.dns['nameserver-policy'];
          if (!np || typeof np !== 'object') np = {};
          np['+.ts.net'] = ['100.100.100.100'];
          config.dns['nameserver-policy'] = np;
          tsLog.push('magicdns');
        }

        if (typeof console !== 'undefined' && console.log) {
          console.log('[tailscale] ' + tsLog.join(',') + ' | ' + profileName);
        }
      }
    } catch (tsErr) {
      /* Tailscale 补丁异常一律忽略 */
    }

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


# ---------------------------------------------------------------------------
# Verge 的 TUN 设置存储（实测 2026-11-11）
# ---------------------------------------------------------------------------
# 只有数据目录下 config.yaml 里的 tun.route-exclude-address 会进入运行时配置。
# 全局扩展脚本和全局扩展配置（Merge.yaml）里写的同名字段，都会被 Verge 的 TUN
# 设置层顶回 config.yaml 的值 —— 同一次实验里 exclude-interface / rules / dns
# 都活了下来，唯独这个字段被覆盖。所以 Tailscale 的网段排除必须写进 config.yaml，
# 而且要重启 Clash Verge（刷新订阅不够）才生效。
CORE_CONFIG_NAME = "config.yaml"
TS_ROUTE_EXCLUDE = ("100.64.0.0/10", "fd7a:115c:a1e0::/48")


def core_config_path(env: dict):
    data_dir = (env.get("client") or {}).get("data_dir")
    if not data_dir:
        return None
    p = os.path.join(data_dir, CORE_CONFIG_NAME)
    return p if os.path.isfile(p) else None


def app_running(env: dict):
    """Clash Verge 的 GUI 是否在运行；判断不了返回 None。"""
    from . import clashverge

    name = os.path.basename(((env.get("client") or {}).get("gui_exe") or "")).lower()
    if not name:
        return None
    try:
        paths = clashverge.list_process_paths()
    except Exception:
        return None
    if not paths:
        return None
    return any(os.path.basename(p).lower() == name for _pid, p in paths)


def patch_core_tun_exclude(env: dict, dry_run: bool = False):
    """把 tailnet 网段写进 config.yaml 的 tun.route-exclude-address。

    返回 (ok, info)。ok=False 只表示这一项没写成，不阻断脚本本身的实施。
    """
    from . import yamlcompat

    path = core_config_path(env)
    if not path:
        return False, {"error": "数据目录里没有 config.yaml",
                       "hint": "该版本可能不把 TUN 设置存在这里，需在 GUI 的 TUN 设置里手工加排除网段"}

    try:
        cfg = yamlcompat.load_file(path) or {}
    except Exception as e:
        return False, {"error": "config.yaml 解析失败：%s" % e, "path": path}
    if not isinstance(cfg, dict):
        return False, {"error": "config.yaml 顶层不是映射", "path": path}

    tun = cfg.get("tun")
    if not isinstance(tun, dict):
        tun = {}
        cfg["tun"] = tun
    cur = tun.get("route-exclude-address")
    cur = list(cur) if isinstance(cur, list) else []
    added = [c for c in TS_ROUTE_EXCLUDE if c not in cur]

    info = {"path": path, "before": list(cur), "added": added,
            "app_running": app_running(env), "changed": bool(added)}
    if not added:
        info["after"] = list(cur)
        return True, info

    tun["route-exclude-address"] = cur + added
    info["after"] = tun["route-exclude-address"]
    if dry_run:
        info["dry_run"] = True
        return True, info

    backup = path + ".bak"
    shutil.copy2(path, backup)
    info["backup"] = backup
    yamlcompat.dump(cfg, path)
    return True, info


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

    # TUN 排除网段只能写进 Verge 的 config.yaml，写在脚本里会被设置层覆盖。
    # 放在干跑分支之前，这样 --dry-run 也能告诉用户"将会改什么"。
    ok_core, core = patch_core_tun_exclude(env, dry_run=dry_run)
    summary["core_config_ok"] = ok_core
    summary["core_config"] = core

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
    L.append("  Tailscale 兼容 : 已内置（进程直连 + MagicDNS + 排除网段）")

    core = result.get("core_config") or {}
    if core.get("error"):
        L.append("  TUN 排除网段   : 未写入 — %s" % core["error"])
        if core.get("hint"):
            L.append("                   %s" % core["hint"])
    elif core.get("dry_run") and core.get("changed"):
        L.append("  TUN 排除网段   : 将写入 config.yaml（%s）— 干跑未落盘"
                 % "、".join(core.get("added") or []))
    elif core.get("changed"):
        L.append("  TUN 排除网段   : 已写入 config.yaml（%s）"
                 % "、".join(core.get("added") or []))
        L.append("                   备份 %s" % core.get("backup"))
        L.append("                   ⚠ 必须完全退出并重启 Clash Verge 才生效（刷新订阅不够）")
        if core.get("app_running"):
            L.append("                   ⚠ Clash Verge 正在运行：它退出时会回写 config.yaml，"
                     "建议先退出再跑 apply")
    elif core:
        L.append("  TUN 排除网段   : 已存在，无需改动")
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
