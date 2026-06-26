# 用途

GSAP Plugins 是 GreenSock 官方的插件 skill，覆盖 ScrollToPlugin、ScrollSmoother、Flip、Draggable、Inertia、Observer、SplitText、ScrambleText、SVG、物理和缓动插件等。

# 什么时候触发

当你要求使用 GSAP 插件、做 FLIP 动画、拖拽、滚动平滑、文字拆分、SVG 绘制、复杂缓动或插件注册时，应触发。

# 关键规则

- 使用插件前通常要 `gsap.registerPlugin(...)`。
- 按需求选择官方插件，不要手写复杂且脆弱的替代逻辑。
- 当前 GSAP 官方插件已随公开 `gsap` npm 包可用，不需要私有 npm token。

# 维护记录

2026-06-09：从 GreenSock 官方 `greensock/gsap-skills` 安装。
