# -*- coding: utf-8 -*-
"""azf-campus-net-fix 确定性内核。

分层（见 SKILL.md）：
  L0  例行维护 —— profile → apply → verify，0 AI 成本
  L1  画像不支持当前网络时 —— 输出证据，交由 AI 诊断
  L2  内核需要修改时 —— 交由 azf-auto-dev-loop
"""

__version__ = "1.0.0"
