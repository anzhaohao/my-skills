---
name: azf-deep-learning-experiment-record
description: An Zhaofeng's evidence-analysis workflow for deep-learning runs. Use when Codex needs to inspect configs, manifests, train logs, metrics, figures, predictions, checkpoints, or baselines and turn them into a reliable experiment summary. Use with azf-obsidian-project-record when the result belongs in the Obsidian project vault.
---

# Deep Learning Experiment Evidence

## Role Boundary

This skill owns evidence reading and experiment interpretation. It does not own the Obsidian project folder, total note, mainline note, debug-record placement, or template body.

- `azf-obsidian-project-record` decides the project folder, note role, classification, and whether project indexes/mainlines should be synchronized.
- The active Vault Templater template creates the note structure and frontmatter.
- This skill reads the external run artifacts and fills the generated experiment note with source-grounded facts.
- Filling an experiment note does not automatically update the total note or mainline. Synchronize those only when An Zhaofeng explicitly asks.

## Storage Boundary

Keep large and reproducibility-critical outputs outside the Obsidian Vault, normally under an external project root:

```text
D:\Postgraduate_JilinUniversity\02_Project\<project-name>\
  experiments\
    <run-id>\
      manifest.md
      config\
      logs\
      figures\
      predictions\
      checkpoints\
      environment\
```

The Vault note records the experiment's understanding and links to the external files with `file:///D:/...` links. Do not copy checkpoints, raw logs, or bulky prediction files into the Vault merely to make the note complete.

Every run should have stable Chinese properties `实验编号` and `实验归档路径`. The minimum `manifest.md` should state the purpose, actual command, Git commit, dataset/version/split, configuration entry point, environment, and artifact directory.

## Workflow

1. Resolve the run and its external `实验归档路径`. If the path is missing or ambiguous, ask; do not invent a run directory.
2. If the result belongs to `01-Project`, use `azf-obsidian-project-record` to resolve the target experiment/debug role and invoke the current Vault template. The default template root is `E:\software\Obsidian\安钊锋的外置大脑\05-Junk Drawer\2_模板`; if no matching role is found there, let the project skill inspect the active Templater configuration.
3. Read evidence in this order when present: `manifest.md`, configuration, dataset summary, training logs, metrics, figures/predictions, checkpoints, environment record, and a user-specified baseline.
4. Fill only the generated note structure. Preserve existing user-written content and mark missing artifacts explicitly.
5. Reread the finished note and verify every reported number, external link, figure reference, and conclusion against the source files.
6. If An Zhaofeng explicitly requests project synchronization, pass the run conclusion and relevant links to `azf-obsidian-project-record`; otherwise leave total/mainline notes unchanged.

## Evidence Reading Rules

For each artifact, use:

```text
用途：这个文件或图用来判断什么
关键结果：读到的具体数值或现象
判断：这个结果支持什么，不能支持什么，还缺什么证据
```

Use cautious conclusions:

- `train_loss`下降只说明模型在拟合训练数据。
- `val_loss`同步下降才支持验证集上的泛化暂时正常。
- train/validation 差距扩大支持“可能过拟合”，不能只凭一张图确认。
- 一张预测图只能说明一个样本或一个局部现象，不能代表整体泛化。
- 测试指标只能在数据划分、模型、损失、预处理和评价协议可比时比较。

Only state numbers read from files or command output. Label derived values and assumptions as inference. If a file is absent, write `未生成` or `未找到` and do not silently substitute a screenshot or an old value.

## Comparison Gate

Before comparing two runs, verify:

- same dataset version and split;
- same preprocessing and label definition;
- same model family and loss;
- same evaluation protocol;
- which variable actually changed.

If more than one major setting changed, state that attribution is uncertain. If the baseline is ambiguous, ask which run to compare instead of choosing silently. For several runs, keep a separate comparison overview only when requested; do not turn every single-run note into a leaderboard.

## Obsidian Link Format

Use forward-slash local links and angle brackets:

```markdown
- 实验归档：[run-001](<file:///D:/Postgraduate_JilinUniversity/02_Project/project/experiments/run-001/>)
- 归档说明：[manifest.md](<file:///D:/Postgraduate_JilinUniversity/02_Project/project/experiments/run-001/manifest.md>)
- 训练日志：[train_log.csv](<file:///D:/Postgraduate_JilinUniversity/02_Project/project/experiments/run-001/logs/train_log.csv>)
- Loss 曲线：[loss_curve.png](<file:///D:/Postgraduate_JilinUniversity/02_Project/project/experiments/run-001/figures/loss_curve.png>)
```

Use the Vault's active Templater-generated experiment structure rather than copying a historical note body. The template may provide sections such as experiment setup, overview, logs/metrics, visualizations, model files, comparison, problems/next step, and one-line summary; this skill supplies the evidence for those sections.

## Closeout

Report:

- external `实验归档路径` and `实验编号`;
- target Vault note, if one was created or updated;
- artifacts read and artifacts missing;
- key evidence-grounded conclusion;
- whether project total/mainline synchronization was performed or intentionally left pending.
