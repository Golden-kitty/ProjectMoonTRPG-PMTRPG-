param(
  [Parameter(Mandatory=$true)][string]$Src,
  [string]$OutDocs = "docs",
  [string]$Assets = "assets",
  [switch]$Clean
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath (Resolve-Path ".").Path

Write-Host "Import WinCHM export -> Markdown" -ForegroundColor Cyan
Write-Host "Src: $Src"
Write-Host "OutDocs: $OutDocs"
Write-Host "Assets: $Assets"

$argsList = @(
  "scripts/import_winchm_export.py",
  "--src", $Src,
  "--out-docs", $OutDocs,
  "--assets", $Assets,
  "--target", "github"
)
if ($Clean) { $argsList += "--clean" }

python @argsList

