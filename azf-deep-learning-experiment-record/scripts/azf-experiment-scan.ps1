[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunPath,

    [string]$OutputPath = '',
    [string]$StatePath = '',
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8Json {
    param([Parameter(Mandatory = $true)]$Value, [Parameter(Mandatory = $true)][string]$Path)
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $json = $Value | ConvertTo-Json -Depth 30
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.UTF8Encoding]::new($false))
}

function Read-JsonOrDefault {
    param([string]$Path, $Default)
    if (-not (Test-Path -LiteralPath $Path)) { return $Default }
    try {
        $raw = [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($false))
        if ([string]::IsNullOrWhiteSpace($raw)) { return $Default }
        return ($raw | ConvertFrom-Json)
    } catch { return $Default }
}

function Get-RelativePath {
    param([string]$Base, [string]$Path)
    $baseUri = [System.Uri]::new(($Base.TrimEnd('\') + '\'))
    $pathUri = [System.Uri]::new($Path)
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace('\', '/')
}

function Get-TextIfSmall {
    param([System.IO.FileInfo]$File)
    if ($File.Length -gt 5MB) { return '' }
    $textExtensions = @('.log', '.txt', '.md', '.json', '.yaml', '.yml', '.toml', '.csv', '.jsonl', '.ini', '.cfg')
    if ($textExtensions -notcontains $File.Extension.ToLowerInvariant()) { return '' }
    try { return [System.IO.File]::ReadAllText($File.FullName, [System.Text.UTF8Encoding]::new($false)) } catch { return '' }
}

if (-not (Test-Path -LiteralPath $RunPath -PathType Container)) { throw "实验目录不存在：$RunPath" }
$RunPath = (Get-Item -LiteralPath $RunPath).FullName
if ([string]::IsNullOrWhiteSpace($OutputPath)) { $OutputPath = Join-Path $RunPath 'experiment-evidence.json' }
if ([string]::IsNullOrWhiteSpace($StatePath)) { $StatePath = Join-Path $RunPath '.azf-experiment-state.json' }
$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$stateFullPath = [System.IO.Path]::GetFullPath($StatePath)

$oldState = Read-JsonOrDefault -Path $StatePath -Default ([ordered]@{ files = @() })
$oldFiles = @{}
foreach ($item in @($oldState.files)) { if ($item.path) { $oldFiles[[string]$item.path] = $item } }

$excluded = @('.git', 'node_modules', '__pycache__', '.venv', 'checkpoints')
$files = @(Get-ChildItem -LiteralPath $RunPath -Recurse -File | Where-Object {
    $relative = Get-RelativePath -Base $RunPath -Path $_.FullName
    $parts = $relative.Split('/')
    (@($parts | Where-Object { $excluded -contains $_ }).Count -eq 0) -and
    $_.Name -ne '.azf-experiment-state.json' -and $_.Name -ne 'experiment-evidence.json' -and
    $_.Name -notmatch '^(?:evidence|state).*\.json$' -and
    $_.FullName -ne $outputFullPath -and $_.FullName -ne $stateFullPath
})

$records = @()
$changed = @()
$texts = @()
foreach ($file in $files) {
    $relative = Get-RelativePath -Base $RunPath -Path $file.FullName
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $record = [ordered]@{
        path = $relative
        size = [int64]$file.Length
        last_modified = $file.LastWriteTimeUtc.ToString('o')
        sha256 = $hash
    }
    $records += [pscustomobject]$record
    $old = if ($oldFiles.ContainsKey($relative)) { $oldFiles[$relative] } else { $null }
    if ($Force -or $null -eq $old -or [string]$old.sha256 -ne $hash) { $changed += $relative }
    $text = Get-TextIfSmall -File $file
    if (-not [string]::IsNullOrWhiteSpace($text)) { $texts += $text }
}

$allText = ($texts -join "`n")
function First-Match { param([string]$Pattern)
    $m = [regex]::Match($allText, $Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if ($m.Success) { return $m.Groups[1].Value.Trim() }
    return $null
}

$configNames = @('config.yaml', 'config.yml', 'config.json', 'config.toml', 'manifest.md', 'manifest.json')
$missing = @($configNames | Where-Object { -not (Test-Path -LiteralPath (Join-Path $RunPath $_)) })
$evidence = [ordered]@{
    status = 'EVIDENCE_READY'
    experiment_id = Split-Path -Leaf $RunPath
    date = First-Match -Pattern '(?m)^(?:date|created_at)\s*[:=]\s*([^\r\n]+)'
    git_commit = First-Match -Pattern '(?m)(?:git[_ -]?commit|commit)\s*[:=]\s*([0-9a-f]{7,40})'
    dataset = First-Match -Pattern '(?m)^dataset\s*[:=]\s*([^\r\n]+)'
    model = First-Match -Pattern '(?m)^model\s*[:=]\s*([^\r\n]+)'
    config = First-Match -Pattern '(?m)^(?:config|configuration)\s*[:=]\s*([^\r\n]+)'
    device = First-Match -Pattern '(?m)^(?:device|gpu)\s*[:=]\s*([^\r\n]+)'
    start_time = First-Match -Pattern '(?m)^start[_ -]?time\s*[:=]\s*([^\r\n]+)'
    end_time = First-Match -Pattern '(?m)^end[_ -]?time\s*[:=]\s*([^\r\n]+)'
    best_metric = First-Match -Pattern '(?m)best[_ -]?(?:metric|score)\s*[:=]\s*([^\r\n]+)'
    final_metric = First-Match -Pattern '(?m)final[_ -]?(?:metric|score)\s*[:=]\s*([^\r\n]+)'
    error_summary = First-Match -Pattern '(?ms)error[_ -]?summary\s*[:=]\s*([^\r\n]+)'
    source_files = @($records | ForEach-Object { $_.path })
    file_hashes = @($records | ForEach-Object { [ordered]@{ path = $_.path; sha256 = $_.sha256 } })
    changed_files = @($changed)
    missing_artifacts = @($missing)
    processed_at = (Get-Date).ToString('o')
}

$newState = [ordered]@{ files = @($records); processed_at = $evidence.processed_at }
Write-Utf8Json -Value $evidence -Path $OutputPath
Write-Utf8Json -Value $newState -Path $StatePath
$evidence | ConvertTo-Json -Depth 30
