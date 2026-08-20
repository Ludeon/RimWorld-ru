#Requires -Version 7.0
<#
Creates junction (Windows) or symlink (Linux/macOS) links inside the
installed RimWorld's Data/<dlc>/Languages/ pointing at this repo's
translation folders, so the game reads localization directly from the
repo instead of a manually copied version. The link is named the same
in every DLC — after this repo's own root folder name.

Usage:
  ./SetupLocalizationLinks.ps1          # auto-detect / confirm / prompt for path, safe to re-run
  ./SetupLocalizationLinks.ps1 -Remove  # remove the links
#>

[CmdletBinding()]
param(
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/Resolve-RimWorldPath.ps1"
. "$PSScriptRoot/New-DataLink.ps1"

$repoRoot = $PSScriptRoot
$repoName = Split-Path -Leaf $repoRoot
$dlcs = @('Core', 'Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

$RimWorldPath = Resolve-RimWorldPath

if ($Remove) {
    foreach ($dlc in $dlcs) {
        $linkPath = "$RimWorldPath/Data/$dlc/Languages/$repoName"
        if (Test-Path -LiteralPath $linkPath) {
            Remove-Item -LiteralPath $linkPath -Force -Recurse
            Write-Host "Removed: $linkPath"
        }
    }
    return
}

Write-Host "Using RimWorld: $RimWorldPath"

foreach ($dlc in $dlcs) {
    New-DataLink -LinkPath "$RimWorldPath/Data/$dlc/Languages/$repoName" -TargetPath "$repoRoot/$dlc"
}

Write-Host 'Done.'
