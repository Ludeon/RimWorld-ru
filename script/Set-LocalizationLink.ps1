<#
Creates or removes the link inside the installed RimWorld's
Data/<Dlc>/Languages/ pointing at this repo's <Dlc> translation folder, so
the game reads localization directly from the repo instead of a manually
copied version. The link is named after this repo's own root folder name.
#>

function Set-LocalizationLink {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$RimWorldPath,
        [Parameter(Mandatory)][string]$RepoRoot,
        [Parameter(Mandatory)][string]$Dlc,
        [switch]$Remove
    )

    $repoName = Split-Path -Leaf $RepoRoot
    $linkPath = "$RimWorldPath/Data/$Dlc/Languages/$repoName"

    if ($Remove) {
        if ((Test-Path -LiteralPath $linkPath) -and $PSCmdlet.ShouldProcess($linkPath, 'Remove')) {
            Remove-Item -LiteralPath $linkPath -Force -Recurse
            Write-Verbose "Removed: $linkPath"
        }
        return
    }

    New-DataLink -LinkPath $linkPath -TargetPath "$RepoRoot/$Dlc"
}
