[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('config-validate', 'model-info', 'production-preview', 'gaps', 'scheduled-dry-run', 'scheduled-run', 'generate', 'validate', 'backfill-preview', 'backfill')]
    [string]$Operation,
    [string]$ConfigPath,
    [string]$Week,
    [string]$Weeks,
    [switch]$ConfirmProductionWrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

$PythonPath = 'E:\software\Anaconda\envs\20260715-ai-paper-weekly\python.exe'
$DefaultConfigPath = 'D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\config\paper-weekly.production.local.yaml'
if (-not $ConfigPath) {
    if ($env:PAPER_WEEKLY_CONFIG) {
        $ConfigPath = $env:PAPER_WEEKLY_CONFIG
    }
    else {
        $ConfigPath = $DefaultConfigPath
    }
}
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "Production Python was not found: $PythonPath"
}
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "Paper-weekly config was not found: $ConfigPath"
}

$Arguments = @('-m', 'paper_weekly')
switch ($Operation) {
    'config-validate' {
        $Arguments += @('config', 'validate', '--config', $ConfigPath, '--json')
    }
    'model-info' {
        $Arguments += @('config', 'model-info', '--config', $ConfigPath, '--json')
    }
    'production-preview' {
        $Arguments += @('production-preview', '--config', $ConfigPath, '--json')
    }
    'gaps' {
        $Arguments += @('gaps', '--config', $ConfigPath, '--json')
    }
    'scheduled-dry-run' {
        $Arguments += @('run', '--scheduled', '--dry-run', '--config', $ConfigPath, '--json')
    }
    'scheduled-run' {
        if (-not $ConfirmProductionWrite) {
            throw 'scheduled-run requires -ConfirmProductionWrite.'
        }
        $Arguments += @('run', '--scheduled', '--config', $ConfigPath, '--json')
    }
    'generate' {
        if (-not $ConfirmProductionWrite) {
            throw 'generate requires -ConfirmProductionWrite.'
        }
        if (-not $Week) {
            throw 'generate requires -Week, for example 2026-W28.'
        }
        $Arguments += @('generate', '--week', $Week, '--config', $ConfigPath, '--json')
    }
    'validate' {
        if (-not $Week) {
            throw 'validate requires -Week, for example 2026-W28.'
        }
        $Arguments += @('validate', '--week', $Week, '--config', $ConfigPath, '--json')
    }
    'backfill-preview' {
        if (-not $Weeks) {
            throw 'backfill-preview requires -Weeks as a comma-separated ISO-week list.'
        }
        $Arguments += @('backfill', '--weeks', $Weeks, '--dry-run', '--config', $ConfigPath, '--json')
    }
    'backfill' {
        if (-not $ConfirmProductionWrite) {
            throw 'backfill requires -ConfirmProductionWrite.'
        }
        if (-not $Weeks) {
            throw 'backfill requires -Weeks as a comma-separated ISO-week list.'
        }
        $Arguments += @('backfill', '--weeks', $Weeks, '--config', $ConfigPath, '--json')
    }
}

& $PythonPath @Arguments
exit $LASTEXITCODE
