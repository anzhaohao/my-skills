#requires -Version 5.1
# Xiaomiao vectorize provider implementation (remote API, no local backend).
#
# Exposes the provider contract used by vectorize.ps1:
#   verify / upload / status / download through the bundled adapter.
# -AdapterPath lets tests or custom vector APIs plug in a compatible adapter.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputImage,

    [Parameter(Mandatory = $true)]
    [string]$OutputSvg,

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
$ProgressPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "resolve-config.ps1")

$inputPath = (Resolve-Path -LiteralPath $InputImage).Path
$outputPath = [IO.Path]::GetFullPath($OutputSvg)
$outputDirectory = Split-Path -Parent $outputPath
if ($outputDirectory) {
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
}

$adapter = if (-not [string]::IsNullOrWhiteSpace($AdapterPath)) { [IO.Path]::GetFullPath($AdapterPath) } else { Join-Path $PSScriptRoot "xiaomiao.ps1" }
$validator = Resolve-RuntimeFile -Name "validate_vector_svg.py" -SubDir "python"
$creditPolicy = Join-Path $PSScriptRoot "assert-credit-policy.ps1"
foreach ($required in @($adapter, $validator, $creditPolicy)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Missing required runtime file: $required"
    }
}

function Invoke-Adapter([string]$ActionName, [hashtable]$Extra = @{}) {
    $named = @{}
    if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) { $named.BaseUrl = $BaseUrl }
    if (-not [string]::IsNullOrWhiteSpace($SecretPath)) { $named.SecretPath = $SecretPath }
    if (-not [string]::IsNullOrWhiteSpace($HomeRoot)) { $named.HomeRoot = $HomeRoot }
    foreach ($key in $Extra.Keys) { $named[$key] = $Extra[$key] }
    # Hashtable splatting binds keys as named parameters (array splatting
    # would pass "-Name" tokens as positional arguments).
    return & $adapter $ActionName @named
}

# This gate runs before authentication or upload so no image bytes leave the
# computer when a known estimate exceeds the user's threshold.
& $creditPolicy -EstimatedCredits $EstimatedCredits -MaxWithoutConfirmation $MaxCreditsWithoutConfirmation -ImageId "preflight" -Approved:$ApproveHighCost | Out-Null

# Authentication is checked without charging credits.
$verification = Invoke-Adapter "verify"
if ($null -eq $verification -or $verification.authenticated -ne $true) {
    throw "Xiaomiao authentication could not be verified."
}

$submission = Invoke-Adapter "upload" @{ ImagePath = $inputPath }
$imageId = [string]$submission.image_id
if ([string]::IsNullOrWhiteSpace($imageId)) {
    throw "Xiaomiao did not return an image id."
}

$deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
$job = $null
$lastStatusError = $null
do {
    try {
        $job = Invoke-Adapter "status" @{ ImageId = $imageId }
        $lastStatusError = $null
    }
    catch {
        $lastStatusError = $_.Exception.Message
        if ([DateTime]::UtcNow -ge $deadline) { break }
        Start-Sleep -Seconds $PollSeconds
        continue
    }
    $status = [string]$job.status
    if ($status -eq "completed") { break }
    if ($status -in @("failed", "expired", "rejected")) {
        throw "Xiaomiao job ended with status: $status"
    }
    if ($null -ne $job.credits_left -and [int]$job.credits_left -lt 0) {
        throw "Xiaomiao credits are unavailable."
    }
    if ([DateTime]::UtcNow -ge $deadline) {
        throw "Xiaomiao job timed out after $TimeoutSeconds seconds."
    }
    Start-Sleep -Seconds $PollSeconds
} while ($true)

if ($null -eq $job -or [string]$job.status -ne "completed") {
    $suffix = if ($lastStatusError) { " Last status error: $lastStatusError" } else { "" }
    throw "Xiaomiao job timed out after $TimeoutSeconds seconds.$suffix"
}

$temporarySvg = "$outputPath.download.$PID"
try {
    $downloaded = $false
    $lastDownloadError = $null
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Invoke-Adapter "download" @{ ImageId = $imageId; OutputPath = $temporarySvg } | Out-Null
            $downloaded = $true
            break
        }
        catch {
            $lastDownloadError = $_.Exception.Message
            if ($attempt -lt 5) { Start-Sleep -Seconds $PollSeconds }
        }
    }
    if (-not $downloaded) {
        throw "Xiaomiao SVG download failed after retries: $lastDownloadError"
    }

    $validationOutput = & py -3 -X utf8 $validator --svg $temporarySvg 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Downloaded result is not a valid true-vector SVG: $validationOutput"
    }

    Move-Item -LiteralPath $temporarySvg -Destination $outputPath -Force
}
finally {
    if (Test-Path -LiteralPath $temporarySvg -PathType Leaf) {
        Remove-Item -LiteralPath $temporarySvg -Force
    }
}

[ordered]@{
    ok = $true
    image_id = $imageId
    output_svg = $outputPath
    credits_left = $job.credits_left
} | ConvertTo-Json -Compress
