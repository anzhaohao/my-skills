# invoke-deepsight.ps1 — 稳定跨目录调用入口
# 从本地配置读取 DeepSight 项目根，使用 uv run 调用 deepsight CLI。
# 不依赖 PATH 中的 deepsight 命令。
# 原样转发所有参数与原样传播子进程退出码。
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)
$ErrorActionPreference = 'Stop'

# 定位本脚本所在目录 → Skill 安装根
$ScriptDir = Split-Path -Parent $PSCommandPath
$SkillRoot = Split-Path -Parent $ScriptDir

# 读取本地配置
$ConfigPath = Join-Path $SkillRoot 'local-config.json'
if (-not (Test-Path $ConfigPath)) {
    Write-Host "[DeepSight] 错误: 未找到 local-config.json（$ConfigPath）。请运行安装脚本。" -ForegroundColor Red
    exit 2
}

try {
    $config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
} catch {
    Write-Host "[DeepSight] 错误: local-config.json 不是合法 JSON: $_" -ForegroundColor Red
    exit 2
}

$ProjectRoot = $config.project_root
if (-not $ProjectRoot) {
    Write-Host "[DeepSight] 错误: local-config.json 缺少 project_root" -ForegroundColor Red
    exit 2
}

# 验证项目根
if (-not (Test-Path $ProjectRoot)) {
    Write-Host "[DeepSight] 错误: 项目根不存在: $ProjectRoot" -ForegroundColor Red
    exit 2
}

$PyprojectPath = Join-Path $ProjectRoot 'pyproject.toml'
if (-not (Test-Path $PyprojectPath)) {
    Write-Host "[DeepSight] 错误: 项目根缺少 pyproject.toml: $PyprojectPath" -ForegroundColor Red
    exit 2
}

# 检查 uv 是否可用
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    Write-Host "[DeepSight] 错误: uv 不可用。请安装 uv (https://docs.astral.sh/uv/)。" -ForegroundColor Red
    exit 3
}

# 构造参数数组并使用 splatting 原样转发
# splatting (@) 保持每个参数为独立数组元素，不因空格而分裂
$allArgs = @('run', '--project', $ProjectRoot, 'deepsight') + $RemainingArgs

# 使用 & 操作符 + splatting 原样传播退出码
& uv $allArgs
exit $LASTEXITCODE
