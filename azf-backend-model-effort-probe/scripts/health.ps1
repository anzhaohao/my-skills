# azf-backend-model-effort-probe — 健康检查（探针是否在跑）
param([int]$Port = 18083)
$Project = "D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260825-backend-model-effort-probe"
$env:PYTHONPATH = Join-Path $Project "src"
python -m backend_model_effort_probe health --port $Port
