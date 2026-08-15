[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SelectedVariantPath,
    [Parameter(Mandatory = $true)][string]$RepoPath,
    [switch]$ConfirmSelection
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $ConfirmSelection) { throw 'Applying a visual variant requires -ConfirmSelection after the user has selected one.' }
if (-not (Test-Path -LiteralPath $SelectedVariantPath -PathType Container)) { throw "Selected variant does not exist: $SelectedVariantPath" }
if (-not (Test-Path -LiteralPath $RepoPath -PathType Container)) { throw "Repository does not exist: $RepoPath" }
$SelectedVariantPath = (Get-Item -LiteralPath $SelectedVariantPath).FullName
$RepoPath = (Get-Item -LiteralPath $RepoPath).FullName
if (-not (& git -C $RepoPath rev-parse --show-toplevel 2>$null)) { throw "Target is not a Git repository: $RepoPath" }

function Get-RelativePath {
    param([string]$Base, [string]$Path)
    $baseFull = (Get-Item -LiteralPath $Base).FullName.TrimEnd('\')
    $pathFull = (Get-Item -LiteralPath $Path).FullName
    $prefix = $baseFull + '\'
    if ($pathFull.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $pathFull.Substring($prefix.Length).Replace('\', '/')
    }
    $baseUri = [System.Uri]::new($prefix)
    $pathUri = [System.Uri]::new($pathFull)
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace('\', '/')
}

$ignoredNames = @('variant-input.json', 'ui-check.json', 'desktop-1440x900.png', 'mobile-390x844.png')
$files = @(Get-ChildItem -LiteralPath $SelectedVariantPath -Recurse -File | Where-Object {
    $_.Name -notin $ignoredNames -and $_.FullName -notmatch '[\\/]\.git[\\/]' -and $_.FullName -notmatch '[\\/]screenshots?[\\/]'
})
if ($files.Count -eq 0) { throw 'Selected variant contains no applicable project files.' }

$conflicts = @()
foreach ($file in $files) {
    $relative = Get-RelativePath -Base $SelectedVariantPath -Path $file.FullName
    $destination = Join-Path $RepoPath $relative
    if (Test-Path -LiteralPath $destination) {
        $status = @(git -C $RepoPath status --short -- $relative 2>$null)
        if ($status.Count -gt 0) { $conflicts += $relative }
    }
}
if ($conflicts.Count -gt 0) { throw "Refusing to overwrite pre-existing user changes: $($conflicts -join ', ')" }

$applied = @()
foreach ($file in $files) {
    $relative = Get-RelativePath -Base $SelectedVariantPath -Path $file.FullName
    $destination = Join-Path $RepoPath $relative
    $parent = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    $applied += $relative
}
$manifest = [ordered]@{
    status = 'APPLIED_SELECTED_VARIANT'
    selected_variant = $SelectedVariantPath
    repo_path = $RepoPath
    files = @($applied)
    no_commit_or_push = $true
    applied_at = (Get-Date).ToString('o')
}
$evidence = Join-Path $SelectedVariantPath 'apply-manifest.json'
[System.IO.File]::WriteAllText($evidence, ($manifest | ConvertTo-Json -Depth 30), [System.Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 30
