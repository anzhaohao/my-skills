# 用途

GSAP React 是 GreenSock 官方的 React/Next.js 集成 skill，用来指导 AI 在 React 组件中正确使用 `useGSAP`、refs、`gsap.context()` 和清理逻辑。

# 什么时候触发

当你要求在 React、Next.js 或 React 组件里写动画，或者提到 `useGSAP`、组件卸载清理、SSR、refs 时，应触发。

# 关键规则

- 优先使用 `@gsap/react` 的 `useGSAP`。
- 动画应绑定到组件作用域，避免全局选择器误伤。
- 组件卸载时必须清理动画和 ScrollTrigger。

# 维护记录

2026-06-09：从 GreenSock 官方 `greensock/gsap-skills` 安装。
