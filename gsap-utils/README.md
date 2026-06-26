# 用途

GSAP Utils 是 GreenSock 官方的工具函数 skill，覆盖 `clamp`、`mapRange`、`normalize`、`interpolate`、`random`、`snap`、`toArray`、`wrap`、`pipe` 等辅助方法。

# 什么时候触发

当你要求把滚动、鼠标、进度或数值范围映射到动画参数，或者提到 `gsap.utils`、clamp、random、snap、wrap、toArray 时，应触发。

# 关键规则

- 优先使用 `gsap.utils` 处理动画相关数值映射，减少手写重复工具函数。
- `toArray` 适合统一处理 NodeList、selector 和数组。
- `mapRange`、`clamp`、`snap` 适合交互和滚动进度计算。

# 维护记录

2026-06-09：从 GreenSock 官方 `greensock/gsap-skills` 安装。
