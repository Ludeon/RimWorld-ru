<#
Creates or removes .Decompiled/ — the game's C# code (Assembly-CSharp.dll,
which holds the code of the base game and all DLCs) decompiled by ilspycmd,
for reference while translating. ilspycmd is pinned in .config/dotnet-tools.json.
Safe to re-run: skips if the game assembly hasn't changed since the last
run, regenerates from scratch otherwise.
#>

function Find-GameAssembly {
    param([string]$RimWorldPath)

    $candidates = @(
        Get-ChildItem -Path "$RimWorldPath/*_Data/Managed/Assembly-CSharp.dll" -ErrorAction SilentlyContinue
        Get-Item -LiteralPath "$RimWorldPath/RimWorldMac.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll" -ErrorAction SilentlyContinue
    )
    return $candidates | Select-Object -First 1
}

function Set-Decompiled {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$RimWorldPath,
        [Parameter(Mandatory)][string]$RepoRoot,
        [switch]$Remove
    )

    # Any failure must stop before the stamp is written, even when called outside setup.ps1.
    $ErrorActionPreference = 'Stop'

    $outDir = "$RepoRoot/.Decompiled"
    $stampPath = "$outDir/.source-stamp"

    if ($Remove) {
        if ((Test-Path -LiteralPath $outDir) -and $PSCmdlet.ShouldProcess($outDir, 'Remove')) {
            Remove-Item -LiteralPath $outDir -Recurse -Force
            Write-Verbose "Removed: $outDir"
        }
        return
    }

    $assembly = Find-GameAssembly -RimWorldPath $RimWorldPath
    if (-not $assembly) {
        Write-Warning "Assembly-CSharp.dll not found under '$RimWorldPath', skipping decompilation."
        return
    }

    if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
        Write-Warning 'dotnet not found on PATH, skipping decompilation. Install the .NET SDK: https://dotnet.microsoft.com/download'
        return
    }

    # The stamp holds the hash of the assembly the current .Decompiled was made from.
    $hash = (Get-FileHash -LiteralPath $assembly.FullName -Algorithm SHA256).Hash
    if ((Test-Path -LiteralPath $stampPath) -and (Get-Content -LiteralPath $stampPath -Raw).Trim() -eq $hash) {
        Write-Verbose "Up to date: $outDir"
        return
    }

    if (-not $PSCmdlet.ShouldProcess($outDir, "Decompile $($assembly.FullName)")) {
        return
    }

    # Clear the contents rather than the folder itself: an open editor (e.g. VS Code with
    # the solution loaded) holds a handle on the folder and makes deleting it fail.
    if (Test-Path -LiteralPath $outDir) {
        Get-ChildItem -LiteralPath $outDir -Force | Remove-Item -Recurse -Force
    }
    else {
        New-Item -ItemType Directory -Path $outDir | Out-Null
    }

    Write-Host 'Decompiling the game code into .Decompiled (takes a few minutes)...'
    Push-Location $RepoRoot
    try {
        dotnet tool restore | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Error 'dotnet tool restore failed.' }

        # -r: resolve Unity/system types from the game's own Managed folder.
        dotnet tool run ilspycmd --disable-updatecheck --ignore-decompilation-errors -lv CSharp8_0 `
            -p -o $outDir -r $assembly.DirectoryName $assembly.FullName | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Error "ilspycmd failed with exit code $LASTEXITCODE." }
    }
    finally {
        Pop-Location
    }

    # A solution file lets the C# extension in VS Code (see .vscode/settings.json) load the project.
    $projectGuid = [guid]::NewGuid().ToString().ToUpperInvariant()
    @"

Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Assembly-CSharp", "Assembly-CSharp.csproj", "{$projectGuid}"
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{$projectGuid}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{$projectGuid}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{$projectGuid}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{$projectGuid}.Release|Any CPU.Build.0 = Release|Any CPU
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
EndGlobal
"@ | Set-Content -LiteralPath "$outDir/Assembly-CSharp.sln" -Encoding utf8BOM

    # Written last: an interrupted run leaves no stamp and is redone from scratch next time.
    Set-Content -LiteralPath $stampPath -Value $hash -NoNewline
    Write-Verbose "OK  $outDir"
}
