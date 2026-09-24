[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Task,

    [string]$RepoPath = (Get-Location).Path,

    [ValidateSet('auto', 'balanced', 'reviewed', 'dry-run', 'economy', 'quality')]
    [string]$Mode = 'balanced',

    [ValidateSet('auto', 'luna', 'terra', 'sol')]
    [string]$Executor = 'auto',

    [ValidateSet('auto', 'terra', 'sol')]
    [string]$Evaluator = 'auto',

    [ValidateSet('generic', 'experiment-record', 'html-ui')]
    [string]$TaskProfile = 'generic',

    [ValidateSet('auto', 'always', 'never')]
    [string]$PlannerMode = 'auto',

    [ValidateSet('auto', 'codex', 'claude-code', 'deepseek', 'kimi-qwen')]
    [string]$Harness = 'auto',

    [ValidateSet('claude-ds-v4-flash', 'claude-ds-v4-pro', 'claude-ds-flash', 'claude-ds-pro-hybrid', 'claude-ds-pro-all', 'claude-kimi', 'claude-qwen')]
    [string]$ExternalProfile = 'claude-ds-v4-flash',

    [ValidateSet('auto', 'low', 'medium', 'high', 'xhigh', 'max')]
    [string]$ExternalEffort = 'auto',

    [string]$DsFlashModel = 'deepseek-v4-flash',

    [string]$DsProModel = 'deepseek-v4-pro',

    [string]$KimiModel = 'k3-256k',

    [string]$QwenModel = 'qwen3.8-27b',

    [ValidateRange(1, 20)]
    [int]$VariantCount = 4,

    [string]$RunRoot = '',
    [string]$RunId = '',
    [ValidateRange(0, 4)]
    [int]$MaxReworkRounds = 4,
    [switch]$Approve
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SkillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PlanSchema = Join-Path $SkillRoot 'schemas\plan.schema.json'
$ExecutionSchema = Join-Path $SkillRoot 'schemas\execution.schema.json'
$EvaluationSchema = Join-Path $SkillRoot 'schemas\evaluation.schema.json'

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)]$Value,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $Value | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $Path -Encoding utf8
}

function Write-AgentEvent {
    param(
        [Parameter(Mandatory = $true)][string]$Role,
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$Status,
        [string]$Harness = 'codex',
        [string]$RequestedModel = '',
        [string]$ResolvedModel = '',
        [string]$RequestedEffort = '',
        [string]$ResolvedEffort = '',
        [string]$Reason = '',
        [string]$Summary = ''
    )
    if (-not $RunDirectory) { return }
    $event = [ordered]@{
        timestamp = (Get-Date).ToString('o')
        run_id = $RunId
        role = $Role
        stage = $Stage
        status = $Status
        harness = $Harness
        requested_model = $RequestedModel
        resolved_model = $ResolvedModel
        requested_effort = $RequestedEffort
        resolved_effort = $ResolvedEffort
        permission_mode = 'full-trust'
        route_reason = $Reason
        decision_summary = $Summary
    }
    $eventPath = Join-Path $RunDirectory 'agent-events.jsonl'
    ($event | ConvertTo-Json -Depth 20 -Compress) | Add-Content -LiteralPath $eventPath -Encoding utf8
    $modelText = if ([string]::IsNullOrWhiteSpace($ResolvedModel)) { $RequestedModel } else { $ResolvedModel }
    Write-Host ("[AGENT] role={0} stage={1} harness={2} model={3} effort={4} status={5}" -f $Role, $Stage, $Harness, $modelText, $RequestedEffort, $Status)
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "JSON 文件不存在：$Path"
    }
    $raw = Get-Content -LiteralPath $Path -Raw -Encoding utf8
    if ([string]::IsNullOrWhiteSpace($raw)) {
        throw "JSON 文件为空：$Path"
    }
    return ($raw | ConvertFrom-Json)
}

function Get-UsageNumber {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory = $true)][string[]]$Names
    )
    foreach ($name in $Names) {
        $pattern = '"' + [regex]::Escape($name) + '"\s*:\s*(\d+)'
        $match = [regex]::Match($Text, $pattern)
        if ($match.Success) {
            return [int64]$match.Groups[1].Value
        }
    }
    return $null
}

function Get-UsageSummary {
    param([Parameter(Mandatory = $true)][string]$EventsPath)
    $text = ''
    if (Test-Path -LiteralPath $EventsPath) {
        $raw = Get-Content -LiteralPath $EventsPath -Raw -Encoding utf8
        if ($null -ne $raw) { $text = [string]$raw }
    }
    [ordered]@{
        input_tokens = Get-UsageNumber -Text $text -Names @('input_tokens', 'prompt_tokens')
        cached_input_tokens = Get-UsageNumber -Text $text -Names @('cached_tokens', 'prompt_cache_hit_tokens')
        cache_write_tokens = Get-UsageNumber -Text $text -Names @('cache_write_tokens')
        cache_miss_tokens = Get-UsageNumber -Text $text -Names @('prompt_cache_miss_tokens')
        output_tokens = Get-UsageNumber -Text $text -Names @('output_tokens', 'completion_tokens')
        usage_source = if ([string]::IsNullOrWhiteSpace($text)) { 'unavailable' } else { 'codex_exec_json_events' }
    }
}

function Get-RouteHistorySummary {
    $records = @()
    if (-not (Test-Path -LiteralPath $RunRoot)) { return @() }
    foreach ($dir in @(Get-ChildItem -LiteralPath $RunRoot -Directory -ErrorAction SilentlyContinue)) {
        $reportPath = Join-Path $dir.FullName 'final-report.json'
        if (-not (Test-Path -LiteralPath $reportPath)) { continue }
        try {
            $report = Read-JsonFile -Path $reportPath
            if ($null -eq $report.route) { continue }
            $records += [pscustomobject]@{
                task_profile = [string]$report.task_profile
                harness = [string]$report.route.harness
                requested_model = [string]$report.route.requested_model
                status = [string]$report.status
                pass = ([string]$report.status -eq 'PASS')
            }
        } catch { continue }
    }
    $summary = @()
    foreach ($group in @($records | Group-Object task_profile, harness, requested_model)) {
        $items = @($group.Group)
        $passCount = @($items | Where-Object { $_.pass }).Count
        $summary += [ordered]@{
            task_profile = [string]$items[0].task_profile
            harness = [string]$items[0].harness
            requested_model = [string]$items[0].requested_model
            samples = $items.Count
            pass_count = $passCount
            pass_rate = if ($items.Count -gt 0) { [Math]::Round($passCount / $items.Count, 4) } else { $null }
            comparable_for_cost_route = ($items.Count -ge 20)
            cost_per_pass = 'unavailable_without_provider_cost'
        }
    }
    return $summary
}

function Get-RunUsageSummary {
    $stages = @()
    foreach ($file in @(Get-ChildItem -LiteralPath $RunDirectory -Filter '*.usage.json' -File -ErrorAction SilentlyContinue)) {
        try {
            $usage = Read-JsonFile -Path $file.FullName
            $stages += [ordered]@{ stage = $file.BaseName -replace '\.usage$', ''; usage = $usage }
        } catch { }
    }
    $sum = [ordered]@{}
    foreach ($field in @('input_tokens', 'cached_input_tokens', 'cache_write_tokens', 'cache_miss_tokens', 'output_tokens')) {
        $values = @($stages | ForEach-Object { $v = $_.usage.$field; if ($null -ne $v) { [int64]$v } })
        $sum[$field] = if ($values.Count -gt 0) { ($values | Measure-Object -Sum).Sum } else { $null }
    }
    [ordered]@{
        stages = $stages
        totals = $sum
        cost_status = 'provider_cost_not_available_in_controller'
        cost_per_pass = 'unavailable_without_provider_cost_and_final_pass_samples'
    }
}

