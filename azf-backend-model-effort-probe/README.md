# azf-backend-model-effort-probe

这个 Skill 回答一个具体问题：**这一轮 cc-haha 发给后端（Dongsy 上游 / Kimi K3）的，
到底是哪个模型、带了什么推理强度字段。**

## 解决什么问题

光凭 Claude Code 前端标签、模型默认值、回答耗时或"思考文本"，都无法确定后端真实收到
的 `model` 和 `reasoning_effort`。普通 cc-haha trace 也不保证记录成功请求的最终强度。
本 Skill 通过一个本地透明代理（项目 `backend-model-effort-probe`）在请求转发前记录安全
元数据，再由 CLI 取回"本轮最近一次出站请求"，把后端实测结果作为回答的最后一行。

## 什么时候触发

**只在用户显式输入 `$azf-backend-model-effort-probe` 时触发。**
已设 `policy.allow_implicit_invocation: false`，不会被自动套用。

## 它测的是什么 / 不是什么

- 测的是**请求字段**：cc-haha 最终发出的 `model`、`reasoning_effort`（含嵌套
  `reasoning.effort`）、`thinking` 开关。
- **不是**供应商内部真实投入的算力——那无法从外部得知。
- 响应回显了 `model` 就记录；没回显写"未回显"；没发强度字段写"未发送"。**绝不猜测。**

## 关键事实 / 配置

- 配套项目：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260825-backend-model-effort-probe`
- 代理只监听 `127.0.0.1:18083`，转发到 `https://api.dongsy.com.cn`。
- 密钥只在内存透传给上游，**绝不落盘**；不记录 messages/提示词/正文/工具参数/图片。
- 状态存 `%LOCALAPPDATA%\azf-backend-model-effort-probe\state.jsonl`，只留最近 20 条。
- 当前验收模型 ID：`k3-256k`。

## 调用方式

```bash
# 健康检查
PYTHONPATH="<项目>/src" python -m backend_model_effort_probe health
# 取本轮最近匹配（安全 JSON）
PYTHONPATH="<项目>/src" python -m backend_model_effort_probe current --model k3-256k --json
```

结果格式化为回答**最后一个非空行**，该行之后不再输出任何内容。

## 前置条件

Skill 能给出"verified"结果的前提是：探针已在运行，且 cc-haha 的
`ANTHROPIC_BASE_URL` 指向 `http://127.0.0.1:18083`。否则只能输出"不可验证"。
切换与回滚见项目 `scripts\start-probe.ps1` / `restore-direct.ps1`。

## 最近一次维护

2026-08-25 初版：项目骨架、透明代理、CLI、46 个无联网测试与密钥扫描全部通过。
Skill 文件与索引建立。尚未做：改 cc-haha 配置接入探针、真实付费 Kimi 请求验证
（这两项需用户确认后才进行）。
