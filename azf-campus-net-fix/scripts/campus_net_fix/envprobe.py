# -*- coding: utf-8 -*-
"""环境探测（probe）与漂移体检（doctor）。

机器档案落在技能目录内：data/env.<hostname>.json（按主机名分文件，多机并存不冲突）。

原则（见计划）：每项探测都附带一条**可执行验证**；验证不过就当没探到。
"""
from __future__ import annotations

import json
import os
import platform
import sys

from . import clashverge as cv
from . import yamlcompat as yc
from .util import hostname, iso_now

SCHEMA_VERSION = 1

# 技能根目录（scripts/ 的上一级）
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(SKILL_ROOT, "data")


def env_path(host: str = None) -> str:
    return os.path.join(DATA_DIR, "env.%s.json" % (host or hostname()))


def load_env(host: str = None):
    p = env_path(host)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def save_env(env: dict) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    p = env_path(env.get("host"))
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(env, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return p


def _runtime_info():
    return {
        "python_exe": sys.executable,
        "python_version": platform.python_version(),
        "yaml_source": yc.SOURCE,
        "yaml_version": yc.version(),
        "yaml_libyaml": yc.has_libyaml(),
    }


def probe(install_dir: str = None, data_dir: str = None) -> dict:
    """执行一次完整环境探测。任何一项验证失败都会抛异常，不会写出半成品档案。"""
    env = {
        "schema_version": SCHEMA_VERSION,
        "host": hostname(),
        "probed_at": iso_now(),
        "os": {"family": platform.system().lower(),
               "release": platform.release(),
               "version": platform.version(),
               "machine": platform.machine()},
    }

    # --- 安装目录（验证：存在 clash-verge.exe / clash-verge）---
    idir, imethod = cv.find_install_dir(install_dir)
    gui_exe = next((os.path.join(idir, n) for n in cv.GUI_EXE_CANDIDATES
                    if os.path.isfile(os.path.join(idir, n))), None)
    if not gui_exe:
        raise FileNotFoundError("安装目录里找不到 Clash Verge 可执行文件：%s" % idir)

    # --- 数据目录（验证：profile 目录或 verge.yaml 存在）---
    ddir, app_id, variant = cv.find_data_dir(data_dir)

    # --- 客户端版本（验证：能读到具体版本号；读不到就标 unknown，不猜）---
    ver = cv.client_version_from_logs(ddir)
    ver_src = "log"
    if not ver:
        ver = cv.exe_file_version(gui_exe)
        ver_src = "pe-resource"
    if ver and ver.endswith(".0") and ver_src == "pe-resource":
        ver = ".".join(ver.split(".")[:3])

    verge = cv.read_verge_yaml(ddir)

    # --- 能力探测（能力判定，非版本映射）---
    cap = cv.capabilities(ddir)

    # --- 内核（验证：真的能跑 -v 拿到版本）---
    core = cv.core_info(ddir, idir, verge)
    if not core.get("version"):
        raise RuntimeError("内核无法执行 `-v`，请检查：%s" % core["exe"])

    # --- 订阅（验证：每个订阅文件真的能被 YAML 解析）---
    subs = []
    for s in cv.list_subscriptions(ddir):
        loaded = cv.read_subscription(s["path"])
        subs.append({
            "uid": s["uid"], "name": s["name"], "file": s["file"],
            "path": s["path"], "exists": s["exists"],
            "nodes": len(loaded["proxies"]) if loaded else 0,
            "parsed": loaded is not None,
        })
    if not subs:
        raise RuntimeError("没找到任何订阅。请先在 Clash Verge 里添加并更新订阅。")

    env["client"] = {
        "variant": variant,
        "app_id": app_id,
        "install_dir": idir, "install_dir_method": imethod,
        "data_dir": ddir, "data_dir_method": "explicit" if data_dir else "convention",
        "gui_exe": gui_exe,
        "version": ver or "unknown", "version_source": ver_src if ver else None,
        "profiles_yaml": cap["profiles_yaml"],
        "global_script": cap["global_script"],
        "global_merge": cap["global_merge"],
        "supports_global_script": cap["supports_global_script"],
        "capability_basis": cap["probe_basis"],
        "tun_enabled": bool(verge.get("enable_tun_mode")),
        "system_proxy_enabled": bool(verge.get("enable_system_proxy")),
        "overrides": {"install_dir": install_dir, "data_dir": data_dir},
    }
    env["core"] = core
    env["runtime"] = _runtime_info()
    env["subscriptions"] = subs
    env["verified"] = {
        "gui_exe_exists": os.path.isfile(gui_exe),
        "core_runs": bool(core.get("version")),
        "profiles_parsed": all(s["parsed"] for s in subs),
        "subscription_count": len(subs),
    }
    return env


def doctor(env: dict = None, host: str = None):
    """廉价漂移体检。返回 (ok: bool, issues: [str], env)。"""
    env = env or load_env(host)
    if not env:
        return False, ["机器档案不存在，需要先运行 `probe`"], None

    issues = []
    c = env.get("client") or {}
    core = env.get("core") or {}

    if env.get("schema_version") != SCHEMA_VERSION:
        issues.append("机器档案 schema 版本不符（%s != %s）"
                      % (env.get("schema_version"), SCHEMA_VERSION))

    if not os.path.isfile(c.get("gui_exe") or ""):
        issues.append("Clash Verge 可执行文件不存在或已移动：%s" % c.get("gui_exe"))

    ddir = c.get("data_dir") or ""
    if not (os.path.isdir(os.path.join(ddir, "profiles"))
            or os.path.isfile(os.path.join(ddir, "verge.yaml"))):
        issues.append("数据目录失效：%s" % ddir)

    if not os.path.isfile(core.get("exe") or ""):
        issues.append("内核不存在：%s" % core.get("exe"))
    else:
        now = cv.core_version(core["exe"])
        if now and core.get("version") and now != core["version"]:
            issues.append("内核版本已变化：%s → %s（需要重新探测与画像）"
                          % (core["version"], now))

    ver_now = cv.client_version_from_logs(ddir) if os.path.isdir(ddir) else None
    if ver_now and c.get("version") not in (None, "unknown") and ver_now != c["version"]:
        issues.append("Clash Verge 版本已变化：%s → %s" % (c["version"], ver_now))

    if c.get("supports_global_script"):
        gs = c.get("global_script")
        if gs and not os.path.isfile(gs):
            issues.append("全局扩展脚本路径失效：%s" % gs)

    for s in (env.get("subscriptions") or []):
        if not os.path.isfile(s.get("path") or ""):
            issues.append("订阅文件缺失：%s（%s）" % (s.get("name"), s.get("path")))

    rt = env.get("runtime") or {}
    if not os.path.isfile(rt.get("python_exe") or ""):
        # Python 换了不算致命，但需要刷新档案
        issues.append("Python 解释器路径已变化：%s" % rt.get("python_exe"))

    return (not issues), issues, env


def refresh_runtime(env: dict) -> dict:
    """只刷新与运行时/订阅有关的字段，避免整份档案重探。"""
    env["runtime"] = _runtime_info()
    env["probed_at"] = iso_now()
    subs = []
    for s in cv.list_subscriptions(env["client"]["data_dir"]):
        loaded = cv.read_subscription(s["path"])
        subs.append({"uid": s["uid"], "name": s["name"], "file": s["file"],
                     "path": s["path"], "exists": s["exists"],
                     "nodes": len(loaded["proxies"]) if loaded else 0,
                     "parsed": loaded is not None})
    env["subscriptions"] = subs
    return env