function Get-ResolvedModelFromText {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory = $true)][string]$RequestedModel
    )
    try {
        $parsed = $Text | ConvertFrom-Json
        if ($parsed.PSObject.Properties.Name -contains 'modelUsage' -and $null -ne $parsed.modelUsage) {
            $usageModels = @($parsed.modelUsage.PSObject.Properties.Name | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
            if ($usageModels.Count -gt 0) { return [string]$usageModels[0] }
        }
    } catch { }
    foreach ($name in @('resolved_model', 'model_id', 'model')) {
        $pattern = '"' + $name + '"\s*:\s*"([^\"]+)"'
        $match = [regex]::Match($Text, $pattern)
        if ($match.Success -and -not [string]::IsNullOrWhiteSpace($match.Groups[1].Value)) {
            return $match.Groups[1].Value
        }
    }
    return 'unverified'
}

function Invoke-CodexStage {
    param(
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$Prompt,
        [Parameter(Mandatory = $true)][string]$Model,
        [Parameter(Mandatory = $true)][ValidateSet('low', 'medium', 'high', 'xhigh', 'max')][string]$Effort,
        [Parameter(Mandatory = $true)][ValidateSet('planner', 'executor', 'evaluator')][string]$Role,
        [Parameter(Mandatory = $true)][string]$SchemaPath,
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [Parameter(Mandatory = $true)][string]$RunDirectory
    )

    $promptPath = Join-Path $RunDirectory ('{0}.prompt.txt' -f $Stage)
    $eventsPath = Join-Path $RunDirectory ('{0}.events.jsonl' -f $Stage)
    $errorPath = Join-Path $RunDirectory ('{0}.stderr.log' -f $Stage)
    Set-Content -LiteralPath $promptPath -Value $Prompt -Encoding utf8

    $args = @(
        'exec', '--ephemeral', '--json',
        # API-key 登录不提供 ChatGPT 会话令牌。控制器只依赖本地 Skill，
        # 因此关闭插件初始化，避免访问需要官方会话的远程插件目录。
        '--disable', 'plugins',
        # 控制器已经串行管理 Planner/Executor/Evaluator；关闭阶段内部协作，
        # 避免模型在结构化输出前启动不可审计的额外等待或子代理。
        '--disable', 'multi_agent',
        '--disable', 'multi_agent_v2',
        '-m', $Model,
        '-c', ('model_reasoning_effort="{0}"' -f $Effort),
        '--dangerously-bypass-approvals-and-sandbox',
        '-C', $RepoPath,
        '--output-schema', $SchemaPath,
        '-o', $OutputPath,
        '-'
    )

    Write-AgentEvent -Role $Role -Stage $Stage -Status 'STARTED' -Harness 'codex' -RequestedModel $Model -RequestedEffort $Effort -Reason 'controller_route' -Summary '阶段已启动；权限为 full-trust，职责边界由提示词和事后审计约束。'

    # Codex 会把诊断、兼容性提示和 MCP 收尾警告写到 stderr，即使阶段成功。
    # 暂时允许原生命令写 stderr，随后仍以退出码和结构化输出判定成功与否。
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $Prompt | & codex @args 1> $eventsPath 2> $errorPath
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        $errorText = if (Test-Path -LiteralPath $errorPath) {
            (Get-Content -LiteralPath $errorPath -Raw -Encoding utf8).Trim()
        } else { '' }
        throw "$Stage 阶段失败，退出码=$exitCode。$errorText"
    }
    if (-not (Test-Path -LiteralPath $OutputPath)) {
        throw "$Stage 没有产生结构化输出：$OutputPath"
    }
    $usage = Get-UsageSummary -EventsPath $eventsPath
    Write-JsonFile -Value $usage -Path (Join-Path $RunDirectory ('{0}.usage.json' -f $Stage))
    $eventsText = if (Test-Path -LiteralPath $eventsPath) { Get-Content -LiteralPath $eventsPath -Raw -Encoding utf8 } else { '' }
    $resolvedModel = Get-ResolvedModelFromText -Text ([string]$eventsText) -RequestedModel $Model
    Write-JsonFile -Value ([ordered]@{
        requested_model = $Model
        resolved_model = $resolvedModel
        requested_effort = $Effort
        resolved_effort = if ($resolvedModel -eq 'unverified') { 'unverified' } else { $Effort }
        harness = 'codex'
    }) -Path (Join-Path $RunDirectory ('{0}.resolution.json' -f $Stage))
    Write-AgentEvent -Role $Role -Stage $Stage -Status 'COMPLETE' -Harness 'codex' -RequestedModel $Model -ResolvedModel $resolvedModel -RequestedEffort $Effort -ResolvedEffort $Effort -Reason 'stage_complete' -Summary '结构化输出已写入，退出码为 0。'
}

function Get-ExternalProfileSpec {
    param([Parameter(Mandatory = $true)][string]$Profile)
    switch ($Profile) {
        { $_ -in @('claude-ds-v4-flash', 'claude-ds-flash') } {
            return [pscustomobject][ordered]@{
                profile = 'claude-ds-v4-flash'
                requested_model = $DsFlashModel
                capability_tier = 'cheap'
            }
        }
        { $_ -in @('claude-ds-v4-pro', 'claude-ds-pro-hybrid', 'claude-ds-pro-all') } {
            return [pscustomobject][ordered]@{
                profile = 'claude-ds-v4-pro'
                requested_model = $DsProModel
                capability_tier = 'pro'
            }
        }
        'claude-kimi' {
            return [pscustomobject][ordered]@{
                profile = 'claude-kimi'
                requested_model = $KimiModel
                capability_tier = 'pro'
            }
        }
        'claude-qwen' {
            return [pscustomobject][ordered]@{
                profile = 'claude-qwen'
                requested_model = $QwenModel
                capability_tier = 'cheap'
            }
        }
        default { throw "未知 Claude Code profile：$Profile" }
    }
}

function Resolve-ExternalEffort {
    param(
        [Parameter(Mandatory = $true)]$Plan,
        [Parameter(Mandatory = $true)][string]$Profile,
        [switch]$Retry
    )
    if ($ExternalEffort -ne 'auto') { return $ExternalEffort }
    $spec = Get-ExternalProfileSpec -Profile $Profile
    if ($spec.capability_tier -eq 'pro' -or $Retry) { return 'high' }
    $score = [int]$Plan.complexity_score
    if ($score -le 2) { return 'low' }
    if ($score -le 5) { return 'medium' }
    return 'high'
}

