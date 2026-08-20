#Requires -Version 7.0
<#
One-command workspace setup. Links this repo's translation folders into a
locally installed RimWorld (so the game reads translations straight from
the repo) and links the game's English source data into .Data/** (for
reference while translating), for every owned DLC.

Usage:
  ./script/setup.ps1          # auto-detect / confirm / prompt for path, safe to re-run
  ./script/setup.ps1 -Remove  # remove everything this script created
#>

[CmdletBinding()]
param(
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/Resolve-RimWorldPath.ps1"
. "$PSScriptRoot/New-DataLink.ps1"
. "$PSScriptRoot/Set-DataLink.ps1"
. "$PSScriptRoot/Set-LocalizationLink.ps1"

$repoRoot = Split-Path -Parent $PSScriptRoot
$RimWorldPath = Resolve-RimWorldPath
$dlcs = @('Core', 'Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

if ($Remove) {
    foreach ($dlc in $dlcs) {
        Set-LocalizationLink -RimWorldPath $RimWorldPath -RepoRoot $repoRoot -Dlc $dlc -Remove
        Set-DataLink -RepoRoot $repoRoot -Dlc $dlc -Remove
    }
    $dataRoot = "$repoRoot/.Data"
    if ((Test-Path -LiteralPath $dataRoot) -and -not (Get-ChildItem -LiteralPath $dataRoot)) {
        Remove-Item -LiteralPath $dataRoot -Force
    }
    Write-Host 'Done.'
    return
}

Write-Host "Using RimWorld: $RimWorldPath"

foreach ($dlc in $dlcs) {
    Write-Host "`n${dlc}:"
    Set-LocalizationLink -RimWorldPath $RimWorldPath -RepoRoot $repoRoot -Dlc $dlc
    Set-DataLink -RimWorldPath $RimWorldPath -RepoRoot $repoRoot -Dlc $dlc
}

Write-Host "`nDone."
