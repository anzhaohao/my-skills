#requires -Version 5.1

[CmdletBinding()]
param(
    [switch]$SkipApi,
    [switch]$VerifyApi,
    [switch]$SkipIllustrator,
    [switch]$RequireIllustratorOpen,
    [switch]$Json,
    [string]$SkillRoot = "",
    [string]$SecretPath = "",
    [string]$HomeRoot = ""
)

$ErrorActionPreference = "Stop"

# Dual-layout resolution: installed skill (scripts/doctor.ps1) or repository
# (installers/doctor.ps1 -> ../runtime/powershell).
$resolveConfig = Join-Path $PSScriptRoot "resolve-config.ps1"
if (-not (Test-Path -LiteralPath $resolveConfig -PathType Leaf)) {
    $resolveConfig = Join-Path $PSScriptRoot "..\runtime\powershell\resolve-config.ps1"
}
. $resolveConfig -HomeRoot $HomeRoot -SecretPath $SecretPath

$lockPath = Join-Path $PSScriptRoot "runtime-lock.json"
if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
    $lockPath = Join-Path $PSScriptRoot "..\runtime-lock.json"
}
if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
    throw "Missing runtime lock: $lockPath"
}
$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8 | ConvertFrom-Json

$results = New-Object System.Collections.Generic.List[object]
$fatal = $false

function Add-Check([string]$Name, [string]$Status, [string]$Message, [bool]$Required) {
    $script:results.Add([pscustomobject]@{
        name = $Name
        status = $Status
        required = $Required
        message = $Message
    })
    if ($Required -and $Status -eq "FAIL") { $script:fatal = $true }
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @("py", "-3") }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @("python") }
    return @()
}

if ($env:OS -eq "Windows_NT") { Add-Check "windows" "PASS" "Windows detected." $true }
else { Add-Check "windows" "FAIL" "Cell-lct stable supports Windows only." $true }

if ($PSVersionTable.PSVersion -ge [version]"5.1") { Add-Check "powershell" "PASS" $PSVersionTable.PSVersion.ToString() $true }
else { Add-Check "powershell" "FAIL" "PowerShell 5.1 or newer is required." $true }

$python = Get-PythonCommand
if ($python.Count -eq 0) {
    Add-Check "python" "FAIL" "Python 3.11-3.14 is required." $true
} else {
    $pythonExe = $python[0]
    $pythonPrefix = @()
    if ($python.Count -gt 1) { $pythonPrefix = $python[1..($python.Count - 1)] }
    $versionText = (& $pythonExe @pythonPrefix -c "import sys; print('.'.join(map(str,sys.version_info[:3])))" 2>&1 | Out-String).Trim()
    $pythonVersion = $null
    if ([version]::TryParse($versionText, [ref]$pythonVersion) -and $pythonVersion -ge [version]"3.11" -and $pythonVersion -lt [version]"3.15") {
        Add-Check "python" "PASS" $versionText $true
    } else {
        Add-Check "python" "FAIL" "Detected '$versionText'; supported range is 3.11-3.14." $true
    }

    $fontToolsVersion = (& $pythonExe @pythonPrefix -c "import fontTools; print(fontTools.__version__)" 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $fontToolsVersion -eq [string]$lock.pythonDependencies.fonttools) {
        Add-Check "fonttools" "PASS" $fontToolsVersion $true
    } else {
        Add-Check "fonttools" "FAIL" "Expected $($lock.pythonDependencies.fonttools), detected '$fontToolsVersion'. Run setup.ps1." $true
    }
}

