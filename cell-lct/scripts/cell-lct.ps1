#requires -Version 5.1
# Cell-lct unified Harness-neutral CLI.
#
# One stable entry point for every harness. A harness only needs to know this
# command; it never reaches into the runtime scripts directly.
#
#   cell-lct.ps1 doctor
#   cell-lct.ps1 verify
#   cell-lct.ps1 image-clean -InputImage <path> -OutputImage <path> [-Provider <name>]
#   cell-lct.ps1 vectorize -InputImage <path> -OutputSvg <path> [-Provider <name>] [-AdapterPath <path>]
#   cell-lct.ps1 prepare -InputSvg <path> -WorkDir <path> [-JobId <id>]
#   cell-lct.ps1 draw -InputSvg <path> -WorkDir <path> [-OutputAi <path>] [-OutputPng <path>] [-DryRun]
#   cell-lct.ps1 reconstruct -InputImage <path> -TextManifest <path> -OutputRoot <path> [-DryRun]

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("doctor", "verify", "image-clean", "vectorize", "prepare", "draw", "reconstruct")]
    [string]$Command = "doctor",

    [string]$InputImage,
    [string]$OutputImage,
    [string]$InputSvg,
    [string]$OutputSvg,
    [string]$WorkDir,
    [string]$OutputAi,
    [string]$OutputPng,
    [string]$TextManifest,
    [string]$OutputRoot,
    [string]$JobId = "",
    [string]$Provider = "",
    [string]$AdapterPath = "",
    [string]$HomeRoot = "",
    [string]$SecretPath = "",
    [int]$MinBatchSize = 20,
    [int]$MaxBatchSize = 50,
    [switch]$DryRun,
    [switch]$SkipApi,
    [switch]$SkipIllustrator
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "resolve-config.ps1") -HomeRoot $HomeRoot -SecretPath $SecretPath

function Find-CellLctFile([string[]]$Candidates) {
    foreach ($candidate in $Candidates) {
        $path = Join-Path $PSScriptRoot $candidate
        if (Test-Path -LiteralPath $path -PathType Leaf) { return $path }
    }
    throw "CELL_LCT_RUNTIME_FILE_MISSING|$($Candidates -join ' or ')"
}

function Assert-Required([string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "CELL_LCT_ARGUMENT_MISSING|-$Name is required for '$Command'." }
}

