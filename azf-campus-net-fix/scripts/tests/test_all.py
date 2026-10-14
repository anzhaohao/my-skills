# -*- coding: utf-8 -*-
"""azf-campus-net-fix 测试套件（纯 stdlib unittest，无第三方测试框架）。

    python scripts/tests/test_all.py            # 全部
    python scripts/tests/test_all.py -k yaml    # 过滤

分三层：
  单元      —— 纯逻辑，无网络
  集成      —— 读真实 Clash Verge 配置（已跳过缺失项）
  端到端    —— 经真实代理请求（需 --e2e 显式开启）
"""
from __future__ import annotations

import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)

from campus_net_fix import cfnets, envprobe, netif, override, strategy, yamlcompat  # noqa: E402
from campus_net_fix import clashverge as cv  # noqa: E402
from campus_net_fix import reach  # noqa: E402
from campus_net_fix.util import free_port, is_ipv4  # noqa: E402


# ---------------------------------------------------------------------------
# 单元：YAML
# ---------------------------------------------------------------------------
class TestYaml(unittest.TestCase):
    """今天踩过的坑：flow-style 条目会被朴素解析器整段漏掉。"""

    BLOCK = """
proxies:
- name: A
  type: vless
  server: a.example.com
  port: 443
  tls: true
  servername: s.example.com
  network: ws
  ws-opts:
    path: /x
    headers:
      Host: h.example.com
proxy-groups:
- name: G
  type: select
  proxies: [A, DIRECT]
rules:
- MATCH,G
"""

    FLOW = """
proxies:
- { name: A, type: vless, server: a.example.com, port: 443, tls: true, servername: s.example.com, network: ws, ws-opts: { path: /x, headers: { Host: h.example.com } } }
- { name: B, type: vmess, server: b.example.com, port: 8443, tls: true, servername: t.example.com, network: ws, ws-opts: { path: /y, headers: { Host: t.example.com } } }
proxy-groups:
- { name: G, type: select, proxies: [A, B, DIRECT] }
rules:
- MATCH,G
"""

    def test_block_style(self):
        cfg = yamlcompat.load_text(self.BLOCK)
        self.assertEqual(len(cfg["proxies"]), 1)
        self.assertEqual(cfg["proxies"][0]["server"], "a.example.com")
        self.assertEqual(cfg["proxies"][0]["ws-opts"]["headers"]["Host"],
                         "h.example.com")

    def test_flow_style_not_dropped(self):
        """flow-style 必须被完整解析 —— 这是早期解析器漏节点的根因。"""
        cfg = yamlcompat.load_text(self.FLOW)
        self.assertEqual(len(cfg["proxies"]), 2)
        self.assertEqual([p["name"] for p in cfg["proxies"]], ["A", "B"])
        self.assertEqual(cfg["proxies"][1]["server"], "b.example.com")

    def test_roundtrip_dump(self):
        cfg = yamlcompat.load_text(self.FLOW)
        text = yamlcompat.dump_text(cfg)
        again = yamlcompat.load_text(text)
        self.assertEqual(len(again["proxies"]), 2)
        self.assertEqual(again["proxies"][0]["name"], "A")


