#requires -Version 5.1
# Cell-lct Harness-neutral configuration and secret resolution.
#
# This script is the single source of truth for every path decision:
#   - Cell-lct home directory (default: ~/.cell-lct)
#   - config.json (optional user overrides, never secrets)
#   - DPAPI secret file location
#
# Resolution priority (highest first):
#   1. explicit script parameters
#   2. CELL_LCT_* environment variables
#   3. ~/.cell-lct/config.json
#   4. built-in defaults
#   5. legacy Codex fallback (~/.codex/secrets/xiaomiao-api-key.dpapi) ONLY
#      when the neutral default file does not exist, so existing installs
#      keep working after upgrade without copying plaintext keys.
#
# Usage:
#   & resolve-config.ps1                 -> prints resolved JSON
#   & resolve-config.ps1 -SecretPath X   -> explicit override
#   . resolve-config.ps1                 -> dot-source; call the functions below

[CmdletBinding()]
param(
    [string]$HomeRoot = "",
    [string]$ConfigPath = "",
    [string]$SecretPath = "",
    [string]$ImageEditProvider = "",
    [string]$VectorizeProvider = "",
    [string]$XiaomiaoBaseUrl = ""
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------- defaults

$script:DefaultConfig = @{
    image_edit_provider = "codex-agent"
    vectorize_provider = "xiaomiao"
    xiaomiao_base_url = "https://xiaomiao-ai.com"
    output_root = ""
    # Toggle: require user confirmation before uploading when the estimated
    # credit cost exceeds 1 (default on; disables the gate when off).
    credit_gate_enabled = $true
    # Toggle: run diagnostics automatically at the end of setup.ps1.
    setup_run_doctor = $true
    skill_install = @{
        # User-declared default skill destination. Never hard-coded by the
        # project: only used when the user sets it here (config page or
        # config.json), and always overridable with -SkillDestination.
        preferred_destination = ""
    }
    runtime = @{
        min_batch_size = 20
        max_batch_size = 50
        complex_point_threshold = 320
        max_batch_points = 2200
        checkpoint_seconds = 30
        in_session_retry_limit = 12
    }
    image_edit = @{
        codex_instruction = @"
Only remove all visible text and glyphs from the image and naturally restore
the adjacent background. Keep every arrow and arrow tail, connector, frame,
coordinate axis, tick mark, heatmap, legend, scientific subject, color, size,
relative position, layer order, and the complete layout. Do not add, move,
redraw, or restyle any non-text element.
"@
    }
}

# ---------------------------------------------------------------- functions

function Get-CellLctHome {
    param([string]$Override = "")
    if (-not [string]::IsNullOrWhiteSpace($Override)) { return [IO.Path]::GetFullPath($Override) }
    $envHome = $env:CELL_LCT_HOME
    if (-not [string]::IsNullOrWhiteSpace($envHome)) { return [IO.Path]::GetFullPath($envHome) }
    return Join-Path $env:USERPROFILE ".cell-lct"
}

function Get-CellLctConfigPath {
    param([string]$cellLctHome)
    return Join-Path $cellLctHome "config.json"
}

function Read-CellLctConfig {
    param([string]$ConfigPath)
    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
        return @{ config_found = $false; values = $null }
    }
    try {
        $raw = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        return @{ config_found = $true; values = $raw }
    } catch {
        throw "CELL_LCT_CONFIG_INVALID|$ConfigPath|$($_.Exception.Message)"
    }
}

function Merge-CellLctConfig {
    param($Defaults, $UserValues)
    $merged = $Defaults
    if ($null -eq $UserValues) { return $merged }
    foreach ($property in $UserValues.PSObject.Properties) {
        $merged[$property.Name] = $property.Value
    }
    return $merged
}

function Get-EnvOverride([string]$Name) {
    $value = [Environment]::GetEnvironmentVariable("CELL_LCT_$Name")
    return $(if ([string]::IsNullOrWhiteSpace($value)) { "" } else { $value })
}

function Resolve-RuntimeFile {
    param([string]$Name, [string]$SubDir = "")
    # Installed layout: runtime files are flattened into the skill scripts dir.
    $flat = Join-Path $PSScriptRoot $Name
    if (Test-Path -LiteralPath $flat -PathType Leaf) { return $flat }
    # Repository layout: powershell/ ../python/ and ../illustrator/.
    if (-not [string]::IsNullOrWhiteSpace($SubDir)) {
        $nested = Join-Path $PSScriptRoot "..\$SubDir\$Name"
        if (Test-Path -LiteralPath $nested -PathType Leaf) { return $nested }
    }
    throw "CELL_LCT_RUNTIME_FILE_MISSING|$Name"
}

