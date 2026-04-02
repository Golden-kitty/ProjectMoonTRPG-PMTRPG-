<#
.SYNOPSIS
    Dispatch Launcher - open one Cursor dialog per dispatch file.

.DESCRIPTION
    Scan openspec/dispatch/ for files matching the given Change ID and
    open a Cursor deeplink for each file.

.PARAMETER ChangeId
    Change ID used to match dispatch files.

.PARAMETER WorkspacePath
    Workspace root path. Defaults to the parent of this script folder.

.PARAMETER DryRun
    Print the commands without opening any Cursor dialog.

.PARAMETER DelaySeconds
    Delay between dialog launches. Default: 2.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ChangeId,

    [string]$WorkspacePath = "",

    [switch]$DryRun,

    [int]$DelaySeconds = 2
)

if (-not $WorkspacePath) {
    $WorkspacePath = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
}

$dispatchDir = Join-Path $WorkspacePath "openspec\dispatch"

if (-not (Test-Path $dispatchDir)) {
    Write-Error "Dispatch directory not found: $dispatchDir"
    Write-Error "Generate dispatch files for the change first."
    exit 1
}

$pattern = "$ChangeId--*.md"
$files = Get-ChildItem -Path $dispatchDir -Filter $pattern -File -ErrorAction SilentlyContinue | Sort-Object Name

if ($files.Count -eq 0) {
    Write-Error "No dispatch files matched: $dispatchDir\$pattern"
    exit 1
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Dispatch Launcher - $ChangeId" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Found $($files.Count) dispatch file(s):" -ForegroundColor White

foreach ($file in $files) {
    $modelTag = $file.BaseName -replace "^$([regex]::Escape($ChangeId))--", ""
    $relativePath = "openspec/dispatch/$($file.Name)"
    $firstLine = Get-Content $file.FullName -TotalCount 1 -Encoding UTF8
    $recommendedModel = ""

    if ($firstLine -match "/\s*(.+)$") {
        $recommendedModel = $Matches[1].Trim()
    }

    Write-Host "  [$modelTag] $relativePath" -ForegroundColor Green
    if ($recommendedModel) {
        Write-Host "           Recommended model: $recommendedModel" -ForegroundColor DarkGray
    }
}

Write-Host ""

if ($DryRun) {
    Write-Host "[DryRun] Commands that would be executed:" -ForegroundColor Yellow
    Write-Host ""
}

$index = 0
foreach ($file in $files) {
    $index++
    $modelTag = $file.BaseName -replace "^$([regex]::Escape($ChangeId))--", ""
    $relativePath = "openspec/dispatch/$($file.Name)"
    $prompt = "Please switch to Agent mode, then read and execute all instructions in $relativePath."
    $encodedPrompt = [System.Uri]::EscapeDataString($prompt)
    $deeplink = "cursor://anysphere.cursor-deeplink/prompt?text=$encodedPrompt"

    $firstLine = Get-Content $file.FullName -TotalCount 1 -Encoding UTF8
    $recommendedModel = ""
    if ($firstLine -match "/\s*(.+)$") {
        $recommendedModel = $Matches[1].Trim()
    }

    if ($DryRun) {
        Write-Host "  [$index/$($files.Count)] Start-Process `"$deeplink`"" -ForegroundColor DarkYellow
        if ($recommendedModel) {
            Write-Host "              -> Select model: $recommendedModel" -ForegroundColor DarkGray
        }
    }
    else {
        Write-Host "[$index/$($files.Count)] Opening dialog: $modelTag" -ForegroundColor Green
        if ($recommendedModel) {
            Write-Host "  -> Select model in Cursor: $recommendedModel" -ForegroundColor Yellow
        }

        Start-Process $deeplink

        if ($index -lt $files.Count) {
            Write-Host "  Waiting ${DelaySeconds}s ..." -ForegroundColor DarkGray
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "  [DryRun] No dialogs were opened." -ForegroundColor Yellow
}
else {
    Write-Host "  All dialogs were opened." -ForegroundColor Green
    Write-Host "  In each Cursor window, pick the model and confirm execution." -ForegroundColor White
}

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
