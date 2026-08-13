# 教学依据与参考

本 Skill 采用以下通用原则：主动学习、控制认知负荷、根据学习者调整、激发好奇、促进元认知、掌握后再推进。它们是设计依据，不是对学习效果的保证。

## 主要参考

- [Google LearnLM Partner Prompt Guide](https://services.google.com/fh/files/misc/learnlm_prompt_guide.pdf)：主动学习、认知负荷、自适应、好奇心和元认知；建议一次一步、用提示而不是过早给答案。
- [LearnLM: Improving Gemini for Learning](https://arxiv.org/abs/2412.16429)：通过教学指令控制教学行为，并以教学质量量表评估。
- [Universal Diagnostic Tutor](https://github.com/SenmuuuuW/universal-diagnostic-tutor-skill)（MIT）：诊断优先、最小教学动作、掌握证据、可见状态卡。
- [Bloom](https://github.com/Li-Evan/Bloom)（MIT）：逐篇学习、反馈驱动、费曼检查和文件化学习过程。
- [Sigma Tutor](https://github.com/sanyuan0704/sanyuan-skills/tree/main/skills/sigma)（MIT）：错误认识记录、交错练习、间隔复习和可视化路线。
- [Mr. Ranedeer AI Tutor](https://github.com/JushBJJ/Mr.-Ranedeer-AI-Tutor)：教学深度和表达方式可配置。仓库未检测到明确许可证，因此仅参考公开思想，不复制内容。

## 本地化决定

- 不采用“永远不给答案”的硬规则，因为科研实施常常需要任务优先。
- 不默认生成完整课程或网页，先服务当前科研项目。
- 不建立第二套隐藏记忆，优先复用用户可见的 Obsidian 项目记录和已有 agent-memory 边界。
- 不用虚构百分数表示掌握度，采用复述、解释、预测、边界判断和近迁移证据。
- 不让教学层替代论文检索、实验设计、统计、优化或代码验证等专业 Skill。
