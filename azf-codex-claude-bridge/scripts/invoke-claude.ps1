param(
  [ValidateSet("diff-review", "staged-review", "stdin-review", "question")]
  [string]$Mode = "diff-review",

  [string]$Prompt = "",

  [switch]$Json
)

$ErrorActionPreference = "Stop"

function Fail($message) {
  Write-Error $message
  exit 1
}

function Get-CommandText($command, $arguments) {
  $output = & $command @arguments
  if ($LASTEXITCODE -ne 0) {
    Fail "Command failed: $command $($arguments -join ' ')"
  }
  return ($output | Out-String)
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Fail "Claude Code CLI was not found on PATH. Install or log in to Claude Code, then retry."
}

$reviewPrompt = @"
Respond in Chinese. Perform a read-only review. Focus on:
- obvious bugs
- behavioral regressions
- data-loss risks
- concurrency or state-consistency issues
- security or permission risks
- missing critical tests

Do not ask to edit files directly. Organize the output as:
High-risk issues / Medium-risk issues / Low-risk suggestions / Assumptions Codex should verify.
"@

$content = ""

switch ($Mode) {
  "diff-review" {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
      Fail "git was not found on PATH."
    }
    $content = Get-CommandText "git" @("diff", "HEAD")
    if ([string]::IsNullOrWhiteSpace($content)) {
      $content = Get-CommandText "git" @("diff")
    }
    if ([string]::IsNullOrWhiteSpace($content)) {
      Fail "No git diff content found."
    }
    $Prompt = "$reviewPrompt`n`nReview this git diff:`n$content"
  }
  "staged-review" {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
      Fail "git was not found on PATH."
    }
    $content = Get-CommandText "git" @("diff", "--staged")
    if ([string]::IsNullOrWhiteSpace($content)) {
      Fail "No staged git diff content found."
    }
    $Prompt = "$reviewPrompt`n`nReview this staged git diff:`n$content"
  }
  "stdin-review" {
    $content = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($content)) {
      Fail "No stdin content received."
    }
    $Prompt = "$reviewPrompt`n`nReview this content:`n$content"
  }
  "question" {
    if ([string]::IsNullOrWhiteSpace($Prompt)) {
      Fail "Mode question requires -Prompt."
    }
  }
}

$claudeArgs = @("-p", $Prompt)
if ($Json) {
  $claudeArgs += @("--output-format", "json")
}

& claude @claudeArgs
if ($LASTEXITCODE -ne 0) {
  Fail "Claude CLI exited with code $LASTEXITCODE."
}
