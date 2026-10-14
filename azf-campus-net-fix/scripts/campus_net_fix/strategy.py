# -*- coding: utf-8 -*-
"""策略选择：把画像判定映射为**预先定义好的**动作。

硬性规则（见计划）：AI 只做「选择」，不做「创作」。
策略必须在这里穷举定义，否则同一个问题每次会得到不同解法，无法回归测试。
"""
from __future__ import annotations

# verdict → 策略定义
#   implementable=True  内核可以自动实施
#   implementable=False 只输出报告与建议，绝不硬改配置（诚实降级原则）
STRATEGIES = {
    "A": {
        "name": "cf-preferred-ip",
        "title": "IP 层黑名单（部分）",
        "implementable": True,
        "why": "存在可达的 Cloudflare anycast IP，且订阅里有 Cloudflare 前置节点，"
               "换入口 IP 能绕过 IP 层封锁。",
        "does": ["把 CF 前置节点的入口 IP 换成实测可达的优选 IP",
                 "把实测确认连不通的节点从所有代理组剔除",
                 "写入 Clash Verge 全局扩展脚本（对以后新增订阅也生效）"],
    },
    "B": {
        "name": "report-sni-blocked",
        "title": "SNI / TLS 层阻断",
        "implementable": False,
        "why": "TCP 可通但 TLS 握手被重置 —— 封锁发生在 TLS 层，换入口 IP 完全无效。",
        "advice": [
            "换 IP 这条路在当前网络不成立，不要浪费时间重扫优选 IP",
            "可考虑：走 CDN 前置 + 未被阻断的 SNI、或改用不依赖 SNI 的协议",
            "若机场提供国内中转入口，优先使用（入口在国内，不经 TLS 层封锁）",
        ],
    },
    "C": {
        "name": "report-protocol-blocked",
        "title": "协议 / 端口层封锁",
        "implementable": False,
        "why": "没有可达的 Cloudflare IP 可换，且 UDP/QUIC 通道受限。",
        "advice": [
            "优先尝试 QUIC 系协议（Hysteria2 / TUIC），但需先确认 UDP 端口放行",
            "若 UDP 被整体限速或封锁，只能走 TCP 系 + 国内中转入口",
        ],
    },
    "D": {
        "name": "report-portal",
        "title": "需要 portal 认证",
        "implementable": False,
        "why": "外网请求被重定向到认证页，属于接入层问题，与代理配置无关。",
        "advice": ["先在浏览器完成校园网认证，再重新运行 profile"],
    },
    "E": {
        "name": "noop",
        "title": "未发现封锁",
        "implementable": True,
        "why": "绝大多数节点已可达，无需任何修改。",
        "does": ["不做任何修改（幂等退出）"],
    },
    "X": {
        "name": "escalate",
        "title": "未知封锁形态",
        "implementable": False,
        "why": "画像不匹配任何已知策略。",
        "advice": [
            "不要硬改配置",
            "把 profile 的 JSON 与证据交给 AI 诊断（L1）",
            "若确认是新的封锁形态，进入 L2 修改内核",
        ],
    },
}


def choose(profile: dict) -> dict:
    """依据画像选策略。返回可序列化的决策对象。"""
    verdict = (profile or {}).get("verdict") or "X"
    spec = STRATEGIES.get(verdict, STRATEGIES["X"])

    nodes = (profile or {}).get("nodes") or {}
    cf = (profile or {}).get("cf") or {}
    pref = (profile or {}).get("cf_preferred") or {}

    # 策略 A 的额外前置条件：必须真的存在可换的目标与可改的节点
    blockers = []
    if spec["implementable"]:
        if not (pref.get("working") or 0):
            blockers.append("没有实测可用的 Cloudflare 优选 IP")
        if not ((profile or {}).get("cf_fronted_domains")):
            blockers.append("订阅里没有 Cloudflare 前置节点，换入口 IP 无处可换")

    implementable = bool(spec["implementable"] and not blockers)

    return {
        "verdict": verdict,
        "action": spec["name"],
        "title": spec["title"],
        "implementable": implementable,
        "why": spec["why"],
        "does": spec.get("does") or [],
        "advice": spec.get("advice") or [],
        "blockers": blockers,
        "facts": {
            "nodes_total": nodes.get("total", 0),
            "nodes_reachable": nodes.get("reachable", 0),
            "cf_ratio": cf.get("ratio"),
            "cf_preferred_working": pref.get("working"),
            "cf_fronted_domains": len((profile or {}).get("cf_fronted_domains") or []),
            "sni": ((profile or {}).get("layers") or {}).get("sni", {}).get("verdict"),
            "udp443_ok": ((profile or {}).get("layers") or {}).get(
                "udp_ports", {}).get("udp443_ok"),
        },
    }


def summarize(decision: dict) -> str:
    L = []
    L.append("策略: %s —— %s" % (decision["action"], decision["title"]))
    L.append("  可自动实施: %s" % ("是" if decision["implementable"] else "否"))
    L.append("  依据: %s" % decision["why"])
    if decision["does"]:
        L.append("  将执行:")
        for x in decision["does"]:
            L.append("    - %s" % x)
    if decision["advice"]:
        L.append("  建议:")
        for x in decision["advice"]:
            L.append("    - %s" % x)
    if decision["blockers"]:
        L.append("  阻碍:")
        for x in decision["blockers"]:
            L.append("    - %s" % x)
    return "\n".join(L)
