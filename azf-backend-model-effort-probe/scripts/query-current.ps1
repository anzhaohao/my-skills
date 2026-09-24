# azf-backend-model-effort-probe — 取本轮最近一次出站请求（安全 JSON）
# 供 Skill 调用。只读，不修改任何状态。
param(
    [string]$Model = "k3-256k",
    [double]$Window = 120
)
$Project = "D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260825-backend-model-effort-probe"
$env:PYTHONPATH = Join-Path $Project "src"
python -m backend_model_effort_probe current --model $Model --window $Window --json
