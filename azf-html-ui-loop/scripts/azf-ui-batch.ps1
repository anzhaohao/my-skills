[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RepoPath,
    [Parameter(Mandatory = $true)][string]$RunDirectory,
    [ValidateRange(1, 20)][int]$VariantCount = 4,
    [string]$TargetPage = '',
    [string[]]$FunctionalRequirement = @(),
    [string[]]$GenerationPrompt = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-JsonNoBom {
    param([Parameter(Mandatory = $true)]$Value, [Parameter(Mandatory = $true)][string]$Path)
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 30), [System.Text.UTF8Encoding]::new($false))
}

if (-not (Test-Path -LiteralPath $RepoPath -PathType Container)) { throw "仓库目录不存在：$RepoPath" }
$RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path
if (-not (Test-Path -LiteralPath $RunDirectory)) { New-Item -ItemType Directory -Path $RunDirectory -Force | Out-Null }
$RunDirectory = (Resolve-Path -LiteralPath $RunDirectory).Path
$uiRoot = Join-Path $RunDirectory 'ui'
$variantRoot = Join-Path $uiRoot 'variants'
New-Item -ItemType Directory -Path $variantRoot -Force | Out-Null

$head = (& git -C $RepoPath rev-parse --verify HEAD 2>$null | Out-String).Trim()
$status = @(git -C $RepoPath status --short 2>$null)
if ($LASTEXITCODE -ne 0) { throw "目标目录不是 Git 仓库：$RepoPath" }

$variants = @()
for ($i = 1; $i -le $VariantCount; $i++) {
    $id = 'v{0:d2}' -f $i
    $path = Join-Path $variantRoot $id
    New-Item -ItemType Directory -Path $path -Force | Out-Null
    $prompt = if ($GenerationPrompt.Count -ge $i) { $GenerationPrompt[$i - 1] } else {
        "Generate a visibly distinct visual direction for $id. Preserve all functional requirements; explore layout, hierarchy, typography, color, background, cards, and motion without copying another variant."
    }
    $instruction = [ordered]@{
        variant_id = $id
        source_repo = $RepoPath
        source_baseline = [ordered]@{ head = $head; status_short = $status }
        target_page = $TargetPage
        functional_requirements = @($FunctionalRequirement)
        generation_prompt = $prompt
        canonical_worktree_write = $false
        note = 'This is an isolated candidate. Apply it to the canonical worktree only after explicit user selection.'
    }
    $instructionPath = Join-Path $path 'variant-input.json'
    Write-JsonNoBom -Value $instruction -Path $instructionPath
    $variants += [ordered]@{
        variant_id = $id
        path = $path
        generation_prompt = $prompt
        changed_files = @()
        screenshots = @()
    }
}

$manifest = [ordered]@{
    status = 'VARIANTS_READY'
    run_id = Split-Path -Leaf $RunDirectory
    source_repo = $RepoPath
    source_baseline = [ordered]@{ head = $head; status_short = $status }
    target_page = $TargetPage
    variant_count = $VariantCount
    target_viewports = @('1440x900', '390x844')
    functional_requirements = @($FunctionalRequirement)
    variants = @($variants)
    generated_at = (Get-Date).ToString('o')
}
$manifestPath = Join-Path $uiRoot 'variant-manifest.json'
$manifest | ConvertTo-Json -Depth 30 | ForEach-Object { [System.IO.File]::WriteAllText($manifestPath, $_, [System.Text.UTF8Encoding]::new($false)) }
$manifest | ConvertTo-Json -Depth 30
