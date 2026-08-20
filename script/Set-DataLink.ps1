<#
Creates or removes the .Data/<Dlc>/** links (junction/symlink) that mirror
one DLC's Defs/Keyed/Strings from a locally installed RimWorld into this
repo, for reference while translating.
#>

function Set-DataLink {
    param(
        [Parameter(Mandatory)][string]$RimWorldPath,
        [Parameter(Mandatory)][string]$RepoRoot,
        [Parameter(Mandatory)][string]$Dlc,
        [switch]$Remove
    )

    $dlcDataRoot = "$RepoRoot/.Data/$Dlc"

    if ($Remove) {
        if (Test-Path -LiteralPath $dlcDataRoot) {
            Remove-Item -LiteralPath $dlcDataRoot -Recurse -Force
            Write-Host "Removed: $dlcDataRoot"
        }
        return
    }

    New-DataLink -LinkPath "$dlcDataRoot/Defs" -TargetPath "$RimWorldPath/Data/$Dlc/Defs"
    New-DataLink -LinkPath "$dlcDataRoot/Keyed" -TargetPath "$RimWorldPath/Data/$Dlc/Languages/English/Keyed"
    New-DataLink -LinkPath "$dlcDataRoot/Strings" -TargetPath "$RimWorldPath/Data/$Dlc/Languages/English/Strings"
}
