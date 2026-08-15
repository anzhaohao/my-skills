[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Url,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$NodeCommand = 'node',
    [int]$WaitMilliseconds = 800,
    [switch]$AllowInsecureTls
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command $NodeCommand -ErrorAction SilentlyContinue)) {
    throw "Node.js command not found: $NodeCommand. Dependencies will not be installed automatically."
}
$scriptPath = Join-Path $PSScriptRoot 'azf-ui-capture.mjs'
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$args = @($scriptPath, '--url', $Url, '--out', (Resolve-Path -LiteralPath $OutputDirectory).Path, '--wait', [string]$WaitMilliseconds)
if ($AllowInsecureTls) { $args += '--allow-insecure-tls' }
& $NodeCommand @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
