# 用途

GSAP Performance 是 GreenSock 官方的动画性能 skill，用来指导 AI 写更流畅、更少卡顿的 GSAP 动画。

# 什么时候触发

当你要求优化动画性能、减少卡顿、提升 FPS、处理滚动动画抖动，或需要评估动画是否会导致布局重排时，应触发。

# 关键规则

- 优先动画 `transform` 和 `opacity`，避免频繁动画 `top`、`left`、`width`、`height`。
- 小心 `will-change`，只在需要时使用。
- 大量元素动画要考虑批处理、错峰和 ScrollTrigger 性能策略。

# 维护记录

2026-06-09：从 GreenSock 官方 `greensock/gsap-skills` 安装。