# ---------------------------------------------------------------------------
# 单元：Cloudflare 判定
# ---------------------------------------------------------------------------
class TestCfnets(unittest.TestCase):

    def test_is_cf_ip(self):
        for ip in ("104.16.132.229", "172.67.193.12", "162.159.140.1",
                   "188.114.96.1", "108.162.198.60"):
            self.assertTrue(cfnets.is_cf_ip(ip), ip)
        for ip in ("223.5.5.5", "8.8.8.8", "59.72.114.170", "192.168.1.1",
                   "110.242.70.57"):
            self.assertFalse(cfnets.is_cf_ip(ip), ip)

    def test_is_cf_ip_malformed(self):
        for bad in ("", "not-an-ip", "1.2.3", "999.1.1.1", None):
            self.assertFalse(cfnets.is_cf_ip(bad))

    def test_heuristic_accepts_cdn_fronted(self):
        node = {"name": "JP", "type": "vless", "server": "unamecf.example.com",
                "port": 443, "tls": True, "network": "ws",
                "servername": "ujp1.example.com",
                "ws-opts": {"path": "/x"}}
        self.assertTrue(cfnets.looks_cdn_fronted(node))

    def test_heuristic_rejects_reality(self):
        """REALITY 借 SNI，换入口 IP 必坏 —— 必须排除。"""
        node = {"type": "vless", "server": "pq.aws48.example.top", "port": 443,
                "tls": True, "servername": "iosapps.itunes.apple.com",
                "flow": "xtls-rprx-vision",
                "reality-opts": {"public-key": "x", "short-id": "y"}}
        self.assertFalse(cfnets.looks_cdn_fronted(node))

    def test_heuristic_rejects_bare_ip_and_same_sni(self):
        base = {"type": "vless", "port": 443, "tls": True, "network": "ws"}
        self.assertFalse(cfnets.looks_cdn_fronted(
            dict(base, server="1.2.3.4", servername="a.example.com")))
        self.assertFalse(cfnets.looks_cdn_fronted(
            dict(base, server="a.example.com", servername="a.example.com")))
        self.assertFalse(cfnets.looks_cdn_fronted(
            dict(base, server="a.example.com", servername="")))
        self.assertFalse(cfnets.looks_cdn_fronted(
            dict(base, server="a.example.com", servername="b.example.com",
                 tls=False)))
        self.assertFalse(cfnets.looks_cdn_fronted(
            dict(base, server="a.example.com", servername="b.example.com",
                 network="tcp")))

    def test_heuristic_rejects_hysteria2(self):
        node = {"type": "hysteria2", "server": "a.example.com", "port": 443,
                "sni": "www.apple.com"}
        self.assertFalse(cfnets.looks_cdn_fronted(node))


# ---------------------------------------------------------------------------
# 单元：策略矩阵
# ---------------------------------------------------------------------------
def _profile(verdict_facts):
    p = {"channel": {"raw_channel_ok": True},
         "baseline": {"internet": True, "portal_redirect": False},
         "cf": {"reachable": 20, "sampled": 34, "ratio": 0.6},
         "cf_preferred": {"working": 20, "tested": 34},
         "cf_fronted_domains": ["a.example.com"],
         "nodes": {"total": 100, "reachable": 30, "subs": {}},
         "layers": {"sni": {"verdict": "clean"}, "sni_node": {"verdict": "clean"},
                    "udp_ports": {"udp443_ok": True}},
         "verdict": "A"}
    p.update(verdict_facts or {})
    return p


class TestVerdict(unittest.TestCase):
    from campus_net_fix import profiling as _pf

    def test_channel_broken_is_unknown(self):
        p = _profile({"channel": {"raw_channel_ok": False}})
        self.assertEqual(self._pf.decide_verdict(p), "X")

    def test_portal(self):
        p = _profile({"baseline": {"internet": True, "portal_redirect": True}})
        self.assertEqual(self._pf.decide_verdict(p), "D")

    def test_no_internet(self):
        p = _profile({"baseline": {"internet": False, "portal_redirect": False}})
        self.assertEqual(self._pf.decide_verdict(p), "X")

    def test_mostly_working_is_noop(self):
        p = _profile({"nodes": {"total": 100, "reachable": 95, "subs": {}}})
        self.assertEqual(self._pf.decide_verdict(p), "E")

    def test_strategy_a_when_preferred_ips_work(self):
        """回归：不能因为「知名被封 SNI 被拦」就把可行方案判成 B。"""
        p = _profile({"layers": {"sni": {"verdict": "blocked"},
                                 "sni_node": {"verdict": "clean"},
                                 "udp_ports": {"udp443_ok": True}}})
        self.assertEqual(self._pf.decide_verdict(p), "A")

    def test_sni_b_when_no_working_preferred_and_node_sni_blocked(self):
        p = _profile({"cf_preferred": {"working": 0, "tested": 34},
                      "cf": {"reachable": 10, "sampled": 34, "ratio": 0.3},
                      "layers": {"sni": {"verdict": "clean"},
                                 "sni_node": {"verdict": "blocked"},
                                 "udp_ports": {"udp443_ok": True}}})
        self.assertEqual(self._pf.decide_verdict(p), "B")

    def test_c_when_no_cf_and_udp_blocked(self):
        p = _profile({"cf_preferred": {"working": 0},
                      "cf": {"reachable": 0, "sampled": 34, "ratio": 0.0},
                      "cf_fronted_domains": [],
                      "layers": {"sni": {"verdict": "clean"},
                                 "sni_node": {"verdict": "unknown"},
                                 "udp_ports": {"udp443_ok": False}}})
        self.assertEqual(self._pf.decide_verdict(p), "C")


