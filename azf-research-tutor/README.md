# 科研学习教练

这个 Skill 用来把 Codex 正在做的科研工作一步一步讲给安钊锋听。它默认不预设光学、仿真、代码、数学或实验设计基础，但不会降低内容深度。

# 什么时候会触发

- “从零教我”“把我当门外汉”；
- “解释你刚才做了什么”；
- “这个公式、代码、仿真结果是什么意思”；
- “我好像懂了，检查一下”；
- “给我一个学习路线”；
- 进行论文、代码、仿真、数据、DOE 或实验工作时，需要边做边讲。

# 它怎么教

默认顺序是：

```text
一句话结论
→ 为什么要做
→ 在项目中的位置
→ 输入、过程、输出
→ 当前项目中的真实例子
→ 专业词和公式
→ 能说明什么、不能说明什么
→ 下一小步
```

专门学习时一次只讲一个关键问题，并用复述、预测或相近小题检查理解。任务优先时会先把工作完成，再在关键节点补讲解，不会强迫把每项科研工作变成考试。

# 主要文件

- `SKILL.md`：触发条件、核心规则和总流程；
- `references/teaching-modes.md`：边做边学、从零讲解、快速说明、理解检查和学习路线；
- `references/research-explanations.md`：公式、论文、代码、仿真、结果图和实验的讲法；
- `references/learning-state.md`：可见的科研学习状态卡；
- `references/quality-rubric.md`：教学质量和常见失败检查；
- `references/pedagogy.md`：LearnLM、Universal Diagnostic Tutor、Bloom 和 Sigma 等设计依据。

# 使用示例

```text
使用 $azf-research-tutor，从零解释 PLKM v0.1 为什么只能看趋势。

使用 $azf-research-tutor，边修改代码边告诉我每一步为什么做。

使用 $azf-research-tutor，让我用自己的话复述有效光谱带宽并检查漏洞。
```

# 重要边界

- 仿真不能写成实验结果；
- 测试通过不能直接证明物理模型正确；
- 不保存隐藏学习分数；
- 未经明确要求不修改 Obsidian；
- 教学层不替代论文检索、实验设计、统计或编程 Skill。

# 最近维护

- 2026-07-23：建立 v0.1。参考 Universal Diagnostic Tutor、Bloom、Sigma 和 Google LearnLM，确定“Skill 先行、Agent 后置”的方案，并加入安钊锋偏好的零基础、一步一步、真人工作记录式讲解。