switch ($Command) {
    "doctor" {
        $doctor = Find-CellLctFile @("doctor.ps1", "..\..\installers\doctor.ps1")
        $arguments = @{}
        if (-not [string]::IsNullOrWhiteSpace($HomeRoot)) { $arguments.HomeRoot = $HomeRoot }
        if ($SkipApi) { $arguments.SkipApi = $true }
        if ($SkipIllustrator) { $arguments.SkipIllustrator = $true }
        & $doctor @arguments
        if (-not $?) { exit 1 }
        exit 0
    }

    "verify" {
        $adapter = Find-CellLctFile @("xiaomiao.ps1")
        $named = @{}
        if (-not [string]::IsNullOrWhiteSpace($SecretPath)) { $named.SecretPath = $SecretPath }
        if (-not [string]::IsNullOrWhiteSpace($HomeRoot)) { $named.HomeRoot = $HomeRoot }
        $result = & $adapter verify @named
        if (-not $? -or $null -eq $result -or $result.authenticated -ne $true) {
            throw "CELL_LCT_VERIFY_FAILED|Vectorize-provider authentication could not be verified."
        }
        [ordered]@{
            ok = $true
            service = "xiaomiao"
            authenticated = $true
        } | ConvertTo-Json -Compress
        exit 0
    }

    "image-clean" {
        Assert-Required "InputImage" $InputImage
        Assert-Required "OutputImage" $OutputImage
        $dispatcher = Find-CellLctFile @("image-edit.ps1", "..\..\providers\image-edit\image-edit.ps1")
        $arguments = @{
            InputImage = $InputImage
            OutputImage = $OutputImage
        }
        if (-not [string]::IsNullOrWhiteSpace($Provider)) { $arguments.Provider = $Provider }
        if (-not [string]::IsNullOrWhiteSpace($HomeRoot)) { $arguments.HomeRoot = $HomeRoot }
        $raw = & $dispatcher @arguments 2>&1 | Out-String
        $ok = $?
        $payload = $null
        try { $payload = $raw | ConvertFrom-Json } catch { }
        if ($ok -and $null -ne $payload -and $payload.ok) {
            $raw.Trim()
            exit 0
        }
        if ($null -ne $payload -and $payload.mode -eq "agent-inline") {
            $raw.Trim()
            exit 3
        }
        throw "IMAGE_EDIT_FAILED|$($raw.Trim())"
    }

    "vectorize" {
        Assert-Required "InputImage" $InputImage
        Assert-Required "OutputSvg" $OutputSvg
        $dispatcher = Find-CellLctFile @("vectorize.ps1")
        $arguments = @{
            InputImage = $InputImage
            OutputSvg = $OutputSvg
        }
        if (-not [string]::IsNullOrWhiteSpace($Provider)) { $arguments.Provider = $Provider }
        if (-not [string]::IsNullOrWhiteSpace($AdapterPath)) { $arguments.AdapterPath = $AdapterPath }
        if (-not [string]::IsNullOrWhiteSpace($HomeRoot)) { $arguments.HomeRoot = $HomeRoot }
        if (-not [string]::IsNullOrWhiteSpace($SecretPath)) { $arguments.SecretPath = $SecretPath }
        & $dispatcher @arguments
        if (-not $?) { exit 1 }
        exit 0
    }

    "prepare" {
        Assert-Required "InputSvg" $InputSvg
        Assert-Required "WorkDir" $WorkDir
        $prepare = Resolve-RuntimeFile -Name "prepare_geometry_cache.py" -SubDir "python"
        $jobId = $JobId
        if ([string]::IsNullOrWhiteSpace($jobId)) {
            $jobId = ([IO.Path]::GetFileNameWithoutExtension($InputSvg) -replace '[^A-Za-z0-9_-]', '_').Trim('_')
        }
        & py -3 -X utf8 $prepare --input $InputSvg --output-dir $WorkDir --job-id $jobId --min-batch-size $MinBatchSize --max-batch-size $MaxBatchSize
        exit $LASTEXITCODE
    }

    "draw" {
        Assert-Required "InputSvg" $InputSvg
        Assert-Required "WorkDir" $WorkDir
        $runner = Find-CellLctFile @("run_cell_lct.ps1")
        $arguments = @{
            InputSvg = $InputSvg
            WorkDir = $WorkDir
            MinBatchSize = $MinBatchSize
            MaxBatchSize = $MaxBatchSize
        }
        if (-not [string]::IsNullOrWhiteSpace($OutputAi)) { $arguments.OutputAi = $OutputAi }
        if (-not [string]::IsNullOrWhiteSpace($OutputPng)) { $arguments.OutputPng = $OutputPng }
        if ($DryRun) { $arguments.DryRun = $true }
        & $runner @arguments
        if (-not $?) { exit 1 }
        exit 0
    }

    "reconstruct" {
        Assert-Required "InputImage" $InputImage
        Assert-Required "TextManifest" $TextManifest
        Assert-Required "OutputRoot" $OutputRoot
        $runner = Find-CellLctFile @("run_from_image.ps1")
        $arguments = @{
            InputImage = $InputImage
            TextManifest = $TextManifest
            OutputRoot = $OutputRoot
            MinBatchSize = $MinBatchSize
            MaxBatchSize = $MaxBatchSize
        }
        if ($DryRun) { $arguments.DryRun = $true }
        & $runner @arguments
        if (-not $?) { exit 1 }
        exit 0
    }
}