class TestStrategy(unittest.TestCase):

    def test_all_verdicts_mapped(self):
        for v in ("A", "B", "C", "D", "E", "X"):
            d = strategy.choose({"verdict": v})
            self.assertEqual(d["verdict"], v)
            self.assertTrue(d["action"], v)
            self.assertIsInstance(d["implementable"], bool)

    def test_a_not_implementable_without_working_ips(self):
        d = strategy.choose({"verdict": "A", "cf_preferred": {"working": 0},
                             "cf_fronted_domains": ["a.example.com"]})
        self.assertFalse(d["implementable"])
        self.assertTrue(any("优选 IP" in b for b in d["blockers"]))

    def test_a_not_implementable_without_cf_nodes(self):
        d = strategy.choose({"verdict": "A", "cf_preferred": {"working": 5},
                             "cf_fronted_domains": []})
        self.assertFalse(d["implementable"])

    def test_bcdx_not_implementable(self):
        for v in ("B", "C", "D", "X"):
            d = strategy.choose({"verdict": v})
            self.assertFalse(d["implementable"], v)


# ---------------------------------------------------------------------------
# 单元：工具与网卡
# ---------------------------------------------------------------------------
class TestUtil(unittest.TestCase):

    def test_is_ipv4(self):
        self.assertTrue(is_ipv4("1.2.3.4"))
        self.assertFalse(is_ipv4("1.2.3"))
        self.assertFalse(is_ipv4("256.1.1.1"))
        self.assertFalse(is_ipv4(""))

    def test_free_port_unique_and_bindable(self):
        import socket
        ports = {free_port() for _ in range(5)}
        self.assertGreaterEqual(len(ports), 4)
        for p in ports:
            s = socket.socket()
            try:
                s.bind(("127.0.0.1", p))
            finally:
                s.close()

    def test_physical_interface_prefers_real_nic(self):
        """隧道/虚拟网卡不能击败真实网卡。"""
        a = netif.physical_interface()
        if not a:
            self.skipTest("本机无法枚举网卡")
        self.assertNotEqual(a["iftype"], netif.IF_TYPE_SOFTWARE_LOOPBACK)
        self.assertTrue(a["ipv4"])
        self.assertTrue(a["has_gateway"])
        self.assertFalse(netif._looks_virtual(a),
                         "选中了虚拟网卡：%s" % a["name"])

    def test_virtual_hint_matching(self):
        self.assertTrue(netif._looks_virtual({"name": "Meta", "description": ""}))
        self.assertTrue(netif._looks_virtual(
            {"name": "X", "description": "VMware Virtual Ethernet Adapter"}))
        self.assertFalse(netif._looks_virtual(
            {"name": "WLAN", "description": "Intel(R) Wi-Fi 6E AX211 160MHz"}))


# ---------------------------------------------------------------------------
# 集成：与真实 Clash Verge 配置
# ---------------------------------------------------------------------------
def _live_env():
    return envprobe.load_env()