function ConvertFrom-ClaudeResult {
    param(
        [Parameter(Mandatory = $true)][string]$RawText,
        [string]$StatusField = 'status',
        [string]$ExpectedStatus = ''
    )
    $wrapper = $null
    try { $wrapper = $RawText | ConvertFrom-Json } catch { $wrapper = $null }
    $candidate = $null
    if ($null -ne $wrapper) {
        if ($wrapper.PSObject.Properties.Name -contains 'structured_output' -and $null -ne $wrapper.structured_output) {
            $candidate = $wrapper.structured_output
        } elseif ($wrapper.PSObject.Properties.Name -contains 'result') {
            $candidate = $wrapper.result
        } else {
            $candidate = $wrapper
        }
    } else {
        $candidate = $RawText
    }
    if ($candidate -is [string]) {
        $text = ([string]$candidate).Trim()
        $text = [regex]::Replace($text, '^```(?:json)?\s*', '', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        $text = [regex]::Replace($text, '\s*```$', '')
        try { $candidate = $text | ConvertFrom-Json } catch {
            $start = $text.IndexOf('{')
            $end = $text.LastIndexOf('}')
            if ($start -lt 0 -or $end -le $start) { throw 'Claude Code 输出中没有可解析的 JSON 对象。' }
            $candidate = $text.Substring($start, $end - $start + 1) | ConvertFrom-Json
        }
    }
    if ($null -eq $candidate -or -not ($candidate.PSObject.Properties.Name -contains $StatusField)) {
        throw "Claude Code 结构化结果缺少 $StatusField。"
    }
    if (-not [string]::IsNullOrWhiteSpace($ExpectedStatus) -and [string]$candidate.$StatusField -ne $ExpectedStatus) {
        throw "Claude Code $StatusField=$($candidate.$StatusField)，预期为 $ExpectedStatus。"
    }
    return $candidate
}

function Invoke-ClaudeCodeStage {
    param(
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$Prompt,
        [Parameter(Mandatory = $true)][string]$Model,
        [Parameter(Mandatory = $true)][ValidateSet('auto', 'low', 'medium', 'high', 'xhigh', 'max')][AllowEmptyString()][string]$Effort,
        [Parameter(Mandatory = $true)][string]$SchemaPath,
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [ValidateSet('planner', 'executor', 'evaluator')][string]$Role = 'executor',
        [string]$StatusField = 'status',
        [string]$ExpectedStatus = '',
        [string]$HarnessLabel = 'claude-code'
    )
    if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
        throw '找不到 claude 命令，无法运行 Claude Code adapter。'
    }
    $promptPath = Join-Path $RunDirectory ('{0}.prompt.txt' -f $Stage)
    $stdoutPath = Join-Path $RunDirectory ('{0}.claude.json' -f $Stage)
    $errorPath = Join-Path $RunDirectory ('{0}.stderr.log' -f $Stage)
    Set-Content -LiteralPath $promptPath -Value $Prompt -Encoding utf8
    $schemaObject = Get-Content -LiteralPath $SchemaPath -Raw -Encoding utf8 | ConvertFrom-Json
    # Claude Code's structured-output validator does not implement the local
    # draft-2020-12 URI; the schema constraints themselves remain unchanged.
    if ($schemaObject.PSObject.Properties.Name -contains '$schema') {
        $schemaObject.PSObject.Properties.Remove('$schema')
    }
    $schemaRaw = $schemaObject | ConvertTo-Json -Depth 30 -Compress
    # Windows PowerShell strips embedded quotes when forwarding JSON to a native
    # executable. Preserve them for Claude Code's --json-schema parser.
    $schemaArg = '"' + $schemaRaw.Replace('"', '\"') + '"'
    # effort=auto（或空）表示思维强度交给模型自决：不向 CLI 传 --effort。
    if ([string]::IsNullOrWhiteSpace($Effort) -or $Effort -eq 'auto') {
        $effortLabel = 'auto'
        $effortArgs = @()
    } else {
        $effortLabel = $Effort
        $effortArgs = @('--effort', $Effort)
    }
    $args = @('--print', '--output-format', 'json', '--json-schema', $schemaArg, '--model', $Model) + $effortArgs + @(
        '--permission-mode', 'bypassPermissions',
        '--dangerously-skip-permissions',
        '--no-session-persistence'
    )
    Write-AgentEvent -Role $Role -Stage $Stage -Status 'STARTED' -Harness $HarnessLabel -RequestedModel $Model -RequestedEffort $effortLabel -Reason 'controller_route' -Summary 'Claude Code 非交互 adapter 已自动启动；权限为 full-trust。'
    $previousErrorActionPreference = $ErrorActionPreference
    Push-Location -LiteralPath $RepoPath
    try {
        $ErrorActionPreference = 'Continue'
        $Prompt | & claude @args 1> $stdoutPath 2> $errorPath
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        $errorText = if (Test-Path -LiteralPath $errorPath) { Get-Content -LiteralPath $errorPath -Raw -Encoding utf8 } else { '' }
        throw "Claude Code 阶段失败，退出码=$exitCode。$errorText"
    }
    $raw = Get-Content -LiteralPath $stdoutPath -Raw -Encoding utf8
    $result = ConvertFrom-ClaudeResult -RawText $raw -StatusField $StatusField -ExpectedStatus $ExpectedStatus
    Write-JsonFile -Value $result -Path $OutputPath
    $resolvedModel = Get-ResolvedModelFromText -Text $raw -RequestedModel $Model
    $usage = Get-UsageSummary -EventsPath $stdoutPath
    $usage.usage_source = 'claude_code_json_result'
    Write-JsonFile -Value $usage -Path (Join-Path $RunDirectory ('{0}.usage.json' -f $Stage))
    Write-JsonFile -Value ([ordered]@{
        requested_model = $Model
        resolved_model = $resolvedModel
        requested_effort = $effortLabel
        resolved_effort = if ($resolvedModel -eq 'unverified') { 'unverified' } else { $effortLabel }
        harness = $HarnessLabel
    }) -Path (Join-Path $RunDirectory ('{0}.resolution.json' -f $Stage))
    Write-AgentEvent -Role $Role -Stage $Stage -Status 'COMPLETE' -Harness $HarnessLabel -RequestedModel $Model -ResolvedModel $resolvedModel -RequestedEffort $effortLabel -ResolvedEffort $(if ($resolvedModel -eq 'unverified') { 'unverified' } else { $effortLabel }) -Reason 'stage_complete' -Summary 'Claude Code 返回了可解析的结构化执行结果。'
}

function Get-ModelName {
    param([ValidateSet('luna', 'terra', 'sol')][string]$Tier)
    switch ($Tier) {
        'luna' { return 'gpt-5.6-luna' }
        'terra' { return 'gpt-5.6-terra' }
        'sol' { return 'gpt-5.6-sol' }
    }
}