# Skill location is user-controlled. An explicit -SkillRoot is checked hard;
# without one the check reports context instead of guessing a global default.
if (-not [string]::IsNullOrWhiteSpace($SkillRoot)) {
    $installedSkill = Join-Path $SkillRoot "SKILL.md"
    if (Test-Path -LiteralPath $installedSkill -PathType Leaf) {
        Add-Check "skill" "PASS" $installedSkill $true
    } else {
        Add-Check "skill" "FAIL" "Installed Skill not found at $installedSkill. Run setup.ps1 -SkillDestination <path>." $true
    }
} else {
    Add-Check "skill" "INFO" "No -SkillRoot given; skill location is user-defined (run setup.ps1 with -SkillDestination)." $false
}

Add-Check "image-edit-backend" "INFO" "Configured provider: $($merged.image_edit_provider) (set image_edit_provider in $configPath)." $false
Add-Check "vectorize-provider" "INFO" "Configured provider: $($merged.vectorize_provider) (remote API, no local deployment)." $false

if (-not $SkipIllustrator) {
    $progIdKey = "Registry::HKEY_CLASSES_ROOT\Illustrator.Application.30"
    if (Test-Path -LiteralPath $progIdKey) {
        Add-Check "illustrator-2026" "PASS" "Illustrator.Application.30 is registered." $true
    } else {
        Add-Check "illustrator-2026" "FAIL" "Illustrator 2026 COM registration was not found." $true
    }
    $illustratorProcess = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match "Illustrator" }
    if ($illustratorProcess) { Add-Check "illustrator-open" "PASS" "Illustrator is already running." $RequireIllustratorOpen.IsPresent }
    elseif ($RequireIllustratorOpen) { Add-Check "illustrator-open" "FAIL" "Open Illustrator and the target document yourself." $true }
    else { Add-Check "illustrator-open" "WARN" "Illustrator is not open; open it yourself before drawing." $false }
}

if (-not $SkipApi) {
    $resolvedSecret = Resolve-CellLctSecretPath -Explicit $SecretPath -CellLctHome $cellLctHome -ConfigValues $config.values
    if ($resolvedSecret.source -eq "missing") {
        Add-Check "api-key" "FAIL" "DPAPI key file is missing. Run setup.ps1 and configure it interactively." $true
    } else {
        try {
            $cipher = [IO.File]::ReadAllText($resolvedSecret.path, [Text.Encoding]::UTF8).Trim()
            $secure = ConvertTo-SecureString $cipher
            if ($secure.Length -gt 0) {
                $sourceNote = if ($resolvedSecret.source -eq "legacy-codex") { " (legacy Codex fallback)" } else { "" }
                Add-Check "api-key" "PASS" "DPAPI key is readable for the current Windows account$sourceNote." $true
            } else { Add-Check "api-key" "FAIL" "DPAPI key is empty." $true }
        } catch {
            Add-Check "api-key" "FAIL" "DPAPI key cannot be decrypted by this Windows account." $true
        }

        if ($VerifyApi -and -not $fatal) {
            $client = Join-Path $PSScriptRoot "xiaomiao.ps1"
            if (-not (Test-Path -LiteralPath $client -PathType Leaf)) {
                $client = Join-Path $PSScriptRoot "..\runtime\powershell\xiaomiao.ps1"
            }
            try {
                $arguments = @("verify", "-SecretPath", $resolvedSecret.path, "-HomeRoot", $cellLctHome)
                & $client @arguments | Out-Null
                Add-Check "api-connection" "PASS" "Authenticated API probe succeeded." $true
            } catch {
                Add-Check "api-connection" "FAIL" $_.Exception.Message $true
            }
        }
    }
}

$summary = [pscustomobject]@{
    product = "Cell-lct"
    version = [string]$lock.release
    ok = -not $fatal
    checks = $results
}

if ($Json) {
    $summary | ConvertTo-Json -Depth 5
} else {
    foreach ($item in $results) { Write-Output ("{0}|{1}|{2}" -f $item.status, $item.name, $item.message) }
    Write-Output ("DOCTOR_{0}|version={1}" -f $(if ($fatal) { "FAIL" } else { "OK" }), $lock.release)
}

if ($fatal) { exit 1 }
