# Council of High Intelligence Skill

这个 skill 用来在 Codex 中触发 `/council` 多视角评审。它会把一个复杂问题交给多个不同思考风格的 persona，例如 Socrates、Feynman、Torvalds、Kahneman、Ada 等，进行结构化讨论、反驳和综合结论。

# 什么时候触发

- 用户输入 `/council ...`
- 用户想做需求预审、架构取舍、方案对比、风险评估
- 用户希望在进入 Spec Kit 前先把问题想清楚
- 用户提到 council deliberation、triad、duo、多视角决策分析

# 常用写法

```text
/council --quick 我准备做 xxx 功能，请从产品价值、技术风险、实现顺序上帮我评审。
/council --triad architecture A 方案和 B 方案应该选哪个？
/council --triad product 这个功能是否值得先做 MVP？
/council --triad risk 这个实现方案最大的失败条件是什么？
/council --duo 应该先做最小闭环，还是直接做完整架构？
```

# 和 Spec Kit 的关系

Council 不替代 Spec Kit。推荐定位是：

```text
Council 前置评审 -> Speckit Specify -> Speckit Plan -> Speckit Tasks -> Speckit Analyze -> Speckit Implement
```

Council 负责发现问题定义、风险、取舍和失败条件；Spec Kit 负责把结论落成 `spec.md`、`plan.md`、`tasks.md` 等可追踪产物。

# 当前安装位置

- Codex 生效目录：`C:\Users\anzhaofeng\.codex\skills\council`
- 统一管理目录：`C:\Users\anzhaofeng\.skills-manager\skills\council`

目录内包含：

- `SKILL.md`
- `agents/council-*.md`，共 18 个 persona
- `scripts/*.sh`
- `configs/*.yaml`

# 最近维护

- 2026-07-03：从 `0xNyk/council-of-high-intelligence` 安装 Codex 版 skill，并同步到 Skills Manager 统一目录；补充本 README，明确它作为 Spec Kit 工作流的前置评审工具。
