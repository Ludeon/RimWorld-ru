<#
Resolves the path to a locally installed RimWorld: explicit parameter,
then auto-detection, then an interactive prompt as a last resort.
Validates the result.
#>

function Find-DefaultRimWorldPath {
    if ($IsWindows) {
        $uninstallKeys = @(
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
            'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
            'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
        )
        $entry = Get-ItemProperty -Path $uninstallKeys -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -like '*RimWorld*' -and $_.InstallLocation } |
            Select-Object -First 1
        if ($entry -and (Test-Path -LiteralPath $entry.InstallLocation)) {
            return $entry.InstallLocation.TrimEnd('\')
        }
    }
    elseif ($IsLinux) {
        foreach ($base in @("$HOME/.steam/steam", "$HOME/.local/share/Steam")) {
            $candidate = Join-Path $base 'steamapps/common/RimWorld'
            if (Test-Path -LiteralPath $candidate) { return $candidate }
        }
    }
    # On macOS the data lives inside RimWorldMac.app, there is no reliable default — ask explicitly.
    return $null
}

function Resolve-RimWorldPath {
    param(
        [string]$RimWorldPath
    )

    if (-not $RimWorldPath) {
        $RimWorldPath = Find-DefaultRimWorldPath
    }

    if (-not $RimWorldPath -or -not (Test-Path -LiteralPath (Join-Path $RimWorldPath 'Data'))) {
        $RimWorldPath = Read-Host 'Enter the path to the installed RimWorld folder (e.g. ...\Steam\steamapps\common\RimWorld)'
    }

    $RimWorldPath = $RimWorldPath.TrimEnd('\', '/')

    if (-not (Test-Path -LiteralPath (Join-Path $RimWorldPath 'Data'))) {
        Write-Error "No Data folder found at '$RimWorldPath' — check the path to the installed game."
    }

    return $RimWorldPath
}