function Get-HashBucket {
    param([Parameter(Mandatory = $true)][string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        $hash = $sha.ComputeHash($bytes)
        return [int]($hash[0] % 100)
    }
    finally { $sha.Dispose() }
}

function Resolve-InitialRoute {
    param([Parameter(Mandatory = $true)]$Plan)
    $score = [int]$Plan.complexity_score
    $highRisk = @('high', 'critical') -contains [string]$Plan.risk_level
    if ($Harness -eq 'claude-code') {
        $spec = Get-ExternalProfileSpec -Profile $ExternalProfile
        return [pscustomobject][ordered]@{
            harness = 'claude-code'
            executor_tier = if ($spec.capability_tier -eq 'pro') { 'terra' } else { 'luna' }
            external_profile = $spec.profile
            requested_effort = Resolve-ExternalEffort -Plan $Plan -Profile $ExternalProfile
            route_stage = 0
            route_reason = 'explicit_claude_code'
        }
    }
    if ($Harness -eq 'deepseek') {
        # 全 DS 链路：规划/评估走 DS Pro，执行走 DS Flash；硬风险或高复杂度执行升到 DS Pro。
        # 纯 DeepSeek 模式不上 Sol/GPT，除非显式切换 harness=codex。
        $dsProfile = if ($Mode -eq 'quality' -or $highRisk -or $score -ge 6) { 'claude-ds-v4-pro' } else { 'claude-ds-v4-flash' }
        $dsSpec = Get-ExternalProfileSpec -Profile $dsProfile
        return [pscustomobject][ordered]@{
            harness = 'deepseek'
            executor_tier = if ($dsSpec.capability_tier -eq 'pro') { 'terra' } else { 'luna' }
            external_profile = $dsProfile
            requested_effort = Resolve-ExternalEffort -Plan $Plan -Profile $dsProfile
            route_stage = 0
            route_reason = 'explicit_deepseek_harness'
        }
    }
    if ($Harness -eq 'kimi-qwen') {
        # Kimi + Qwen 链路：Planner/Evaluator 走 Kimi（$KimiModel），Executor 固定 Qwen（$QwenModel）。
        # 思维强度默认交给模型自决（auto）；可用 -ExternalEffort 显式覆盖。
        return [pscustomobject][ordered]@{
            harness = 'kimi-qwen'
            executor_tier = 'luna'
            external_profile = 'claude-qwen'
            requested_effort = $ExternalEffort
            route_stage = 0
            route_reason = 'explicit_kimi_qwen_harness'
        }
    }
    if ($Harness -eq 'codex') {
        $nativeTier = Resolve-ExecutorTier -Plan $Plan
        return [pscustomobject][ordered]@{
            harness = 'codex'
            executor_tier = $nativeTier
            external_profile = $null
            requested_effort = if ($nativeTier -eq 'luna') { 'medium' } else { 'high' }
            route_stage = 0
            route_reason = 'explicit_codex_harness'
        }
    }
    if ($Executor -ne 'auto') {
        return [pscustomobject][ordered]@{
            harness = 'codex'
            executor_tier = $Executor
            external_profile = $null
            requested_effort = if ($Executor -eq 'luna') { 'medium' } else { 'high' }
            route_stage = 0
            route_reason = 'explicit_executor'
        }
    }
    if ($Mode -eq 'quality' -or $highRisk -or $score -ge 8) {
        return [pscustomobject][ordered]@{
            harness = 'codex'; executor_tier = 'sol'; external_profile = $null
            requested_effort = 'high'; route_stage = 0; route_reason = 'high_risk_or_quality'
        }
    }
    if ($score -ge 6) {
        return [pscustomobject][ordered]@{
            harness = 'codex'; executor_tier = 'terra'; external_profile = $null
            requested_effort = 'high'; route_stage = 0; route_reason = 'medium_execution_complexity'
        }
    }
    $bucket = Get-HashBucket -Text ($RunId + '|' + $TaskProfile + '|' + $Task)
    if ($bucket -lt 60) {
        return [pscustomobject][ordered]@{
            harness = 'claude-code'; executor_tier = 'luna'; external_profile = 'claude-ds-v4-flash'
            requested_effort = Resolve-ExternalEffort -Plan $Plan -Profile 'claude-ds-v4-flash'
            route_stage = 0; route_reason = 'weighted_cheap_pool_ds_60'
        }
    }
    return [pscustomobject][ordered]@{
        harness = 'codex'; executor_tier = 'luna'; external_profile = $null
        requested_effort = 'medium'; route_stage = 0; route_reason = 'weighted_cheap_pool_luna_40'
    }
}

function Get-NextRoute {
    param([Parameter(Mandatory = $true)]$CurrentRoute)
    $stage = [int]$CurrentRoute.route_stage
    $harness = [string]$CurrentRoute.harness
    $profile = [string]$CurrentRoute.external_profile
    if ($harness -eq 'deepseek') {
        # 全 DS 升级链：Flash → Flash 定向重试 → Pro。纯 DeepSeek 模式不升级到 Sol/GPT。
        if ($profile -eq 'claude-ds-v4-flash') {
            if ($stage -eq 0) {
                return [pscustomobject][ordered]@{ harness = 'deepseek'; executor_tier = 'luna'; external_profile = 'claude-ds-v4-flash'; requested_effort = 'high'; route_stage = 1; route_reason = 'same_ds_flash_targeted_retry' }
            }
            return [pscustomobject][ordered]@{ harness = 'deepseek'; executor_tier = 'terra'; external_profile = 'claude-ds-v4-pro'; requested_effort = 'high'; route_stage = 3; route_reason = 'upgrade_to_ds_v4_pro' }
        }
        return [pscustomobject][ordered]@{ harness = 'deepseek'; executor_tier = 'terra'; external_profile = 'claude-ds-v4-pro'; requested_effort = 'high'; route_stage = 3; route_reason = 'ds_pro_final_rework' }
    }
    if ($harness -eq 'kimi-qwen') {
        # Kimi + Qwen 升级链：Executor 固定 Qwen，只做一次同档定向重试（effort 仍 auto），不升级 GPT。
        if ($stage -eq 0) {
            return [pscustomobject][ordered]@{ harness = 'kimi-qwen'; executor_tier = 'luna'; external_profile = 'claude-qwen'; requested_effort = 'auto'; route_stage = 1; route_reason = 'same_qwen_targeted_retry' }
        }
        return [pscustomobject][ordered]@{ harness = 'kimi-qwen'; executor_tier = 'luna'; external_profile = 'claude-qwen'; requested_effort = 'auto'; route_stage = 3; route_reason = 'qwen_final_rework' }
    }
    if ($harness -eq 'claude-code' -and $profile -eq 'claude-ds-v4-flash') {
        if ($stage -eq 0) {
            return [pscustomobject][ordered]@{ harness = 'claude-code'; executor_tier = 'luna'; external_profile = 'claude-ds-v4-flash'; requested_effort = 'high'; route_stage = 1; route_reason = 'same_ds_flash_targeted_retry' }
        }
        if ($stage -eq 1) {
            return [pscustomobject][ordered]@{ harness = 'codex'; executor_tier = 'terra'; external_profile = $null; requested_effort = 'high'; route_stage = 2; route_reason = 'upgrade_to_terra' }
        }
        return [pscustomobject][ordered]@{ harness = 'claude-code'; executor_tier = 'terra'; external_profile = 'claude-ds-v4-pro'; requested_effort = 'high'; route_stage = 3; route_reason = 'upgrade_to_ds_v4_pro' }
    }
    if ($harness -eq 'codex' -and $CurrentRoute.executor_tier -eq 'luna') {
        if ($stage -eq 0) {
            return [pscustomobject][ordered]@{ harness = 'codex'; executor_tier = 'luna'; external_profile = $null; requested_effort = 'medium'; route_stage = 1; route_reason = 'same_luna_targeted_retry' }
        }
        if ($stage -eq 1) {
            return [pscustomobject][ordered]@{ harness = 'codex'; executor_tier = 'terra'; external_profile = $null; requested_effort = 'high'; route_stage = 2; route_reason = 'upgrade_to_terra' }
        }
        return [pscustomobject][ordered]@{ harness = 'claude-code'; executor_tier = 'terra'; external_profile = 'claude-ds-v4-pro'; requested_effort = 'high'; route_stage = 3; route_reason = 'upgrade_to_ds_v4_pro' }
    }
    if ($harness -eq 'codex' -and $CurrentRoute.executor_tier -eq 'terra') {
        return [pscustomobject][ordered]@{ harness = 'claude-code'; executor_tier = 'terra'; external_profile = 'claude-ds-v4-pro'; requested_effort = 'high'; route_stage = 3; route_reason = 'upgrade_to_ds_v4_pro' }
    }
    if ($harness -eq 'claude-code' -and $profile -eq 'claude-ds-v4-pro') {
        return [pscustomobject][ordered]@{ harness = 'codex'; executor_tier = 'sol'; external_profile = $null; requested_effort = 'high'; route_stage = 4; route_reason = 'upgrade_to_sol_last_resort' }
    }
    return [pscustomobject][ordered]@{ harness = 'codex'; executor_tier = 'sol'; external_profile = $null; requested_effort = 'high'; route_stage = 4; route_reason = 'upgrade_to_sol_last_resort' }
}

function Resolve-ExecutorTier {
    param([Parameter(Mandatory = $true)]$Plan)

    $risk = [string]$Plan.risk_level
    $score = [int]$Plan.complexity_score
    $highRisk = @('high', 'critical') -contains $risk

    if ($Executor -ne 'auto') {
        if ($highRisk -and $Executor -ne 'sol') {
            throw "显式 Executor=$Executor 不能处理 $risk 风险任务；请使用 executor=sol 或取消显式限制。"
        }
        return $Executor
    }
    if ($Mode -eq 'quality' -or $highRisk -or $score -ge 8) {
        return 'sol'
    }
    if ($Mode -eq 'economy' -or ($score -le 2 -and [bool]$Plan.mechanical -and $risk -eq 'low')) {
        return 'luna'
    }
    return 'terra'
}

function Resolve-EvaluatorTier {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('luna', 'terra', 'sol')][string]$ExecutorTier,
        [Parameter(Mandatory = $true)]$Plan
    )
    if ($Evaluator -ne 'auto') {
        if ($ExecutorTier -eq 'sol' -and $Evaluator -ne 'sol') {
            throw 'Sol Executor 必须使用 Sol Evaluator，除非显式路由策略被修改。'
        }
        return $Evaluator
    }
    if ($Mode -eq 'quality' -or $ExecutorTier -eq 'sol' -or @('high', 'critical') -contains [string]$Plan.risk_level) {
        return 'sol'
    }
    return 'terra'
}

function Get-Baseline {
    $head = ''
    try {
        $headCandidate = (& git -C $RepoPath rev-parse --verify HEAD 2>$null | Out-String).Trim()
        if ($LASTEXITCODE -eq 0) { $head = $headCandidate }
    } catch { $head = '' }
    $branch = (& git -C $RepoPath branch --show-current 2>$null | Out-String).Trim()
    $status = @(git -C $RepoPath status --short 2>$null)
    $trackedDiff = (& git -c core.safecrlf=false -C $RepoPath diff --no-ext-diff --stat 2>$null) -join [Environment]::NewLine
    $stagedDiff = (& git -c core.safecrlf=false -C $RepoPath diff --cached --stat 2>$null) -join [Environment]::NewLine
    [ordered]@{
        captured_at = (Get-Date).ToString('o')
        repo_path = $RepoPath
        branch = $branch
        head = $head
        status_short = @($status)
        tracked_diff_stat = $trackedDiff
        staged_diff_stat = $stagedDiff
    }
}

