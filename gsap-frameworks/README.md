# 用途

GSAP Frameworks 是 GreenSock 官方的非 React 框架集成 skill，主要指导 Vue、Nuxt、Svelte、SvelteKit 等项目中如何安全使用 GSAP。

# 什么时候触发

当你要求在 Vue、Nuxt、Svelte、SvelteKit 或其他非 React 前端框架里实现动画，或者提到生命周期、组件卸载、选择器作用域时，应触发。

# 关键规则

- 在组件生命周期内创建动画，并在卸载时清理。
- 选择器应尽量限制在组件作用域内，避免影响页面其他区域。
- React 项目应改用 `gsap-react`。

# 维护记录

2026-06-09：从 GreenSock 官方 `greensock/gsap-skills` 安装。
