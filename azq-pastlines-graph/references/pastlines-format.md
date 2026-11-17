# Pastlines 项目格式

本技能只生成基础图谱，不处理图片编辑、样式导入或应用打包。最终文件必须通过 Pastlines 的 `validateProject`。

## 顶层字段

项目对象只允许这些键，多一个键会被拒绝：

| 字段 | 类型 | 说明 |
|---|---|---|
| `format` | string | 固定为 `pastlines-project` |
| `schemaVersion` | string | 固定为 `1.1` |
| `appVersion` | string | 当前应用版本，本项目为 `1.42.0` |
| `projectId` | string | 标准 UUID |
| `title` | string | 非空 |
| `createdAt` | string | 可解析的 ISO 时间 |
| `updatedAt` | string | 可解析的 ISO 时间 |
| `revision` | integer | 非负整数 |
| `graph` | object | 只含 `nodes` 和 `edges` |
| `assets` | object | 基础图谱用 `{}` |
| `viewport` | object | 只含 `x`、`y`、`zoom` |
| `appearance` | object | 只含 `styleId` 和 `snapshot` |

## 节点

每个节点只允许这些键：

| 字段 | 类型 | 约束 |
|---|---|---|
| `id` | string | ASCII `[A-Za-z0-9_.-]+`，全项目唯一 |
| `name` | string | 非空 |
| `type` | string | 建议使用 `事件`、`人物`、`地点`、`群体`、`制度`、`概念`、`史料` |
| `time` | string | 可为空；有明确时间时写简短形式 |
| `description` | string | 卡片正文，1–3 句 |
| `source` | string | 来源定位和证据短引；本技能要求非空 |
| `x` | number | 节点左上角横坐标 |
| `y` | number | 节点左上角纵坐标 |
| `imageIds` | string[] | 只能引用 `assets` 中存在的 ID；基础图谱为 `[]` |
| `color` | string | 空字符串，或 `#RRGGBB` 浅色 |

## 关系

每条边只允许这些键：

| 字段 | 类型 | 约束 |
|---|---|---|
| `id` | string | ASCII `[A-Za-z0-9_.-]+`，全项目唯一 |
| `from` | string | 已存在的节点 ID |
| `to` | string | 已存在的节点 ID |
| `kind` | string | 五类之一 |
| `label` | string | 可为空；建议写 4–12 字的动词短语 |

关系类型：

- `pending`：待确认，最安全的默认值。
- `causal`：因果，从因指向果。
- `temporal`：时序，从早指向晚。
- `comparison`：对比，方向只表示比较的起点。
- `membership`：从属，从部分指向整体。

`.pastlines` 的边没有 `source` 或 `evidence` 字段。证据必须留在 plan 中，不要把长证据塞进 `label`。

## 视角与样式

`viewport` 只含：

```json
{"x": 60, "y": 60, "zoom": 1}
```

`zoom` 允许 0.1–5。基础图谱默认使用 `assets/default-style.json`，复制为 `appearance.snapshot`，并把 `appearance.styleId` 设为 `pastlines-default`。

样式对象只允许：

```text
format, version, id, name, colors, metrics, resources, backgroundImage
```

颜色必须是 `#RRGGBB`；`overlay` 必须是安全的 `rgba(...)`。不要改样式里的对比度，否则应用会拒绝。

## 最小合法骨架

```json
{
  "format": "pastlines-project",
  "schemaVersion": "1.1",
  "appVersion": "1.42.0",
  "projectId": "00000000-0000-4000-8000-000000000000",
  "title": "示例",
  "createdAt": "2026-01-01T00:00:00.000Z",
  "updatedAt": "2026-01-01T00:00:00.000Z",
  "revision": 0,
  "graph": {"nodes": [], "edges": []},
  "assets": {},
  "viewport": {"x": 60, "y": 60, "zoom": 1},
  "appearance": {"styleId": "pastlines-default", "snapshot": null}
}
```

实际生成的 `appearance.snapshot` 使用完整默认样式，不要留 `null`。

## 来源写法

节点来源建议使用统一格式：

```text
来源=教材第35页；原文=「……」；说明=这句只支持A，不支持B。
```

如果是整段概括而不是原文，明确写“转述”：

```text
来源=教材第35页；转述=阿拉伯商人控制东地中海商路，西欧人因此另寻航线；证据=E02。
```