function Write-RouteRecord {
    param(
        [Parameter(Mandatory = $true)]$Plan,
        [Parameter(Mandatory = $true)][string]$ExecutorTier,
        [Parameter(Mandatory = $true)][string]$EvaluatorTier,
        [Parameter(Mandatory = $true)][int]$Round,
        [Parameter(Mandatory = $true)]$RouteState
    )
    $effectiveHarness = [string]$RouteState.harness
    $isExternal = $effectiveHarness -in @('claude-code', 'deepseek', 'kimi-qwen')
    $profile = if ($isExternal) { [string]$RouteState.external_profile } else { $null }
    $executorModel = if ($isExternal) { (Get-ExternalProfileSpec -Profile $profile).requested_model } else { Get-ModelName -Tier $ExecutorTier }
    $resolvedModel = 'pending_stage_resolution'
    $requestedEffort = [string]$RouteState.requested_effort
    $record = [ordered]@{
        run_id = $RunId
        round = $Round
        planner_profile = if ($PlannerInvoked) { if ($Harness -eq 'deepseek') { 'azf_ds_v4_pro_planner' } elseif ($Harness -eq 'kimi-qwen') { 'azf_kimi_planner' } else { ('azf_{0}_planner' -f $PlannerTier) } } else { 'deterministic_preflight' }
        planner_model = if ($Harness -eq 'deepseek') { $DsProModel } elseif ($Harness -eq 'kimi-qwen') { $KimiModel } elseif ($PlannerTier -eq 'sol') { 'gpt-5.6-sol' } else { 'gpt-5.6-terra' }
        planner_effort = if ($PlannerInvoked) { if ($Harness -eq 'deepseek') { if ($PlannerTier -eq 'sol') { 'high' } else { 'medium' } } elseif ($Harness -eq 'kimi-qwen') { $ExternalEffort } else { 'high' } } else { 'not_invoked' }
        planner_invoked = [bool]$PlannerInvoked
        task_profile = $TaskProfile
        harness = $effectiveHarness
        external_profile = $profile
        complexity_score = [int]$Plan.complexity_score
        risk_level = [string]$Plan.risk_level
        mechanical = [bool]$Plan.mechanical
        executor_profile = if ($isExternal) { $profile } else { ('azf_{0}_executor' -f $ExecutorTier) }
        executor_model = $executorModel
        executor_effort = $requestedEffort
        evaluator_profile = if ($Harness -eq 'deepseek') { 'azf_ds_v4_pro_evaluator' } elseif ($Harness -eq 'kimi-qwen') { 'azf_kimi_evaluator' } elseif ($effectiveHarness -eq 'claude-code') { 'fresh_codex_evaluator' } else { ('azf_{0}_evaluator' -f $EvaluatorTier) }
        evaluator_model = if ($Harness -eq 'deepseek') { $DsProModel } elseif ($Harness -eq 'kimi-qwen') { $KimiModel } else { Get-ModelName -Tier $EvaluatorTier }
        evaluator_effort = if ($Harness -eq 'kimi-qwen') { $ExternalEffort } else { 'high' }
        requested_model = $executorModel
        resolved_model = $resolvedModel
        requested_effort = $requestedEffort
        resolved_effort = 'pending_stage_resolution'
        permission_mode = 'full-trust'
        approval_status = 'auto_full_trust'
        route_stage = [int]$RouteState.route_stage
        route_reason = [string]$RouteState.route_reason
        execution_order = @('ds-v4-flash', 'luna', 'terra', 'ds-v4-pro', 'sol')
        variant_count = if ($TaskProfile -eq 'html-ui') { $VariantCount } else { 0 }
        mode = $Mode
        generated_at = (Get-Date).ToString('o')
    }
    Write-JsonFile -Value $record -Path (Join-Path $RunDirectory ('route-r{0}.json' -f $Round))
    return $record
}

function Invoke-Planner {
    param([string]$AdditionalContext = '')
    $baselineText = Get-Content -LiteralPath (Join-Path $RunDirectory 'baseline.json') -Raw -Encoding utf8
    $prompt = @"
你是 azf_${PlannerTier}_planner。只读分析，不修改文件，不提交、不暂存、不推送。

原始任务：
$Task

任务档案：$TaskProfile
变体数量（仅 html-ui）：$VariantCount

执行前基线：
$baselineText

工作要求：
1. 读取项目规则、AGENTS.md、相关代码和测试入口。
2. 评估需求歧义、修改范围、技术风险、推理深度、验证复杂度，每项 0～2 分。
3. 标记 risk_level 和 mechanical；安全、权限、迁移、并发、核心架构或不可逆操作必须按高风险处理。
4. 只制定最小充分修改计划，不编辑文件。
5. 按仓库实际情况给出测试命令和可验证的验收标准。
6. selected_executor/selected_evaluator 只提供建议；外部控制器会再次按策略核对路由。
7. html-ui 任务不要求设计契约；如果需要多方案，保持功能约束不变并探索差异明显的视觉方向。
8. steps 之外必须尽量生成原子 work_items；每个 work_item 要包含 id、objective、target_files、context_files、allowed_actions、forbidden_actions、acceptance_checks、required_evidence 和 failure_policy。

额外上下文：
$AdditionalContext

    只输出符合所给 JSON Schema 的 JSON，status 必须为 PLAN_READY。Schema 中的所有字段都必须输出；没有内容的数组输出 []，没有内容的字符串输出空字符串，planner_invoked 和 variant_count 也必须填写。
"@
    $path = Join-Path $RunDirectory 'plan.json'
    if ($Harness -eq 'deepseek') {
        $plannerEffort = if ($PlannerTier -eq 'sol') { 'high' } else { 'medium' }
        Invoke-ClaudeCodeStage -Stage 'planner' -Prompt $prompt -Model $DsProModel -Effort $plannerEffort -SchemaPath $PlanSchema -OutputPath $path -RunDirectory $RunDirectory -Role 'planner' -StatusField 'status' -ExpectedStatus 'PLAN_READY' -HarnessLabel 'deepseek'
    } elseif ($Harness -eq 'kimi-qwen') {
        # Kimi 规划：思维强度交给模型自决（effort auto，可被 -ExternalEffort 覆盖）。
        Invoke-ClaudeCodeStage -Stage 'planner' -Prompt $prompt -Model $KimiModel -Effort $ExternalEffort -SchemaPath $PlanSchema -OutputPath $path -RunDirectory $RunDirectory -Role 'planner' -StatusField 'status' -ExpectedStatus 'PLAN_READY' -HarnessLabel 'kimi-qwen'
    } else {
        $plannerModel = if ($PlannerTier -eq 'sol') { 'gpt-5.6-sol' } else { 'gpt-5.6-terra' }
        Invoke-CodexStage -Stage 'planner' -Prompt $prompt -Model $plannerModel -Effort 'high' -Role 'planner' -SchemaPath $PlanSchema -OutputPath $path -RunDirectory $RunDirectory
    }
    return (Read-JsonFile -Path $path)
}

