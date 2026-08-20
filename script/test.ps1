#Requires -Version 7.0
<#
Runs the same translation format checks CI runs in .github/workflows,
locally and before pushing. Requires Python 3.

Usage:
  ./script/test.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$checksDir = Join-Path $repoRoot '.github/workflows'

$checks = @(
    'check_dash_format.py'
    'check_pawn_gender.py'
    'check_report_string_dot.py'
    'check_utf-8.py'
    'check_xml_format.py'
    'worldinfo_case.py'
)

$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-Error 'Python 3 not found (looked for "python3" and "python" on PATH).'
}

Push-Location $repoRoot
try {
    $failed = $false
    foreach ($check in $checks) {
        Write-Host "`n=== $check ===" -ForegroundColor Cyan
        & $python.Source (Join-Path $checksDir $check)
        if ($LASTEXITCODE -ne 0) { $failed = $true }
    }
}
finally {
    Pop-Location
}

if ($failed) {
    Write-Host "`nFAILED" -ForegroundColor Red
    exit 1
}

Write-Host "`nOK" -ForegroundColor Green
