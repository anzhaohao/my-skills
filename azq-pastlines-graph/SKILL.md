---
name: azq-pastlines-graph
description: 从章节、文章或笔记生成可打开的基础 Pastlines 图谱。用于制作 .pastlines 项目、章节结构图、因果链、概念图，或校验和布局已有图谱；输出 schema 合规文件、可审阅的 plan 和证据/质量报告，不编造无出处内容。
---

# Pastlines 基础图谱

把一份有边界的资料整理成 Pastlines 能直接打开的基础图谱。先产出可审阅的 plan，再由脚本生成 `.pastlines`；模型只做语义抽取，格式、布局和检查交给脚本。

## 使用场景

- 用户给定一章、一节、一篇文章或一份笔记，要求做 Pastlines 图谱、章节结构图或因果链。
- 用户已有节点和关系清单，要求生成可打开的 `.pastlines`。
- 用户要求检查已有 `.pastlines` 的节点、关系、孤立点或来源覆盖。

不用于修改 Pastlines 应用代码、打包 exe 或做视觉回归；这些走 `pastlines` 发布技能。

## 输入

必填：

- 源文件路径，或已提取的正文；PDF 先转成可检索文本。
- 图谱标题。
- 范围边界，例如“第 6 课《全球航路的开辟》子目《新航路的开辟》”。

默认值：

- 12–24 个节点；超过 40 个先拆章节或子图。
- 关系先标 `pending`，只有证据明确时才改成 `causal`、`temporal`、`comparison` 或 `membership`。
- 输出 `<标题>.pastlines` 和 `<标题>.plan.json`；默认不嵌入图片。

如果用户没有给粒度，按“一个可以独立解释的历史对象、事件或概念 = 一个节点”处理。不要把一句长段落机械拆成很多节点，也不要把整章压成一个节点。

## 硬规则

- 每个节点必须有 `source`：文件、页码或段落定位，加一小段原文或准确转述；无出处不建节点。
- 每条边必须在 plan 里写 `evidence`；`.pastlines` 的边没有来源字段，证据留在 plan 中。
- 不编造人物、时间、地点、因果和数字。不确定就保留 `pending`，在 `label` 中写“可能”“待证”或具体疑点。
- 节点名要短；解释放在 `description`，一般 1–3 句。
- 节点和关系 ID 只用 ASCII：`[A-Za-z0-9_.-]+`；建议 `n01` 或 `person-columbus`。
- 关系类型闭集：`pending`、`causal`、`temporal`、`comparison`、`membership`。
- 方向固定：`causal` 从因到果，`temporal` 从早到晚，`membership` 从部分到整体。
- 默认 `imageIds: []`，不把网络图片、SVG 或未经处理的资源塞进项目。
- 不覆盖用户已有的 `.pastlines`；输出到新文件，除非用户明确要求另存覆盖。

## Plan 格式

中间文件是可读 JSON，不是最终项目格式：

```json
{
  "title": "新航路的开辟",
  "nodes": [
    {
      "id": "n01",
      "name": "阿拉伯商人",
      "type": "群体",
      "time": "",
      "description": "控制东地中海商路，是西欧人另寻航线的背景。",
      "source": "教材第35页；原文「自从阿拉伯商人控制东地中海商路后……」"
    },
    {
      "id": "n02",
      "name": "西欧人",
      "type": "群体",
      "time": "",
      "description": "寻找经大西洋到达印度的航线。",
      "source": "教材第35页；同上段。"
    }
  ],
  "edges": [
    {
      "from": "n01",
      "to": "n02",
      "kind": "causal",
      "label": "控制商路后另寻航线",
      "evidence": "教材第35页；原文直接说明阿拉伯商人控制商路后，西欧人开始寻找新航线。"
    }
  ]
}
```

`x`、`y` 可选；不填时脚本按关系方向自动分层布局，并支持多个互不连通的节点组。

## 流程

1. 读源文件，先写一句范围说明，列出纳入和排除的段落。
2. 只抽节点：为每个节点写 `id`、名称、类型、时间、描述和来源；此步不连边。
3. 再抽关系：只能连接已存在的节点；每条边写 `evidence` 和短标签。找不到证据的关系不要画。
4. 审查：合并同义节点，删除重复边和没有解释价值的边；保留少量有意为之的上下文节点。
5. 生成项目：

```bash
python scripts/plan_to_pastlines.py plan.json graph.pastlines
```

默认按 1440×900 内容区计算初始缩放。要交付给 1024×768 屏幕时，再加：

```bash
python scripts/plan_to_pastlines.py plan.json graph.pastlines --viewport-width 1024 --viewport-height 768
```

6. 校验：

```bash
python scripts/validate_pastlines.py graph.pastlines --require-sources
```

7. 如果当前电脑有 Pastlines，使用项目唯一入口 `src\Pastlines.cmd` 打开新文件，检查 1440×900 和 1024×768 两个内容区；至少看节点是否都在画面内、文字是否裁切、关系方向是否读得通。

## 交付

- `.pastlines` 项目文件。
- 同名 `.plan.json`，保留节点来源和边证据。
- 一段简短质量报告：节点数、关系数、孤立节点、无来源节点、待确认关系、未解决项。

不要把“脚本退出 0”写成“图谱内容已验收”。脚本只证明格式和布局可生成；语义是否准确仍要对照原文。

## 停止条件

- 任一节点或关系缺少来源 → 先补证据，不生成最终文件。
- plan 校验失败、ID 冲突或关系指向不存在节点 → 不输出。
- 孤立节点超过 20% → 检查是否漏关系，或明确说明它们是上下文卡。
- 节点超过 40 个 → 拆成章节图或子图，不硬塞一张大图。
- 打开项目时报 schema 错误 → 不宣称完成，先修格式。

## 参考

- 字段、约束和最小合法项目：[references/pastlines-format.md](references/pastlines-format.md)
- 抽取、关系判断、布局和验收：[references/graph-method.md](references/graph-method.md)
