#requires -Version 5.1
# Cell-lct unified vectorize provider dispatcher.
#
# Turns a text-cleaned reference image into a true-vector SVG through the
# configured vectorize provider. The default provider is the remote Xiaomiao
# API (no local deployment required). -AdapterPath allows tests and future
# custom vector APIs to plug in any adapter exposing the same contract:
#   verify / upload / status / download  (see runtime/powershell/xiaomiao.ps1)

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputImage,

    [Parameter(Mandatory = $true)]
    [string]$OutputSvg,

    [string]$Provider = "",

    [ValidateRange(2, 60)]
    [int]$PollSeconds = 5,

    [ValidateRange(30, 3600)]
    [int]$TimeoutSeconds = 900,

    [ValidateRange(1, 1000000)]
    [int]$MaxCreditsWithoutConfirmation = 1,

    [ValidateRange(0, 1000000)]
    [int]$EstimatedCredits = 1,

    [switch]$ApproveHighCost,

    [string]$BaseUrl = "",
    [string]$SecretPath = "",
    [string]$HomeRoot = "",

    [string]$AdapterPath = ""
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "resolve-config.ps1") -HomeRoot $HomeRoot -SecretPath $SecretPath -XiaomiaoBaseUrl $BaseUrl
$provider = if (-not [string]::IsNullOrWhiteSpace($Provider)) { $Provider } else { [string]$merged.vectorize_provider }

switch ($provider) {
    "xiaomiao" {
        # Config toggle credit_gate_enabled=false lifts the confirmation
        # threshold so uploads never pause (still gated by -ApproveHighCost).
        $gateMax = if ([bool]$merged.credit_gate_enabled) { $MaxCreditsWithoutConfirmation } else { 1000000 }
        $arguments = @{
            InputImage = $InputImage
            OutputSvg = $OutputSvg
            PollSeconds = $PollSeconds
            TimeoutSeconds = $TimeoutSeconds
            MaxCreditsWithoutConfirmation = $gateMax
            EstimatedCredits = $EstimatedCredits
            BaseUrl = [string]$merged.xiaomiao_base_url
        }
        if ($ApproveHighCost) { $arguments.ApproveHighCost = $true }
        if (-not [string]::IsNullOrWhiteSpace($SecretPath)) { $arguments.SecretPath = $SecretPath }
        if (-not [string]::IsNullOrWhiteSpace($HomeRoot)) { $arguments.HomeRoot = $HomeRoot }
        if (-not [string]::IsNullOrWhiteSpace($AdapterPath)) { $arguments.AdapterPath = $AdapterPath }
        & (Join-Path $PSScriptRoot "vectorize-xiaomiao.ps1") @arguments
        if (-not $?) { exit 1 }
        exit 0
    }

    default {
        throw "VECTORIZE_PROVIDER_UNKNOWN|$provider|Supported: xiaomiao (custom-vector-api via -AdapterPath)."
    }
}
