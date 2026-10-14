# -*- coding: utf-8 -*-
"""Clash Verge 适配层。

设计原则（见计划）：**全部确定性探测，不靠 AI 发挥**；每一项探测都必须附带
一条可执行验证，验证不过就当没探到 —— 防止幻觉路径变成坏配置。

实测依据（2026-10-14，Clash Verge Rev 2.5.8）：
  · 内核进程由 SYSTEM 服务启动，MainModule 路径**读不出来** → 不能靠它
  · GUI 进程是用户态，路径**可读** → 用它推导安装目录
  · 内核选择可从 verge.yaml 的 `clash_core` 字段直读
  · 全局扩展脚本能力可从 profiles.yaml 的 `uid: Script` 条目判定（能力探测，非版本映射）
  · Rev 与原版产品名都叫 "Clash Verge" → 用**数据目录名**区分
"""
from __future__ import annotations

import glob
import os
import platform
import re
import subprocess
import sys

from . import yamlcompat
from .util import IS_WINDOWS, _CREATE_NO_WINDOW

# Clash Verge 各分支的数据目录名（platformdirs 风格的应用 ID）
APP_IDS = {
    "clash-verge-rev": "io.github.clash-verge-rev.clash-verge-rev",
    "clash-verge": "io.github.clash-verge.clash-verge",
}

GUI_EXE_CANDIDATES = ["clash-verge.exe", "Clash Verge.exe", "clash-verge"]
CORE_EXE_CANDIDATES = ["verge-mihomo.exe", "verge-mihomo-alpha.exe",
                       "mihomo.exe", "clash-meta.exe", "clash.exe"]


# ---------------------------------------------------------------------------
# 进程枚举（纯 ctypes，不调 shell、不需要管理员）
# ---------------------------------------------------------------------------
def list_process_paths():
    """返回 [(pid, exe_path)]。无法读取路径的进程会被跳过（例如 SYSTEM 服务）。"""
    if not IS_WINDOWS:
        return _list_process_paths_posix()
    import ctypes
    from ctypes import wintypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    MAX_PATH = 32768

    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
    except Exception:
        return []

    arr = (wintypes.DWORD * 8192)()
    needed = wintypes.DWORD()
    if not psapi.EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(needed)):
        return []
    count = needed.value // ctypes.sizeof(wintypes.DWORD)

    out = []
    for i in range(count):
        pid = arr[i]
        if not pid:
            continue
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            continue
        try:
            size = wintypes.DWORD(MAX_PATH)
            buf = ctypes.create_unicode_buffer(MAX_PATH)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                if buf.value:
                    out.append((int(pid), buf.value))
        finally:
            kernel32.CloseHandle(handle)
    return out


def _list_process_paths_posix():
    out = []
    for p in glob.glob("/proc/[0-9]*/exe"):
        try:
            out.append((int(p.split("/")[2]), os.readlink(p)))
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# 安装目录
# ---------------------------------------------------------------------------
def _install_dir_from_process():
    for _pid, path in list_process_paths():
        base = os.path.basename(path).lower()
        if base in ("clash-verge.exe", "clash verge.exe", "clash-verge"):
            d = os.path.dirname(path)
            if _has_core(d) or os.path.isfile(os.path.join(d, "clash-verge.exe")):
                return d, "gui-process"
    return None, None


def _has_core(d: str) -> bool:
    return any(os.path.isfile(os.path.join(d, n)) for n in CORE_EXE_CANDIDATES)