class TestClashVergeAdapter(unittest.TestCase):

    def setUp(self):
        self.env = _live_env()
        if not self.env:
            self.skipTest("无机器档案，跳过（先运行 probe）")

    def test_data_dir_and_core_exist(self):
        c = self.env["client"]
        self.assertTrue(os.path.isdir(c["install_dir"]))
        self.assertTrue(os.path.isfile(c["gui_exe"]))
        self.assertTrue(os.path.isfile(self.env["core"]["exe"]))

    def test_core_version_really_runs(self):
        """版本必须是真跑 -v 得到的，不能靠文件名猜。"""
        v = cv.core_version(self.env["core"]["exe"])
        self.assertTrue(v and v[0].isdigit(), "内核版本异常: %r" % v)

    def test_capability_has_basis(self):
        """能力判定必须给出可核查的依据，不能是无据结论。"""
        c = self.env["client"]
        self.assertTrue(c.get("capability_basis"))
        if c.get("supports_global_script"):
            self.assertTrue(os.path.isfile(c["global_script"]))

    def test_subscriptions_parsed(self):
        self.assertTrue(self.env["subscriptions"])
        for s in self.env["subscriptions"]:
            self.assertTrue(os.path.isfile(s["path"]))
            self.assertGreater(s["nodes"], 0, s["name"])

    def test_doctor_passes_on_live_env(self):
        ok, issues, _ = envprobe.doctor(self.env)
        self.assertTrue(ok, "体检未通过: %s" % issues)


class TestFixSemantics(unittest.TestCase):
    """跨语言一致性：Python 预演与 JS 脚本必须选中同一批节点。"""

    def setUp(self):
        self.env = _live_env()
        if not self.env:
            self.skipTest("无机器档案")

    def _all_proxies(self):
        out = []
        for s in self.env["subscriptions"]:
            sub = cv.read_subscription(s["path"])
            if sub:
                out += sub["proxies"]
        return out

    def test_apply_fix_only_touches_cf_fronted(self):
        proxies = self._all_proxies()
        if not proxies:
            self.skipTest("无节点")
        domains = sorted({p["server"] for p in proxies
                          if cfnets.looks_cdn_fronted(p)})
        ips = ["162.159.140.1", "104.26.0.1"]
        fixed, n = reach.apply_cf_fix(proxies, domains, ips)
        self.assertEqual(len(fixed), len(proxies))
        for a, b in zip(proxies, fixed):
            if a["server"] != b["server"]:
                n_changed = n
                self.assertIn(a["server"], domains)
                self.assertIn(b["server"], ips)
            # 名称 / 类型 / SNI 一律不得改动
            self.assertEqual(a.get("name"), b.get("name"))
            self.assertEqual(a.get("type"), b.get("type"))
            self.assertEqual(a.get("servername"), b.get("servername"))
            self.assertEqual(a.get("sni"), b.get("sni"))
            self.assertEqual(a.get("reality-opts"), b.get("reality-opts"))
            self.assertEqual(a.get("ws-opts"), b.get("ws-opts"))

    def test_reality_nodes_never_rewritten(self):
        proxies = self._all_proxies()
        domains = sorted({p["server"] for p in proxies
                          if cfnets.looks_cdn_fronted(p)})
        fixed, _ = reach.apply_cf_fix(proxies, domains, ["104.16.0.1"])
        for a, b in zip(proxies, fixed):
            if a.get("reality-opts"):
                self.assertEqual(a["server"], b["server"],
                                 "REALITY 节点被误改：%s" % a.get("name"))

    def test_pseudo_nodes_skipped(self):
        self.assertTrue(reach._is_pseudo({"server": "127.0.0.1"}))
        self.assertTrue(reach._is_pseudo({"server": ""}))
        self.assertFalse(reach._is_pseudo({"server": "a.example.com"}))


