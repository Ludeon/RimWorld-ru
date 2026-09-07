<#
Resolves the path to a locally installed RimWorld: auto-detects a default
path and asks the user to confirm it, falling back to an interactive
prompt if there is no default or the user rejects it. Validates the result.
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
    $RimWorldPath = Find-DefaultRimWorldPath

    if ($RimWorldPath) {
        $answer = Read-Host "Found RimWorld at '$RimWorldPath'. Use this path? [Y/n]"
        if ($answer -match '^n') {
            $RimWorldPath = $null
        }
    }

    if (-not $RimWorldPath) {
        $RimWorldPath = Read-Host 'Enter the path to the installed RimWorld folder (e.g. ...\Steam\steamapps\common\RimWorld)'
    }

    $RimWorldPath = $RimWorldPath.TrimEnd('\', '/')

    if (-not (Test-Path -LiteralPath (Join-Path $RimWorldPath 'Data'))) {
        Write-Error "No Data folder found at '$RimWorldPath' — check the path to the installed game."
    }

    return $RimWorldPath
}