def _install_dir_from_fs(max_depth: int = 3):
    """有界文件系统搜索，不遍历整盘。"""
    roots = []
    if IS_WINDOWS:
        roots += [os.environ.get("LOCALAPPDATA", ""),
                  os.environ.get("PROGRAMFILES", ""),
                  os.environ.get("PROGRAMFILES(X86)", ""),
                  os.environ.get("APPDATA", "")]
        for letter in "CDEFGH":
            d = letter + ":\\"
            if os.path.isdir(d):
                roots.append(d)
        for d in ("C:\\Program Files", "C:\\Program Files (x86)"):
            if os.path.isdir(d):
                roots.append(d)
    else:
        roots += [os.path.expanduser("~/Applications"), "/Applications",
                  "/usr/local/bin", "/opt", os.path.expanduser("~")]

    seen = set()
    for root in roots:
        if not root or not os.path.isdir(root) or root in seen:
            continue
        seen.add(root)
        for dirpath, dirnames, filenames in os.walk(root):
            depth = dirpath[len(root):].count(os.sep)
            if depth >= max_depth:
                dirnames[:] = []
                continue
            dirnames[:] = [x for x in dirnames
                           if not x.startswith(".") and x.lower() not in
                           ("windows", "system32", "node_modules", "$recycle.bin")]
            if any(f.lower() in ("clash-verge.exe", "clash-verge") for f in filenames):
                return dirpath, "fs-search"
    return None, None


def find_install_dir(explicit: str = None):
    """返回 (install_dir, method)。method ∈ gui-process|fs-search|explicit。"""
    if explicit:
        explicit = os.path.abspath(explicit)
        if os.path.isdir(explicit) and os.path.isfile(
                os.path.join(explicit, "clash-verge.exe")):
            return explicit, "explicit"
        raise FileNotFoundError("指定的安装目录无效（未找到 clash-verge.exe）：%s" % explicit)

    d, m = _install_dir_from_process()
    if d:
        return d, m
    d, m = _install_dir_from_fs()
    if d:
        return d, m
    raise FileNotFoundError(
        "找不到 Clash Verge 安装目录。请用 --install-dir 显式指定"
        "（目录里应有 clash-verge.exe）。")


# ---------------------------------------------------------------------------
# 数据目录
# ---------------------------------------------------------------------------
def _data_dir_candidates():
    out = []
    if IS_WINDOWS:
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            out += [os.path.join(appdata, v) for v in APP_IDS.values()]
    elif platform.system() == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
        out += [os.path.join(base, v) for v in APP_IDS.values()]
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
        out += [os.path.join(base, v) for v in APP_IDS.values()]
    return out


def find_data_dir(explicit: str = None):
    """返回 (data_dir, app_id, variant)。验证标准：存在 profiles 目录或 verge.yaml。"""
    def _valid(d):
        return os.path.isdir(d) and (
            os.path.isdir(os.path.join(d, "profiles"))
            or os.path.isfile(os.path.join(d, "verge.yaml")))

    if explicit:
        explicit = os.path.abspath(explicit)
        if not _valid(explicit):
            raise FileNotFoundError(
                "指定的数据目录无效（未找到 profiles/ 或 verge.yaml）：%s" % explicit)
        return explicit, os.path.basename(explicit), _variant_of(os.path.basename(explicit))

    for d in _data_dir_candidates():
        if _valid(d):
            return d, os.path.basename(d), _variant_of(os.path.basename(d))
    raise FileNotFoundError(
        "找不到 Clash Verge 数据目录。请先运行一次 Clash Verge，"
        "或用 --data-dir 显式指定（目录里应有 profiles/）。")


def _variant_of(app_id: str) -> str:
    for variant, aid in APP_IDS.items():
        if aid == app_id:
            return variant
    return "unknown"


# ---------------------------------------------------------------------------
# 版本
# ---------------------------------------------------------------------------
_VERSION_RE = re.compile(r"Version:\s*([0-9][0-9A-Za-z.\-+]*)")


def client_version_from_logs(data_dir: str):
    """从 Clash Verge 日志里取版本号（实测可靠，且不需要解析 PE 资源）。

    日志形如：INFO [ClashVergeRev] Version: 2.5.8
    """
    logs = os.path.join(data_dir, "logs")
    if not os.path.isdir(logs):
        return None
    files = sorted(glob.glob(os.path.join(logs, "*.log")),
                   key=lambda p: os.path.getmtime(p), reverse=True)[:12]
    for p in files:
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    m = _VERSION_RE.search(line)
                    if m:
                        return m.group(1)
        except Exception:
            continue
    return None


