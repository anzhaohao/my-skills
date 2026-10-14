# -*- coding: utf-8 -*-
"""PyYAML 兼容层：优先用系统安装的 PyYAML，缺失时回退到 scripts/vendor 里的副本。

为什么必须 vendor：换电脑后可能没有 PyYAML，而工具不应联网安装依赖。
为什么不能绕开 YAML：Clash Verge 生成的配置有 block-style 与 flow-style 两种写法，
正则解析会在 flow-style 上漏节点（今日实测漏掉 45 个）。
"""
from __future__ import annotations

import io
import os
import sys

_VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor")

SOURCE = None       # "system" | "vendored"

try:                                                    # 优先系统安装
    import yaml as _yaml
    SOURCE = "system"
except ImportError:                                     # 回退 vendored
    if _VENDOR not in sys.path:
        sys.path.insert(0, _VENDOR)
    import yaml as _yaml
    SOURCE = "vendored"


def version() -> str:
    return getattr(_yaml, "__version__", "unknown")


def has_libyaml() -> bool:
    return bool(getattr(_yaml, "__with_libyaml__", False))


def load_text(text: str):
    return _yaml.safe_load(text)


def load_file(path: str):
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        return _yaml.safe_load(fh)


def dump(obj, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        _yaml.safe_dump(obj, fh, allow_unicode=True, sort_keys=False, width=4096)


def dump_text(obj) -> str:
    return _yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=4096)
