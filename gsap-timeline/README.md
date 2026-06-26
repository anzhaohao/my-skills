# 用途

GSAP Timeline 是 GreenSock 官方的时间线 skill，用来指导 AI 编排多段动画、控制动画顺序、标签、嵌套和播放状态。

# 什么时候触发

当你要求一组动画按顺序播放、复杂入场动画、页面转场、动画编排、动画暂停/反向/重播，或提到 timeline 时，应触发。

# 关键规则

- 复杂序列优先使用 `gsap.timeline()`，不要堆大量 `delay`。
- 用 position parameter 和 label 控制精确节奏。
- 共享默认参数可放在 timeline 的 `defaults` 中。

# 维护记录

2026-06-09：从 GreenSock 官方 `greensock/gsap-skills` 安装。