def exe_file_version(path: str):
    """读取 PE 文件版本号（纯 ctypes，不调 shell）。失败返回 None。"""
    if not IS_WINDOWS or not os.path.isfile(path):
        return None
    try:
        import ctypes
        from ctypes import wintypes

        version = ctypes.WinDLL("version", use_last_error=True)
        size = version.GetFileVersionInfoSizeW(path, None)
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        if not version.GetFileVersionInfoW(path, 0, size, buf):
            return None
        r = ctypes.c_void_p()
        length = wintypes.UINT()
        if not version.VerQueryValueW(buf, "\\", ctypes.byref(r), ctypes.byref(length)):
            return None

        class VS_FIXEDFILEINFO(ctypes.Structure):
            _fields_ = [("dwSignature", wintypes.DWORD),
                        ("dwStrucVersion", wintypes.DWORD),
                        ("dwFileVersionMS", wintypes.DWORD),
                        ("dwFileVersionLS", wintypes.DWORD),
                        ("dwProductVersionMS", wintypes.DWORD),
                        ("dwProductVersionLS", wintypes.DWORD),
                        ("dwFileFlagsMask", wintypes.DWORD),
                        ("dwFileFlags", wintypes.DWORD),
                        ("dwFileOS", wintypes.DWORD),
                        ("dwFileType", wintypes.DWORD),
                        ("dwFileSubtype", wintypes.DWORD),
                        ("dwFileDateMS", wintypes.DWORD),
                        ("dwFileDateLS", wintypes.DWORD)]

        info = ctypes.cast(r, ctypes.POINTER(VS_FIXEDFILEINFO)).contents
        ms, ls = info.dwFileVersionMS, info.dwFileVersionLS
        return "%d.%d.%d.%d" % (ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 内核
# ---------------------------------------------------------------------------
def read_verge_yaml(data_dir: str) -> dict:
    p = os.path.join(data_dir, "verge.yaml")
    if not os.path.isfile(p):
        return {}
    try:
        return yamlcompat.load_file(p) or {}
    except Exception:
        return {}


def core_info(data_dir: str, install_dir: str, verge: dict = None):
    """返回 dict(kind, exe, version, source)。"""
    verge = verge if verge is not None else read_verge_yaml(data_dir)
    kind = verge.get("clash_core") or "verge-mihomo"

    # 候选顺序：verge.yaml 指定 → 安装目录候选 → 数据目录旁的 sidecar
    candidates = []
    if not kind.endswith(".exe"):
        candidates.append(os.path.join(install_dir, kind + ".exe"))
    else:
        candidates.append(os.path.join(install_dir, kind))
    candidates += [os.path.join(install_dir, n) for n in CORE_EXE_CANDIDATES]
    candidates.append(os.path.join(data_dir, kind + ".exe"))

    exe = next((c for c in candidates if os.path.isfile(c)), None)
    if not exe:
        raise FileNotFoundError(
            "找不到 mihomo 内核（依据 verge.yaml 的 clash_core=%s，安装目录 %s）"
            % (kind, install_dir))

    return {"kind": kind, "exe": exe, "version": core_version(exe),
            "source": "verge.yaml:clash_core"}


def core_version(exe: str):
    """真实跑一次 `mihomo -v` 拿版本 —— 不靠文件名猜。"""
    try:
        r = subprocess.run([exe, "-v"], capture_output=True, text=True,
                           timeout=15, encoding="utf-8", errors="replace",
                           creationflags=_CREATE_NO_WINDOW)
        m = re.search(r"\bv?(\d+\.\d+\.\d+)", (r.stdout or "") + (r.stderr or ""))
        return m.group(1) if m else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 扩展脚本能力（能力探测，不是版本映射）
# ---------------------------------------------------------------------------
def capabilities(data_dir: str):
    """探测 Clash Verge 的功能面。

    supports_global_script 的判定依据：profiles.yaml 里存在 `uid: Script` 且
    `type: script` 的条目。这样跨版本不会误判（见计划）。
    """
    profiles_yaml = os.path.join(data_dir, "profiles.yaml")
    out = {
        "profiles_yaml": profiles_yaml if os.path.isfile(profiles_yaml) else None,
        "global_script": None,
        "global_merge": None,
        "supports_global_script": False,
        "probe_basis": None,
    }
    if not out["profiles_yaml"]:
        out["probe_basis"] = "profiles.yaml 不存在"
        return out

    try:
        cfg = yamlcompat.load_file(profiles_yaml) or {}
    except Exception as e:
        out["probe_basis"] = "profiles.yaml 解析失败: %s" % e
        return out

    pdir = os.path.join(data_dir, "profiles")
    for item in (cfg.get("items") or []):
        if not isinstance(item, dict):
            continue
        uid, typ = item.get("uid"), item.get("type")
        if uid == "Script" and typ == "script":
            out["supports_global_script"] = True
            out["global_script"] = os.path.join(pdir, item.get("file") or "Script.js")
            out["probe_basis"] = "profiles.yaml 含 uid:Script(type=script)"
        elif uid == "Merge" and typ == "merge":
            out["global_merge"] = os.path.join(pdir, item.get("file") or "Merge.yaml")
    if not out["probe_basis"]:
        out["probe_basis"] = "profiles.yaml 中未找到 uid:Script 条目"
    return out


# ---------------------------------------------------------------------------
# 订阅
# ---------------------------------------------------------------------------
def list_subscriptions(data_dir: str):
    """返回 [{uid, name, file, path, script, merge, proxies_loadable}]。"""
    profiles_yaml = os.path.join(data_dir, "profiles.yaml")
    if not os.path.isfile(profiles_yaml):
        return []
    try:
        cfg = yamlcompat.load_file(profiles_yaml) or {}
    except Exception:
        return []

    pdir = os.path.join(data_dir, "profiles")
    out = []
    for item in (cfg.get("items") or []):
        if not isinstance(item, dict) or item.get("type") != "remote":
            continue
        fn = item.get("file") or ""
        path = os.path.join(pdir, fn)
        opt = item.get("option") or {}
        out.append({
            "uid": item.get("uid"),
            "name": item.get("name") or fn.replace(".yaml", ""),
            "file": fn,
            "path": path,
            "exists": os.path.isfile(path),
            "script": opt.get("script"),
            "merge": opt.get("merge"),
            "current_selected": item.get("selected") or [],
        })
    return out


def read_subscription(path: str):
    """读取订阅缓存文件，返回 dict(proxies, proxy-groups, raw)。"""
    if not os.path.isfile(path):
        return None
    try:
        cfg = yamlcompat.load_file(path)
    except Exception:
        return None
    if not isinstance(cfg, dict):
        return None
    return {"proxies": cfg.get("proxies") or [],
            "proxy-groups": cfg.get("proxy-groups") or [],
            "raw": cfg}


def read_runtime_config(data_dir: str):
    """读取当前激活订阅的合并运行时配置（Clash Verge 生成）。"""
    p = os.path.join(data_dir, "clash-verge.yaml")
    if not os.path.isfile(p):
        return None
    try:
        cfg = yamlcompat.load_file(p)
    except Exception:
        return None
    return cfg if isinstance(cfg, dict) else None


def current_profile_uid(data_dir: str):
    profiles_yaml = os.path.join(data_dir, "profiles.yaml")
    if not os.path.isfile(profiles_yaml):
        return None
    try:
        return (yamlcompat.load_file(profiles_yaml) or {}).get("current")
    except Exception:
        return None
