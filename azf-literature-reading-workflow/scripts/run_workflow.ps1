param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$WorkflowArgs
)

$runtimeRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'runtime'))
if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot 'workflow\cli.py'))) {
    throw "Bundled literature workflow runtime not found: $runtimeRoot"
}

$exitCode = 0
Push-Location $runtimeRoot
try {
    & python -X utf8 -m workflow.cli @WorkflowArgs
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $exitCode