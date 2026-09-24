#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$SecretPath = "",
    [string]$HomeRoot = ""
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "resolve-config.ps1") -HomeRoot $HomeRoot -SecretPath $SecretPath

$resolved = Resolve-CellLctSecretPath -Explicit $SecretPath -CellLctHome $cellLctHome -ConfigValues $config.values
$targetPath = $resolved.path
$secretDirectory = Split-Path -Parent $targetPath
New-Item -ItemType Directory -Force -Path $secretDirectory | Out-Null

$secret = Read-Host "Paste the Xiaomiao API key" -AsSecureString
$pointer = [IntPtr]::Zero
try {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    $plainText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    if ($plainText -notmatch '^img_live_[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$') {
        throw "The value does not match the Xiaomiao API-key format."
    }
}
finally {
    if ($pointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
    $plainText = $null
}

$cipherText = ConvertFrom-SecureString $secret
$temporaryPath = "$targetPath.tmp.$PID"
[IO.File]::WriteAllText($temporaryPath, $cipherText, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $targetPath -Force

$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $targetPath '/inheritance:r' '/grant:r' "${identity}:(F)" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "The key was encrypted, but its file permissions could not be restricted."
}

Write-Output "Xiaomiao API key stored with Windows DPAPI at $targetPath"
