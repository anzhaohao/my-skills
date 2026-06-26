# 用途

GSAP ScrollTrigger 是 GreenSock 官方的滚动动画 skill，用来指导 AI 正确实现滚动触发、scrub、pin、视差和滚动联动动画。

# 什么时候触发

当你要求滚动动画、页面滚动触发、固定段落、视差、长页面叙事动画，或明确提到 ScrollTrigger、pin、scrub 时，应触发。

# 关键规则

- 使用前注册 `ScrollTrigger` 插件。
- DOM 或布局变化后根据需要调用 `ScrollTrigger.refresh()`。
- 在组件化框架中必须清理 ScrollTrigger，避免重复绑定。

# 维护记录

2026-06-09：从 GreenSock 官方 `greensock/gsap-skills` 安装。