class TestOverrideRender(unittest.TestCase):

    def test_render_contains_expected_constants(self):
        env = {"host": "H", "client": {"global_script": "x.js",
                                       "supports_global_script": True},
               "subscriptions": [{"name": "机场A"}]}
        prof = _profile({})
        prof["cf_preferred"] = {"working": 2, "tested": 3,
                                "results": [{"ip": "104.16.0.1", "delay": 100},
                                            {"ip": "162.159.140.1", "delay": 110}]}
        prof["nodes"] = {"total": 10, "reachable": 6,
                         "subs": {"机场A": {"total": 10, "reachable": 6,
                                            "dead": ["n1", "n2"], "alive": []}}}
        decision = strategy.choose(prof)
        text = override.render(env, prof, decision)
        self.assertIn("104.16.0.1", text)
        self.assertIn("162.159.140.1", text)
        self.assertIn("a.example.com", text)
        self.assertIn("n1", text)
        self.assertIn("function main(config, profileName)", text)
        self.assertIn("looksCdnFronted", text)
        self.assertIn("reality-opts", text)

    def test_no_double_percent_left_unrendered(self):
        """模板里的 %% 必须被正确还原成 %，且不残留占位符。"""
        env = {"host": "H", "client": {"global_script": "x.js",
                                       "supports_global_script": True},
               "subscriptions": [{"name": "A"}]}
        prof = _profile({})
        prof["cf_preferred"] = {"working": 1, "tested": 1,
                                "results": [{"ip": "104.16.0.1", "delay": 1}]}
        prof["nodes"] = {"total": 1, "reachable": 0, "subs": {}}
        text = override.render(env, prof, strategy.choose(prof))
        self.assertNotIn("%(", text)
        self.assertNotIn("%%", text)
        self.assertIn("CF_IPS[fixedCount % CF_IPS.length]", text)

    def test_apply_refuses_when_not_implementable(self):
        env = {"host": "H", "client": {"global_script": "x.js",
                                       "supports_global_script": True},
               "subscriptions": []}
        prof = _profile({})
        ok, res = override.apply(env, prof, strategy.choose({"verdict": "B"}),
                                 dry_run=True)
        self.assertFalse(ok)
        self.assertIn("不可自动实施", res["error"])

    def test_apply_refuses_without_global_script_support(self):
        env = {"host": "H",
               "client": {"global_script": None, "supports_global_script": False,
                          "capability_basis": "test"},
               "subscriptions": []}
        prof = _profile({})
        ok, res = override.apply(env, prof, strategy.choose({"verdict": "E"}),
                                 dry_run=True)
        self.assertFalse(ok)
        self.assertIn("不支持全局扩展脚本", res["error"])


# ---------------------------------------------------------------------------
# 端到端（默认跳过，需 --e2e）
# ---------------------------------------------------------------------------
class TestEndToEnd(unittest.TestCase):

    def test_verify_through_proxy(self):
        if "--e2e" not in sys.argv:
            self.skipTest("需要 --e2e 显式开启（会经真实代理发请求）")
        from campus_net_fix import verify
        env = _live_env()
        if not env:
            self.skipTest("无机器档案")
        res = verify.run(env)
        self.assertTrue(res.get("checks"), res)
        print("\n" + verify.summarize(res))

    def test_verify_simulate(self):
        """自主验证：不经用户 Clash，直接跑修复后的配置。"""
        if "--e2e" not in sys.argv:
            self.skipTest("需要 --e2e 显式开启（会启动临时 mihomo 并请求外网）")
        from campus_net_fix import profiling, verify
        env = _live_env()
        if not env:
            self.skipTest("无机器档案")
        prof = profiling.load_profile(env.get("host"))
        if not prof:
            self.skipTest("无网络画像")
        res = verify.simulate(env, prof)
        print("\n" + verify.summarize(res))
        self.assertTrue(res.get("ok"), res)

    def test_verify_modes_are_distinguishable(self):
        """两种验证模式的输出必须能区分，避免把旧配置的结果误当修复成功。"""
        from campus_net_fix import verify
        fake = {"ok": True, "passed": 1, "total": 1, "mode": "simulate",
                "subscription": "X", "exit_node": "N", "cf_ips_used": 3,
                "dead_removed": 2, "checks": [
                    {"name": "t", "desc": "d", "url": "u", "status": 204,
                     "bytes": 0, "ok": True}]}
        text = verify.summarize(fake)
        self.assertIn("模拟模式", text)
        self.assertIn("不经用户 Clash", text)


if __name__ == "__main__":
    # 容许 -k 过滤与 --e2e 透传
    argv = [a for a in sys.argv if a not in ("-k", "--e2e")]
    kw = None
    if "-k" in sys.argv:
        i = sys.argv.index("-k")
        if i + 1 < len(sys.argv):
            kw = sys.argv[i + 1]
            argv = [a for a in argv if a != kw]
    unittest.main(argv=argv, verbosity=2)
