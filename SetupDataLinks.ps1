#Requires -Version 7.0
<#
Creates junction (Windows) or symlink (Linux/macOS) links in .Data/**
pointing at the data of a locally installed RimWorld.

Usage:
  ./SetupDataLinks.ps1                          # auto-detect / prompt for path, safe to re-run
  ./SetupDataLinks.ps1 -RimWorldPath 'C:\...\RimWorld'
  ./SetupDataLinks.ps1 -Remove                  # remove .Data entirely
#>

[CmdletBinding()]
param(
    [string]$RimWorldPath,
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/Resolve-RimWorldPath.ps1"

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

$RimWorldPath = Resolve-RimWorldPath -RimWorldPath $RimWorldPath
Write-Host "Using RimWorld: $RimWorldPath"

$dlcs = @('Core', 'Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

function New-DataLink {
    param([string]$LinkPath, [string]$TargetPath)

    if (-not (Test-Path -LiteralPath $TargetPath)) {
        Write-Warning "Source not found, skipping: $TargetPath"
        return
    }

    if (Test-Path -LiteralPath $LinkPath) {
        $existing = Get-Item -LiteralPath $LinkPath -Force
        if ($existing.LinkType -and $existing.Target -contains $TargetPath) {
            return # already set up correctly
        }
        Remove-Item -LiteralPath $LinkPath -Force -Recurse
    }

    $parent = Split-Path -Parent $LinkPath
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    $linkType = $IsWindows ? 'Junction' : 'SymbolicLink'
    New-Item -ItemType $linkType -Path $LinkPath -Target $TargetPath | Out-Null
    Write-Host "  OK  $LinkPath"
}

foreach ($dlc in $dlcs) {
    Write-Host "$dlc..."
    New-DataLink -LinkPath "$dataRoot/$dlc/Defs" -TargetPath "$RimWorldPath/Data/$dlc/Defs"
    New-DataLink -LinkPath "$dataRoot/$dlc/Keyed" -TargetPath "$RimWorldPath/Data/$dlc/Languages/English/Keyed"
    New-DataLink -LinkPath "$dataRoot/$dlc/Strings" -TargetPath "$RimWorldPath/Data/$dlc/Languages/English/Strings"
}

Write-Host 'Done.'
