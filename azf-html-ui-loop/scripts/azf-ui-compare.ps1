[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [string]$OutputPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $ManifestPath)) { throw "变体清单不存在：$ManifestPath" }
$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($OutputPath)) { $OutputPath = Join-Path (Split-Path -Parent $ManifestPath) 'gallery.html' }
$galleryDir = Split-Path -Parent $OutputPath
$cards = foreach ($variant in @($manifest.variants)) {
    $variantPath = [string]$variant.path
    $desktop = Join-Path $variantPath 'desktop-1440x900.png'
    $mobile = Join-Path $variantPath 'mobile-390x844.png'
    $desktopUri = if (Test-Path -LiteralPath $desktop) { [System.Uri]::new((Resolve-Path -LiteralPath $desktop).Path).AbsoluteUri } else { '' }
    $mobileUri = if (Test-Path -LiteralPath $mobile) { [System.Uri]::new((Resolve-Path -LiteralPath $mobile).Path).AbsoluteUri } else { '' }
    "<article><h2>$([System.Net.WebUtility]::HtmlEncode($variant.variant_id))</h2><p>$([System.Net.WebUtility]::HtmlEncode($variant.generation_prompt))</p><div class='shots'><figure><figcaption>Desktop</figcaption><img src='$desktopUri' /></figure><figure><figcaption>Mobile</figcaption><img src='$mobileUri' /></figure></div></article>"
}
$html = @"
<!doctype html><html lang='en'><meta charset='utf-8'><title>AZF UI variants</title>
<style>body{font-family:system-ui,sans-serif;background:#f4f5f7;color:#18202a;margin:24px}article{background:white;border:1px solid #d8dde5;border-radius:14px;padding:16px;margin:0 0 24px}h2{margin:0 0 6px}.shots{display:grid;grid-template-columns:2fr 1fr;gap:16px}figure{margin:0}img{max-width:100%;border:1px solid #cbd2dc;border-radius:8px;background:#fff}figcaption{font-weight:600;margin:0 0 6px}@media(max-width:900px){.shots{grid-template-columns:1fr}}</style>
$($cards -join "`n")
</html>
"@
$parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $parent -Force | Out-Null
[System.IO.File]::WriteAllText($OutputPath, $html, [System.Text.UTF8Encoding]::new($false))
Write-Output $OutputPath