function Resolve-CellLctSecretPath {
    param(
        [string]$Explicit = "",
        [string]$cellLctHome,
        $ConfigValues
    )
    if (-not [string]::IsNullOrWhiteSpace($Explicit)) {
        return @{ path = [IO.Path]::GetFullPath($Explicit); source = "explicit" }
    }
    $envSecret = Get-EnvOverride "XIAOMIAO_SECRET"
    if (-not [string]::IsNullOrWhiteSpace($envSecret)) {
        return @{ path = [IO.Path]::GetFullPath($envSecret); source = "environment" }
    }
    if ($null -ne $ConfigValues -and $ConfigValues.secrets -and $ConfigValues.secrets.xiaomiao_api_key) {
        return @{ path = [IO.Path]::GetFullPath([string]$ConfigValues.secrets.xiaomiao_api_key); source = "config" }
    }
    $neutralPath = Join-Path $cellLctHome "secrets\xiaomiao-api-key.dpapi"
    if (Test-Path -LiteralPath $neutralPath -PathType Leaf) {
        return @{ path = $neutralPath; source = "default" }
    }
    # Legacy Codex fallback: read-only compatibility, never the default.
    $legacyPath = Join-Path $env:USERPROFILE ".codex\secrets\xiaomiao-api-key.dpapi"
    if (Test-Path -LiteralPath $legacyPath -PathType Leaf) {
        return @{ path = $legacyPath; source = "legacy-codex" }
    }
    return @{ path = $neutralPath; source = "missing" }
}

function Read-CellLctSecret {
    param([string]$SecretPath)
    if (-not (Test-Path -LiteralPath $SecretPath -PathType Leaf)) {
        throw "CELL_LCT_SECRET_MISSING|$SecretPath|Run set-xiaomiao-key.ps1 to store the key with Windows DPAPI."
    }
    $cipherText = [IO.File]::ReadAllText($SecretPath, [Text.Encoding]::UTF8).Trim()
    $secureValue = ConvertTo-SecureString $cipherText
    $pointer = [IntPtr]::Zero
    try {
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    finally {
        if ($pointer -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        }
    }
}

# ---------------------------------------------------------------- resolve

$cellLctHome = Get-CellLctHome -Override $HomeRoot
$configPath = if (-not [string]::IsNullOrWhiteSpace($ConfigPath)) { [IO.Path]::GetFullPath($ConfigPath) } else { Get-CellLctConfigPath -CellLctHome $cellLctHome }
$config = Read-CellLctConfig -ConfigPath $configPath
$merged = Merge-CellLctConfig -Defaults $script:DefaultConfig -UserValues $config.values

$envImageEdit = Get-EnvOverride "IMAGE_EDIT_PROVIDER"
$envVectorize = Get-EnvOverride "VECTORIZE_PROVIDER"
$envBaseUrl = Get-EnvOverride "XIAOMIAO_BASE_URL"

if (-not [string]::IsNullOrWhiteSpace($ImageEditProvider)) { $merged.image_edit_provider = $ImageEditProvider }
elseif (-not [string]::IsNullOrWhiteSpace($envImageEdit)) { $merged.image_edit_provider = $envImageEdit }
if (-not [string]::IsNullOrWhiteSpace($VectorizeProvider)) { $merged.vectorize_provider = $VectorizeProvider }
elseif (-not [string]::IsNullOrWhiteSpace($envVectorize)) { $merged.vectorize_provider = $envVectorize }
if (-not [string]::IsNullOrWhiteSpace($XiaomiaoBaseUrl)) { $merged.xiaomiao_base_url = $XiaomiaoBaseUrl }
elseif (-not [string]::IsNullOrWhiteSpace($envBaseUrl)) { $merged.xiaomiao_base_url = $envBaseUrl }

$secret = Resolve-CellLctSecretPath -Explicit $SecretPath -CellLctHome $cellLctHome -ConfigValues $config.values

$result = [ordered]@{
    cell_lct_home = $cellLctHome
    config_path = $configPath
    config_found = $config.config_found
    secret_path = $secret.path
    secret_source = $secret.source
    image_edit_provider = [string]$merged.image_edit_provider
    vectorize_provider = [string]$merged.vectorize_provider
    xiaomiao_base_url = [string]$merged.xiaomiao_base_url
    output_root = [string]$merged.output_root
    credit_gate_enabled = [bool]$merged.credit_gate_enabled
    setup_run_doctor = [bool]$merged.setup_run_doctor
    runtime = $merged.runtime
    skill_install = $merged.skill_install
    image_edit_codex_instruction = [string]$merged.image_edit.codex_instruction
}

if ($MyInvocation.InvocationName -ne ".") {
    $result | ConvertTo-Json -Depth 8
}
