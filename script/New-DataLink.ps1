<#
Creates a junction (Windows) or symlink (Linux/macOS) at LinkPath pointing
to TargetPath. Safe to re-run: skips if the link already points at the
right target, warns and does nothing if the source doesn't exist.
#>

function New-DataLink {
    [CmdletBinding()]
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
    Write-Verbose "OK  $LinkPath"
}
