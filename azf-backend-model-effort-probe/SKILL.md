---
name: azf-backend-model-effort-probe
description: >-
  Report the backend model and reasoning_effort that cc-haha actually sent this
  turn, by querying the local backend-model-effort-probe transparent proxy. Use
  ONLY when the user explicitly invokes $azf-backend-model-effort-probe to ask
  what model / thinking strength the backend really received. Never guess effort
  from UI labels, defaults, latency, or reasoning text.
policy:
  allow_implicit_invocation: false
---

# AZF Backend Model Effort Probe

Answer what model and reasoning strength the **backend actually received** for
the current turn, based on the local transparent proxy's record of the most
recent outbound request. This measures request *fields*, not the provider's
internal compute.

**Trigger:** only when the user explicitly references `$azf-backend-model-effort-probe`.
`policy.allow_implicit_invocation: false` — never auto-apply.

## Hard rules

- The measured "effort" is the request field (`reasoning_effort` / nested
  `reasoning.effort`), nothing more. Never claim to know the provider's real
  internal compute.
- If the response echoes a `model`, report it; if not, write `未回显`.
- If no effort field was sent, write `未发送`. Never infer from UI labels,
  model defaults, response time, or thinking text.
- If you cannot verify this turn's request, output the unverified line. Do NOT
  substitute an older record.

## Procedure

1. **Check proxy health** (must be running for a verifiable answer):

   ```bash
   PYTHONPATH="D:/Postgraduate_JilinUniversity/03_Sundries/02_DevLab/20260825-backend-model-effort-probe/src" \
     python -m backend_model_effort_probe health
   ```

2. **Query this turn's most recent matching request** (compact, safe JSON only):

   ```bash
   PYTHONPATH="D:/Postgraduate_JilinUniversity/03_Sundries/02_DevLab/20260825-backend-model-effort-probe/src" \
     python -m backend_model_effort_probe current --model k3-256k --json
   ```

   `status:"verified"` → you have this turn's fields. `status:"unverified"` →
   do not guess.

3. **Answer the user's question normally.**

4. **Append the result as the LAST non-empty line** of your reply, exactly in
   one of the formats below. Nothing may follow that line — no note, no
   punctuation block, no hint.

## Output formats (final line)

Verified, response echoed the model:

```
后端实测｜请求模型=k3-256k｜响应模型=k3-256k｜reasoning_effort=high｜证据=本轮最近出站请求
```

Verified, response did NOT echo the model:

```
后端实测｜请求模型=k3-256k｜响应模型=未回显｜reasoning_effort=high｜证据=本轮最近出站请求
```

Verified, no effort field was sent (add `thinking` when present):

```
后端实测｜请求模型=k3-256k｜响应模型=未回显｜reasoning_effort=未发送｜thinking=enabled｜证据=本轮最近出站请求
```

Cannot verify (proxy down or no match this turn):

```
后端实测｜不可验证：探针未运行或未匹配到本轮请求
```

## Field mapping from CLI JSON

- `model` → 请求模型
- `response_model` → 响应模型（`null` → `未回显`）
- `reasoning_effort` → reasoning_effort（already `未发送` when absent; nested
  `reasoning.effort` is folded in by the CLI）
- `thinking` → thinking（only include the segment when non-null）
- `verified:false` → use the 不可验证 line
