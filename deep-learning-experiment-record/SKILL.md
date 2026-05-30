---
name: deep-learning-experiment-record
description: Fill or update deep-learning experiment records in Markdown or Obsidian from archived experiment artifacts such as configs, manifests, train logs, metrics JSON, figures, predictions, checkpoints, and prior baseline notes. Use when the user asks to 整理实验记录, 填入实验记录, update an Obsidian experiment note, summarize a training run, compare deep-learning experiments, or convert training outputs into a beginner-friendly research log across any project or agent environment.
---

# Deep Learning Experiment Record

## Core Rule

Always resolve the target note before filling it.

- If the user gives an explicit document path, verify it exists or can be created, state the exact target path in the working update, and proceed without asking again.
- Ask again only when the target path is ambiguous, unsafe, unwritable, or conflicts with multiple existing notes.
- If no target path is given, ask for the target Markdown/Obsidian file and stop.
- If multiple likely notes exist, ask which one to fill and stop.
- If the target already contains a template, preserve its structure unless the user asks for a rewrite.

## Workflow

1. Resolve or confirm target note.
2. Read the target note or template.
3. Locate experiment evidence:
   - `manifest.md`
   - config file such as `.yaml`, `.json`, or `.toml`
   - training log such as `train_log.csv`
   - metrics such as `test_metrics.json`
   - figures such as `loss_curve.png`, prediction plots, confusion matrices, residual plots
   - checkpoints such as `best.pt`, `last.pt`, `.ckpt`, `.pth`
   - previous experiment note or metrics only when the user specifies it, the target note names it, or exactly one clearly matching baseline can be identified from project progress or manifests
4. Fill the note with evidence-grounded content.
5. Reread the written note and verify key metrics, figure links, and next-step text are present.

## Beginner-Friendly Writing Style

Write for a beginner who is learning how to judge a deep-learning experiment.

For each artifact, use this pattern:

```text
用途: 这个文件/图用来判断什么
关键结果: 读到的具体数值或现象
判断: 这个结果说明什么，是否可信，还有什么不能说明
```

Prefer plain explanations:

- `train_loss` falls: the model is fitting the training data.
- `val_loss` also falls: learning likely generalizes to validation data.
- train and val are close: no obvious overfitting yet.
- test metrics improve: compare only when data split and config are comparable.
- one prediction figure is only one case; do not treat it as full generalization.

Avoid overclaiming. Use cautious phrases such as “暂未看到明显过拟合”, “单样本图支持这个判断”, and “仍需多样本检查”.

## Standard Note Structure

If the target note is empty or only a generic template, fill or create these sections:

```markdown
# 1. 实验设置与归档入口
# 2. 实验概览
# 3. 实验结果
## 3.1 日志与指标文件
## 3.2 可视化文件
## 3.3 模型文件
# 4. 与上一次实验对比
# 5. 问题与下一步
# 6. 一句话总结
```

Preserve existing frontmatter. Update `修改时间` if present. Do not delete user-written notes unless replacing obvious placeholders.

## Obsidian Formatting Rules

Use robust Markdown that renders in Obsidian and in plain Markdown.

For archive entry blocks, do not rely on tab indentation or naked indented lines. Use bullets:

Do not convert this block into a table unless the user explicitly asks for a table. Prefer the original note-like layout with top-level bullets and short nested bullets.

```markdown
- 本地归档文件夹：`experiments/EXPERIMENT_ID/`
- 完整路径：`D:\path\to\experiments\EXPERIMENT_ID\`
- 打开归档：[EXPERIMENT_ID](<file:///D:/path/to/experiments/EXPERIMENT_ID/>)
- 归档说明文件：[manifest.md](<file:///D:/path/to/experiments/EXPERIMENT_ID/manifest.md>)
- 实验配置：[config.yaml](<file:///D:/path/to/experiments/EXPERIMENT_ID/config/config.yaml>)
```

Use `file:///` links with forward slashes for local file links. Wrap the URL in angle brackets when paths contain spaces or non-ASCII characters.

Embed images with Obsidian-compatible Markdown:

```markdown
![loss_curve.png](<file:///D:/path/to/loss_curve.png>)
```

Use tables for metric comparisons:

```markdown
| 指标 | baseline | current | 判断 |
|---|---:|---:|---|
| test_loss | 0.0741 | 0.0562 | 下降，变好 |
```

## Evidence Rules

Only state numbers that were read from files or command output. If a value is inferred, label it as an inference.

When comparing experiments:

- Check whether the same dataset split, model, loss, and preprocessing were used.
- Compare with a previous experiment only when the user specifies it, the target note names it, or exactly one clearly matching baseline can be identified from project progress or manifests.
- If comparison seems useful but the baseline is ambiguous, ask the user which baseline to use instead of choosing silently.
- If only one variable changed, explicitly name it.
- If settings differ in multiple ways, warn that attribution is uncertain.

When the run was not archived automatically:

- Explain that `outputs/` is temporary and `experiments/<id>/` is the formal archive.
- Record any补归档/after-the-fact archive step clearly.

## Cross-Agent Portability

Keep instructions independent of Codex-specific tooling. Any capable agent, including Claude Code, can follow this skill using normal filesystem access.

- Prefer reading local files directly.
- Prefer structured files over screenshots when available.
- Do not require a specific shell, Python environment, or IDE.
- Do not assume a Git repository exists.
- If editing a live user note, preserve existing content and fill placeholders surgically.

## Final Response

After filling the note, report:

- target note path
- key sections filled
- any missing artifacts
- one recommended next step

Keep the final response short.
