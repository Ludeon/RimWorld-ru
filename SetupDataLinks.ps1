#Requires -Version 7.0
<#
Creates junction (Windows) or symlink (Linux/macOS) links in .Data/**
pointing at the data of a locally installed RimWorld.

Usage:
  ./SetupDataLinks.ps1          # auto-detect / confirm / prompt for path, safe to re-run
  ./SetupDataLinks.ps1 -Remove  # remove .Data entirely
#>

[CmdletBinding()]
param(
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/Resolve-RimWorldPath.ps1"
. "$PSScriptRoot/New-DataLink.ps1"

$repoRoot = $PSScriptRoot
$dataRoot = "$repoRoot/.Data"

if ($Remove) {
    if (Test-Path -LiteralPath $dataRoot) {
        Remove-Item -LiteralPath $dataRoot -Recurse -Force
        Write-Host "Removed: $dataRoot"
    }
    else {
        Write-Host ".Data not found — nothing to remove."
    }
    return
}

$RimWorldPath = Resolve-RimWorldPath
Write-Host "Using RimWorld: $RimWorldPath"

$dlcs = @('Core', 'Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

foreach ($dlc in $dlcs) {
    Write-Host "$dlc..."
    New-DataLink -LinkPath "$dataRoot/$dlc/Defs" -TargetPath "$RimWorldPath/Data/$dlc/Defs"
    New-DataLink -LinkPath "$dataRoot/$dlc/Keyed" -TargetPath "$RimWorldPath/Data/$dlc/Languages/English/Keyed"
    New-DataLink -LinkPath "$dataRoot/$dlc/Strings" -TargetPath "$RimWorldPath/Data/$dlc/Languages/English/Strings"
}

Write-Host 'Done.'