function Test-HighRiskTask {
    $riskPattern = '安全|权限|认证|授权|迁移|并发|事务|数据库|生产|部署|不可逆|架构|公开 API|public API|security|authentication|authorization|migration|concurrency|transaction|production|deployment|irreversible|architecture'
    return [regex]::IsMatch($Task, $riskPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
}

function Should-InvokePlanner {
    if ($PlannerMode -eq 'always') { $script:PlannerTier = 'sol'; return $true }
    if ($PlannerMode -eq 'never') {
        if (Test-HighRiskTask) { throw 'planner_mode=never 不能用于检测到的高风险任务。请改用 planner_mode=auto 或 always。' }
        return $false
    }
    if ($Mode -eq 'quality' -or (Test-HighRiskTask)) { $script:PlannerTier = 'sol'; return $true }
    if ([regex]::IsMatch($Task, '跨模块|架构|接口设计|重构|多个服务|不确定|复杂|分析|比较|诊断|根因|cross[- ]module|architecture|refactor|ambiguous|diagnose|root cause', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) { $script:PlannerTier = 'terra'; return $true }
    if ($TaskProfile -eq 'html-ui' -and $VariantCount -gt 12) { $script:PlannerTier = 'terra'; return $true }
    if ($TaskProfile -eq 'experiment-record' -and [regex]::IsMatch($Task, '矛盾|比较|诊断|失败原因|下一轮|contradiction|compare|diagnose|failure', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) { $script:PlannerTier = 'terra'; return $true }
    return $false
}

function Invoke-DeterministicPlan {
    $highRisk = Test-HighRiskTask
    $score = 2
    $risk = 'low'
    $mechanical = $true
    $executor = 'luna'
    $evaluator = 'terra'
    $steps = @()
    $affected = @()
    $tests = @()
    $acceptance = @()
    $summary = ''

    switch ($TaskProfile) {
        'experiment-record' {
            $summary = '使用确定性增量实验扫描后，仅处理变化证据并生成记录。'
            $steps = @([ordered]@{ step = '运行实验增量扫描'; purpose = '提取文件哈希、变化文件和常见实验元数据' }, [ordered]@{ step = '根据结构化证据生成记录'; purpose = '减少重复读取原始日志' })
            $tests = @('运行 azf-experiment-scan.ps1 并校验 experiment-evidence.schema.json')
            $acceptance = @('只处理新增或哈希变化的证据文件', '所有数字都能回到 source_files')
        }
        'html-ui' {
            $score = 4
            $mechanical = $false
            $executor = 'terra'
            $summary = '生成隔离的 HTML/CSS 视觉候选，使用独立浏览器截图并等待用户选择。'
            $steps = @([ordered]@{ step = '创建隔离视觉变体'; purpose = '避免覆盖当前主版本' }, [ordered]@{ step = '渲染桌面端和移动端截图'; purpose = '检查真实视觉和响应式行为' }, [ordered]@{ step = '生成候选画廊'; purpose = '让用户选择最终方向' })
            $tests = @('Playwright desktop 1440x900', 'Playwright mobile 390x844')
            $acceptance = @('每个候选都有桌面端和移动端截图', '主工作树在用户选择前保持不变')
        }
        default {
            $summary = '对明确、低风险任务使用确定性路由，在 Claude Code + DS v4 Flash（60%）与 Luna（40%）之间选择，并由 Terra 独立评估。'
            $steps = @([ordered]@{ step = '检查现有工作树'; purpose = '保护用户已有修改' }, [ordered]@{ step = '执行最小范围变更'; purpose = '完成原始任务' })
            $tests = @('运行仓库已有的相关测试入口')
            $acceptance = @('修改范围与任务一致', '相关测试有真实输出')
        }
    }

    if ($highRisk) {
        $score = 8
        $risk = 'high'
        $mechanical = $false
        $executor = 'sol'
        $evaluator = 'sol'
    } elseif ($Mode -eq 'quality') {
        $score = [Math]::Max($score, 8)
        $risk = 'medium'
        $mechanical = $false
        $executor = 'sol'
        $evaluator = 'sol'
    }

    $riskList = [System.Collections.Generic.List[string]]::new()
    if ($highRisk) { $riskList.Add('任务文本命中高风险关键词，需要独立 Sol 规划和评估。') }
    $workItems = @([ordered]@{
        id = 'work-01'
        objective = $summary
        target_files = @($affected)
        target_symbols = @()
        prerequisites = @()
        allowed_actions = @('修改完成任务所需文件', '运行计划中的检查')
        forbidden_actions = @('git add', 'git commit', 'git push', '创建 PR', '无关删除')
        context_files = @()
        acceptance_checks = @($tests)
        required_evidence = @('changed_files', 'diff_stat', 'test_commands', 'exit_codes')
        failure_policy = [ordered]@{ same_error = 'targeted_repair'; repeated_error = 'split_work_item'; plan_conflict = 'replan' }
    })
    return [pscustomobject][ordered]@{
        status = 'PLAN_READY'
        complexity_score = $score
        risk_level = $risk
        mechanical = $mechanical
        selected_executor = $executor
        selected_evaluator = $evaluator
        summary = $summary
        steps = @($steps)
        work_items = $workItems
        affected_files = @($affected)
        test_commands = @($tests)
        acceptance_criteria = @($acceptance)
        risks = $riskList
        task_profile = $TaskProfile
        planner_invoked = $false
        variant_count = if ($TaskProfile -eq 'html-ui') { $VariantCount } else { 0 }
    }
}

function Invoke-Executor {
    param(
        [Parameter(Mandatory = $true)]$Plan,
        [Parameter(Mandatory = $true)][string]$ExecutorTier,
        [Parameter(Mandatory = $true)][string]$ReworkContext,
        [Parameter(Mandatory = $true)][int]$Round,
        [Parameter(Mandatory = $true)]$RouteState
    )
    $planText = Get-Content -LiteralPath (Join-Path $RunDirectory 'plan.json') -Raw -Encoding utf8
    $baselineText = Get-Content -LiteralPath (Join-Path $RunDirectory 'baseline.json') -Raw -Encoding utf8
    $prompt = @"
你是 azf_${ExecutorTier}_executor，负责在当前本地仓库执行已批准计划。

原始任务：
$Task

任务档案：$TaskProfile
变体数量（仅 html-ui）：$VariantCount

Planner 计划：
$planText

当前 Work Item（只处理这一项）：
$([string]($Plan.work_items | Select-Object -First 1 | ConvertTo-Json -Depth 20))

执行前基线：
$baselineText

返工要求：
$ReworkContext

严格要求：
- 先检查当前工作树和已有 diff，保护用户原有修改。
- 只修改计划范围内的文件，保持改动最小。
- 不执行 git add、git commit、git push、创建 PR、破坏性 Git 命令或无关删除。
- 不安装或升级依赖，不做数据库迁移，不修改线上资源，除非原任务明确授权。
- 运行相关格式化、静态检查和测试，并保留真实结果。
- html-ui 任务必须在隔离候选目录中工作，不覆盖主版本；截图和候选画廊交给独立 Playwright 管线。
- 如果计划、环境或权限不足以安全完成，明确报告，不要声称完成。
- 当前会话由控制器以 full-trust 启动；职责边界依靠本提示词、Work Item 和阶段后审计，不得借此扩大任务范围。

    只输出符合 JSON Schema 的 JSON，status 必须为 EXECUTION_COMPLETE。Schema 中的所有字段都必须输出；没有内容的数组输出 []，没有内容的字符串输出空字符串。
"@
    $path = Join-Path $RunDirectory ('execution-r{0}.json' -f $Round)
    $stage = 'executor-r{0}' -f $Round
    if ([string]$RouteState.harness -in @('claude-code', 'deepseek', 'kimi-qwen')) {
        $spec = Get-ExternalProfileSpec -Profile ([string]$RouteState.external_profile)
        Invoke-ClaudeCodeStage -Stage $stage -Prompt $prompt -Model $spec.requested_model -Effort ([string]$RouteState.requested_effort) -SchemaPath $ExecutionSchema -OutputPath $path -RunDirectory $RunDirectory -Role 'executor' -StatusField 'status' -ExpectedStatus 'EXECUTION_COMPLETE' -HarnessLabel ([string]$RouteState.harness)
    } else {
        Invoke-CodexStage -Stage $stage -Prompt $prompt -Model (Get-ModelName -Tier $ExecutorTier) -Effort ([string]$RouteState.requested_effort) -Role 'executor' -SchemaPath $ExecutionSchema -OutputPath $path -RunDirectory $RunDirectory
    }
    return (Read-JsonFile -Path $path)
}

function Invoke-Evaluator {
    param(
        [Parameter(Mandatory = $true)]$Plan,
        [Parameter(Mandatory = $true)]$Execution,
        [Parameter(Mandatory = $true)][string]$EvaluatorTier,
        [Parameter(Mandatory = $true)][int]$Round
    )
    $planText = Get-Content -LiteralPath (Join-Path $RunDirectory 'plan.json') -Raw -Encoding utf8
    $executionText = $Execution | ConvertTo-Json -Depth 30
    $prompt = @"
你是 azf_${EvaluatorTier}_evaluator。使用全新只读会话独立验收，不修改文件。

原始任务：
$Task

任务档案：$TaskProfile

Planner 计划：
$planText

Executor 报告（只能作为线索）：
$executionText

请直接检查：
1. 当前文件和 Git diff；
2. Planner 的每项验收标准；
3. 测试命令和真实输出；
4. 修改范围、回归风险和安全性；
5. Executor 是否确实完成了写入；
6. 当前路由、模型和沙箱是否符合控制器记录。
7. html-ui 任务必须检查真实桌面端和移动端截图，而不是只审查 HTML/CSS；不要用审美契约限制候选，报告各候选的差异、优点和技术问题。

不要只相信 Executor 总结。无法验证时返回 BLOCKED 检查，不得伪造 PASS。
全部验收标准通过才返回 PASS。失败时列出具体文件、证据和修复要求。
如果原计划存在根本问题，将 replan_required 设置为 true。

    只输出符合 JSON Schema 的 JSON。Schema 中的所有字段都必须输出；没有内容的数组输出 []，没有内容的字符串输出空字符串。variant_comparison 的每项都必须包含 variant_id、summary、strengths、weaknesses、technical_issues。
"@
    $path = Join-Path $RunDirectory ('evaluation-r{0}.json' -f $Round)
    if ($Harness -eq 'deepseek') {
        Invoke-ClaudeCodeStage -Stage ('evaluator-r{0}' -f $Round) -Prompt $prompt -Model $DsProModel -Effort 'high' -SchemaPath $EvaluationSchema -OutputPath $path -RunDirectory $RunDirectory -Role 'evaluator' -StatusField 'verdict' -HarnessLabel 'deepseek'
    } elseif ($Harness -eq 'kimi-qwen') {
        # Kimi 评估：思维强度交给模型自决（effort auto，可被 -ExternalEffort 覆盖）。
        Invoke-ClaudeCodeStage -Stage ('evaluator-r{0}' -f $Round) -Prompt $prompt -Model $KimiModel -Effort $ExternalEffort -SchemaPath $EvaluationSchema -OutputPath $path -RunDirectory $RunDirectory -Role 'evaluator' -StatusField 'verdict' -HarnessLabel 'kimi-qwen'
    } else {
        Invoke-CodexStage -Stage ('evaluator-r{0}' -f $Round) -Prompt $prompt -Model (Get-ModelName -Tier $EvaluatorTier) -Effort 'high' -Role 'evaluator' -SchemaPath $EvaluationSchema -OutputPath $path -RunDirectory $RunDirectory
    }
    return (Read-JsonFile -Path $path)
}

function Invoke-DeterministicGate {
    param(
        [Parameter(Mandatory = $true)]$Plan,
        [Parameter(Mandatory = $true)]$Execution,
        [Parameter(Mandatory = $true)][int]$Round
    )
    $issues = @()
    $checks = @()
    $modified = @($Execution.modified_files)
    $workItems = @($Plan.work_items)
    $allowed = @()
    if ($workItems.Count -gt 0) { $allowed = @($workItems[0].target_files) }
    if ($allowed.Count -gt 0 -and $modified.Count -gt 0) {
        $allowedNames = @($allowed | ForEach-Object { [IO.Path]::GetFileName([string]$_) })
        $outOfScope = @($modified | Where-Object { $allowedNames -notcontains [IO.Path]::GetFileName([string]$_) })
        if ($outOfScope.Count -gt 0) { $issues += ('scope_violation: ' + ($outOfScope -join ', ')) }
    }
    if ($null -eq $Execution.status -or [string]$Execution.status -ne 'EXECUTION_COMPLETE') {
        $issues += 'schema_error: execution status is not EXECUTION_COMPLETE'
    }
    foreach ($test in @($Execution.tests)) {
        $resultText = [string]$test.result
        if ([regex]::IsMatch($resultText, '失败|错误|fail|error|non[- ]zero|not run|blocked', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
            $issues += ('test_failure: ' + [string]$test.command)
        }
    }
    $checks += [ordered]@{ name = 'execution_schema'; result = if ($issues -match 'schema_error') { 'FAIL' } else { 'PASS' }; evidence = 'execution JSON status' }
    $checks += [ordered]@{ name = 'scope'; result = if ($issues -match 'scope_violation') { 'FAIL' } else { 'PASS' }; evidence = 'modified_files versus Work Item target_files' }
    $checks += [ordered]@{ name = 'reported_tests'; result = if ($issues -match 'test_failure') { 'FAIL' } else { 'PASS' }; evidence = 'Executor test result fields' }
    $gate = [ordered]@{
        verdict = if ($issues.Count -eq 0) { 'PASS' } else { 'REWORK' }
        checks = $checks
        issues = @($issues)
        round = $Round
        checked_at = (Get-Date).ToString('o')
    }
    Write-JsonFile -Value $gate -Path (Join-Path $RunDirectory ('deterministic-gate-r{0}.json' -f $Round))
    return [pscustomobject]$gate
}

$RunDirectory = $null
$LockPath = $null
$PlannerInvoked = $false
$PlannerTier = 'terra'
$exitCode = 0

try {
    if ($Harness -in @('claude-code', 'deepseek', 'kimi-qwen')) {
        if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
            throw '找不到 claude 命令，请先确认 Claude Code CLI 在 PATH 中。'
        }
    } elseif (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
        throw '找不到 codex 命令，请先确认 Codex CLI 在 PATH 中。'
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw '找不到 git 命令。'
    }
    if (-not (Test-Path -LiteralPath $RepoPath -PathType Container)) {
        throw "仓库目录不存在：$RepoPath"
    }
    $RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path
    $gitRoot = (& git -C $RepoPath rev-parse --show-toplevel 2>$null).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitRoot)) {
        throw "目标目录不是 Git 仓库：$RepoPath"
    }
    $RepoPath = (Resolve-Path -LiteralPath $gitRoot).Path

    if ([string]::IsNullOrWhiteSpace($RunRoot)) {
        $base = if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { $env:TEMP } else { $env:LOCALAPPDATA }
        $RunRoot = Join-Path $base 'azf-auto-dev-loop\runs'
    }
    if ([string]::IsNullOrWhiteSpace($RunId)) {
        $RunId = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    }
    New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
    $RunDirectory = Join-Path $RunRoot $RunId
    New-Item -ItemType Directory -Path $RunDirectory -Force | Out-Null

    $repoKey = (($RepoPath -replace '[^A-Za-z0-9]+', '_').Trim('_'))
    $lockDirectory = Join-Path $RunRoot 'locks'
    New-Item -ItemType Directory -Path $lockDirectory -Force | Out-Null
    $LockPath = Join-Path $lockDirectory ('{0}.lock' -f $repoKey)
    if (Test-Path -LiteralPath $LockPath) {
        throw "同一仓库已有运行中的 azf-auto-dev-loop：$LockPath"
    }
    New-Item -ItemType File -Path $LockPath -Force | Out-Null

    $baseline = Get-Baseline
    Write-JsonFile -Value $baseline -Path (Join-Path $RunDirectory 'baseline.json')
    Write-JsonFile -Value ([ordered]@{
        run_id = $RunId
        task = $Task
        repo_path = $RepoPath
        mode = $Mode
        explicit_executor = $Executor
        explicit_evaluator = $Evaluator
        task_profile = $TaskProfile
        planner_mode = $PlannerMode
        harness = if ($Harness -eq 'auto') { 'codex' } else { $Harness }
        external_profile = if ($Harness -eq 'kimi-qwen') { 'claude-qwen' } elseif ($Harness -in @('claude-code', 'deepseek')) { $ExternalProfile } else { $null }
        requested_model = if ($Harness -eq 'kimi-qwen') { $QwenModel } elseif ($Harness -in @('claude-code', 'deepseek')) { (Get-ExternalProfileSpec -Profile $ExternalProfile).requested_model } else { 'auto' }
        requested_effort = $ExternalEffort
        permission_mode = 'full-trust'
        default_executor_weights = [ordered]@{ claude_ds_v4_flash = 0.60; luna = 0.40 }
        execution_order = @('ds-v4-flash', 'luna', 'terra', 'ds-v4-pro', 'sol')
        variant_count = if ($TaskProfile -eq 'html-ui') { $VariantCount } else { 0 }
        max_rework_rounds = $MaxReworkRounds
        started_at = (Get-Date).ToString('o')
    }) -Path (Join-Path $RunDirectory 'run.json')

    if (Should-InvokePlanner) {
        $PlannerInvoked = $true
        $plan = Invoke-Planner
    } else {
        $plan = Invoke-DeterministicPlan
        Write-JsonFile -Value $plan -Path (Join-Path $RunDirectory 'plan.json')
        Write-Host '[PLAN_READY] planner=deterministic_preflight'
    }
    if ([string]$plan.status -ne 'PLAN_READY') {
        throw 'Planner 没有返回 PLAN_READY。'
    }

    $historyBefore = Get-RouteHistorySummary
    if ($null -eq $historyBefore) { $historyBefore = [object[]]@() }
    Write-JsonFile -Value $historyBefore -Path (Join-Path $RunDirectory 'route-history-before.json')

    $routeState = Resolve-InitialRoute -Plan $plan
    $executorTier = [string]$routeState.executor_tier
    $evaluatorTier = Resolve-EvaluatorTier -ExecutorTier $executorTier -Plan $plan
    $route = Write-RouteRecord -Plan $plan -ExecutorTier $executorTier -EvaluatorTier $evaluatorTier -Round 0 -RouteState $routeState
    $routeModel = if ($routeState.harness -in @('claude-code', 'deepseek', 'kimi-qwen')) { (Get-ExternalProfileSpec -Profile $routeState.external_profile).requested_model } else { Get-ModelName -Tier $executorTier }
    Write-Host ("[PLAN_READY] score={0} risk={1} harness={2} model={3} effort={4} executor={5} evaluator={6}" -f $plan.complexity_score, $plan.risk_level, $routeState.harness, $routeModel, $routeState.requested_effort, $executorTier, $evaluatorTier)

    if ($Mode -eq 'dry-run' -or ($Mode -eq 'reviewed' -and -not $Approve)) {
        $status = if ($Mode -eq 'dry-run') { 'DRY_RUN' } else { 'WAITING_CONFIRMATION' }
        $report = [ordered]@{
            status = $status
            run_id = $RunId
            task_profile = $TaskProfile
            planner_invoked = [bool]$PlannerInvoked
            route = $route
            plan = $plan
            evidence_directory = $RunDirectory
            message = if ($Mode -eq 'dry-run') { '仅完成规划和路由，未修改文件。' } else { '已暂停，使用 -Approve 后才会开始执行。' }
        }
        Write-JsonFile -Value $report -Path (Join-Path $RunDirectory 'final-report.json')
        Write-Host ("[$status] evidence=$RunDirectory")
        $exitCode = 0
    } else {
        $reworkContext = '无。首次执行。'
        $finalEvaluation = $null
        $finalExecution = $null
        $passed = $false
        $completedRound = 0

        for ($round = 0; $round -le $MaxReworkRounds; $round++) {
            $completedRound = $round
            $finalExecution = Invoke-Executor -Plan $plan -ExecutorTier $executorTier -ReworkContext $reworkContext -Round $round -RouteState $routeState
            $resolutionPath = Join-Path $RunDirectory ('executor-r{0}.resolution.json' -f $round)
            if (Test-Path -LiteralPath $resolutionPath) {
                $resolution = Read-JsonFile -Path $resolutionPath
                $route.resolved_model = [string]$resolution.resolved_model
                $route.resolved_effort = [string]$resolution.resolved_effort
                Write-JsonFile -Value $route -Path (Join-Path $RunDirectory ('route-r{0}.json' -f $round))
            }
            $gate = Invoke-DeterministicGate -Plan $plan -Execution $finalExecution -Round $round
            if ([string]$gate.verdict -eq 'PASS') {
                $finalEvaluation = Invoke-Evaluator -Plan $plan -Execution $finalExecution -EvaluatorTier $evaluatorTier -Round $round
            } else {
                $finalEvaluation = [pscustomobject][ordered]@{
                    verdict = 'REWORK'
                    checks = @($gate.checks)
                    summary = '确定性 Gate 未通过，未调用 Evaluator。'
                    rework_required = @($gate.issues)
                    replan_required = $false
                    remaining_risks = @('deterministic_gate_failed')
                    task_profile = $TaskProfile
                    variant_comparison = @()
                    screenshots = @()
                }
                Write-JsonFile -Value $finalEvaluation -Path (Join-Path $RunDirectory ('evaluation-r{0}.json' -f $round))
            }
            if ([string]$finalEvaluation.verdict -eq 'PASS') {
                $passed = $true
                break
            }

            if ($round -ge $MaxReworkRounds) {
                break
            }
            if ($Executor -ne 'auto' -or $Harness -eq 'codex') {
                break
            }

            $reworkContext = (($finalEvaluation.rework_required | ForEach-Object { "- $_" }) -join "`n")
            if ([bool]$finalEvaluation.replan_required) {
                $PlannerInvoked = $true
                $plan = Invoke-Planner -AdditionalContext ("上一次独立验收要求重新规划：`n" + $reworkContext)
                if ([string]$plan.status -ne 'PLAN_READY') {
                    throw '重新规划没有返回 PLAN_READY。'
                }
                Write-JsonFile -Value $plan -Path (Join-Path $RunDirectory 'plan.json')
                $routeState = Resolve-InitialRoute -Plan $plan
            } else {
                $routeState = Get-NextRoute -CurrentRoute $routeState
            }
            $executorTier = [string]$routeState.executor_tier
            $evaluatorTier = Resolve-EvaluatorTier -ExecutorTier $executorTier -Plan $plan
            $route = Write-RouteRecord -Plan $plan -ExecutorTier $executorTier -EvaluatorTier $evaluatorTier -Round ($round + 1) -RouteState $routeState
            $nextModel = if ($routeState.harness -in @('claude-code', 'deepseek', 'kimi-qwen')) { (Get-ExternalProfileSpec -Profile $routeState.external_profile).requested_model } else { Get-ModelName -Tier $executorTier }
            Write-Host ("[REWORK] round={0} next_harness={1} next_model={2} next_effort={3} reason={4} evaluator={5}" -f ($round + 1), $routeState.harness, $nextModel, $routeState.requested_effort, $routeState.route_reason, $evaluatorTier)
        }

        $historyAfter = Get-RouteHistorySummary
        if ($null -eq $historyAfter) { $historyAfter = [object[]]@() }
        $finalStatus = if ($passed) { 'PASS' } else { 'BLOCKED' }
        $report = [ordered]@{
            status = $finalStatus
            run_id = $RunId
            task_profile = $TaskProfile
            planner_invoked = [bool]$PlannerInvoked
            route = $route
            plan = $plan
            final_execution = $finalExecution
            final_evaluation = $finalEvaluation
            rework_rounds = $completedRound
            baseline = $baseline
            route_history = $historyAfter
            usage = Get-RunUsageSummary
            evidence_directory = $RunDirectory
            no_commit_or_push = $true
            completed_at = (Get-Date).ToString('o')
        }
        Write-JsonFile -Value $report -Path (Join-Path $RunDirectory 'final-report.json')
        Write-Host ("[$finalStatus] evidence=$RunDirectory")
        $exitCode = if ($passed) { 0 } else { 2 }
    }
}
catch {
    $message = $_.Exception.Message
    if ($RunDirectory) {
        Write-JsonFile -Value ([ordered]@{
            status = 'BLOCKED'
            run_id = $RunId
            error = $message
            evidence_directory = $RunDirectory
            completed_at = (Get-Date).ToString('o')
        }) -Path (Join-Path $RunDirectory 'final-report.json')
    }
    Write-Error $message
    $exitCode = 2
}
finally {
    if ($LockPath -and (Test-Path -LiteralPath $LockPath)) {
        Remove-Item -LiteralPath $LockPath -Force -ErrorAction SilentlyContinue
    }
}

exit $exitCode
