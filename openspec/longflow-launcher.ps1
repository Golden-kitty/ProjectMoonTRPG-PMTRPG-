<#
.SYNOPSIS
    Longflow Launcher - open or reopen a longflow recovery dialog.

.DESCRIPTION
    Read openspec/changes/<ChangeId>/longflow-state.json, build a deeplink
    for longflow.md, and optionally retry when the heartbeat is stale.

.PARAMETER ChangeId
    Change ID, for example: enable-pmtrpg-dispatch-longflow

.PARAMETER WorkspacePath
    Workspace root path. Defaults to the parent of this script folder.

.PARAMETER DryRun
    Print the state summary and deeplink without opening Cursor.

.PARAMETER AutoRetry
    Enable stale-heartbeat-based relaunch.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ChangeId,

    [string]$WorkspacePath = "",

    [switch]$DryRun,

    [switch]$AutoRetry,

    [int]$StaleAfterSeconds = 180,

    [int]$PollSeconds = 30,

    [int]$CooldownSeconds = 60,

    [int]$MaxLaunchCount = 5
)

function Get-LongflowState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StatePath
    )

    if (-not (Test-Path $StatePath)) {
        throw "Longflow state file not found: $StatePath"
    }

    $raw = Get-Content $StatePath -Raw -Encoding UTF8
    try {
        return $raw | ConvertFrom-Json
    }
    catch {
        throw "Failed to parse JSON state file: $StatePath"
    }
}

function Test-IsTerminalStatus {
    param(
        [string]$Status
    )

    if (-not $Status) {
        return $false
    }

    return @("blocked", "awaiting_user", "completed") -contains $Status.ToLowerInvariant()
}

function Invoke-LongflowLaunch {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prompt,

        [Parameter(Mandatory = $true)]
        [int]$LaunchIndex,

        [switch]$DryRunMode
    )

    $encodedPrompt = [System.Uri]::EscapeDataString($Prompt)
    $deeplink = "cursor://anysphere.cursor-deeplink/prompt?text=$encodedPrompt"

    if ($DryRunMode) {
        Write-Host "[DryRun] [$LaunchIndex] Start-Process `"$deeplink`"" -ForegroundColor DarkYellow
    }
    else {
        Write-Host "[$LaunchIndex] Opening longflow recovery dialog..." -ForegroundColor Green
        Start-Process $deeplink
    }

    return $deeplink
}

if (-not $WorkspacePath) {
    $WorkspacePath = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
}

$changeDir = Join-Path $WorkspacePath "openspec\changes\$ChangeId"
$longflowDoc = Join-Path $changeDir "longflow.md"
$statePath = Join-Path $changeDir "longflow-state.json"

if (-not (Test-Path $changeDir)) {
    Write-Error "Change directory not found: $changeDir"
    exit 1
}

if (-not (Test-Path $longflowDoc)) {
    Write-Error "Longflow document not found: $longflowDoc"
    exit 1
}

$relativeDoc = "openspec/changes/$ChangeId/longflow.md"
$relativeState = "openspec/changes/$ChangeId/longflow-state.json"

$state = Get-LongflowState -StatePath $statePath
$status = [string]$state.status
$phase = [string]$state.current_phase
$task = [string]$state.current_task
$nextAction = [string]$state.next_action
$heartbeat = [string]$state.heartbeat_at

$defaultPrompt = "Please switch to Agent mode and continue $relativeDoc. Read $relativeState first, then resume from next_action."
$prompt = if ($state.resume_prompt) { [string]$state.resume_prompt } else { $defaultPrompt }

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Longflow Launcher - $ChangeId" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "State summary:" -ForegroundColor White
Write-Host "  status        : $status" -ForegroundColor Gray
Write-Host "  current_phase : $phase" -ForegroundColor Gray
Write-Host "  current_task  : $task" -ForegroundColor Gray
Write-Host "  heartbeat_at  : $heartbeat" -ForegroundColor Gray
Write-Host "  next_action   : $nextAction" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: deeplink still requires user confirmation in Cursor." -ForegroundColor Yellow
Write-Host ""

if (Test-IsTerminalStatus -Status $status) {
    Write-Host "Current state is terminal. Skipping automatic dialog launch." -ForegroundColor Yellow
    if ($DryRun) {
        Invoke-LongflowLaunch -Prompt $prompt -LaunchIndex 1 -DryRunMode | Out-Null
    }
    Write-Host ""
    exit 0
}

$launchCount = 1
$lastLaunchAt = Get-Date
Invoke-LongflowLaunch -Prompt $prompt -LaunchIndex $launchCount -DryRunMode:$DryRun | Out-Null

if ($DryRun) {
    Write-Host ""
    if ($AutoRetry) {
        Write-Host "[DryRun] AutoRetry is enabled, but polling is skipped." -ForegroundColor DarkYellow
    }
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

if (-not $AutoRetry) {
    Write-Host ""
    Write-Host "Dialog launch completed. User confirmation in Cursor is still required." -ForegroundColor Green
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

Write-Host "AutoRetry enabled. Monitoring heartbeat staleness for dialog relaunch." -ForegroundColor Green

while ($launchCount -lt $MaxLaunchCount) {
    Start-Sleep -Seconds $PollSeconds
    $state = Get-LongflowState -StatePath $statePath
    $status = [string]$state.status

    if (Test-IsTerminalStatus -Status $status) {
        Write-Host "Detected terminal status: $status. Stopping automatic retry." -ForegroundColor Yellow
        break
    }

    $heartbeatText = [string]$state.heartbeat_at
    if (-not $heartbeatText) {
        continue
    }

    try {
        $heartbeatTime = [datetime]::Parse($heartbeatText).ToUniversalTime()
    }
    catch {
        Write-Host "Could not parse heartbeat_at: $heartbeatText" -ForegroundColor Yellow
        continue
    }

    $now = (Get-Date).ToUniversalTime()
    $staleSeconds = ($now - $heartbeatTime).TotalSeconds
    $cooldownElapsed = ((Get-Date) - $lastLaunchAt).TotalSeconds

    if ($staleSeconds -lt $StaleAfterSeconds) {
        continue
    }

    if ($cooldownElapsed -lt $CooldownSeconds) {
        continue
    }

    $launchCount++
    Write-Host "Heartbeat stale for $([int]$staleSeconds)s. Dialog relaunch attempt #$launchCount." -ForegroundColor Yellow
    $prompt = if ($state.resume_prompt) { [string]$state.resume_prompt } else { $defaultPrompt }
    Invoke-LongflowLaunch -Prompt $prompt -LaunchIndex $launchCount | Out-Null
    $lastLaunchAt = Get-Date
}

if ($launchCount -ge $MaxLaunchCount) {
    Write-Host "Max launch count reached. Stopping automatic dialog retry." -ForegroundColor Yellow
}

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
