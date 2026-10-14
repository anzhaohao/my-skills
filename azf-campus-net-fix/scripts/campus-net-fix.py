#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""azf-campus-net-fix CLI 入口。

用法：
    python campus-net-fix.py doctor
    python campus-net-fix.py probe [--install-dir P] [--data-dir P]
    python campus-net-fix.py profile
    python campus-net-fix.py apply [--dry-run]
    python campus-net-fix.py verify
    python campus-net-fix.py run
    python campus-net-fix.py env [key]

退出码：0 成功 / 3 需重新探测 / 4 画像不支持 / 5 依赖缺失
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from campus_net_fix.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
