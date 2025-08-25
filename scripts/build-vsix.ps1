<#
build-vsix.ps1 - Simple helper to build (and optionally install) the VSIX.

USAGE (run from repo root or any location):
    pwsh ./scripts/build-vsix.ps1                      # Build Release (auto-detect host arch)
    pwsh ./scripts/build-vsix.ps1 -Configuration Debug # Debug build
    pwsh ./scripts/build-vsix.ps1 -Platform x64        # Force x64
    pwsh ./scripts/build-vsix.ps1 -Project extensions/vs/WFormatVSIX.csproj
    pwsh ./scripts/build-vsix.ps1 -Install             # Build then launch VSIX installer

PARAMETERS:
    -Configuration   Build configuration (Debug | Release). Default: Release
    -Platform        Target platform (AnyCPU | x86 | x64 | ARM | ARM64). Auto-detected if omitted.
    -Project         Path to the .csproj for the VSIX (relative or absolute)
    -Install         If specified, locates VSIXInstaller.exe (via vswhere/PATH) and installs

REQUIREMENTS:
    - msbuild must be on PATH (e.g. from a Developer PowerShell prompt)
    - Visual Studio 2022 installed if using -Install

OUTPUT:
        - VSIX placed at <projectDir>/bin/<Configuration>/<AssemblyName>.vsix
            (Platform currently does not change output folder name; differentiate manually if needed.)

NOTES:
    - Does not auto-increment version; edit source.extension.vsixmanifest manually.
    - To uninstall: in VS, Extensions > Manage Extensions > Installed.
    - To debug: open the VSIX project in VS and F5 (experimental instance).
#>


Param(
    [string]$Configuration = "Release",
    [ValidateSet('AnyCPU','x86','x64','ARM','ARM64')][string]$Platform = '',
    [string]$Project = "extensions/vs/WFormatVSIX.csproj",
    [string]$OutputPath = (Join-Path (Get-Location) ""),
    [string]$Version = $null,
    [switch]$Install
)

$ErrorActionPreference = 'Stop'
function Write-Info($m){ Write-Host "[build-vsix] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[build-vsix] $m" -ForegroundColor Yellow }
function Write-Err($m){ Write-Host "[build-vsix] $m" -ForegroundColor Red }

# Auto-detect MSBuild Platform if not provided
if (-not $Platform) {
    try { $rawArch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString() } catch { $rawArch = $env:PROCESSOR_ARCHITECTURE }
    Write-Info "Auto-detected OS architecture: $rawArch"
    switch ($rawArch.ToUpperInvariant()) {
        'ARM64' { $Platform = 'ARM64' }
        'ARM'   { $Platform = 'ARM' }
        'X64'   { $Platform = 'x64' }
        'AMD64' { $Platform = 'x64' }
        'X86'   { $Platform = 'x86' }
        default { $Platform = 'AnyCPU' }
    }
    Write-Info "Auto-detected platform: $Platform"
} else {
    Write-Info "Using specified platform: $Platform"
}


$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Push-Location $repoRoot
try {
    if (-not (Test-Path $Project)) { Write-Err "Project not found: $Project"; exit 1 }

    # If Version is specified, update the VSIX manifest before build
    if ($Version) {
        $manifestPath = Join-Path (Split-Path $Project) 'source.extension.vsixmanifest'
        if (Test-Path $manifestPath) {
            Write-Info "Setting VSIX version to $Version in $manifestPath"
            [xml]$manifestXml = Get-Content $manifestPath
            $identityNode = $manifestXml.PackageManifest.Metadata.Identity
            if ($identityNode) {
                $identityNode.Version = $Version
                $manifestXml.Save($manifestPath)
            } else {
                Write-Warn "Could not find <Identity> node in manifest. Version not updated."
            }
        } else {
            Write-Warn "Manifest file not found: $manifestPath"
        }
    }

    $msbuild = "msbuild"
    if (-not (Get-Command $msbuild -ErrorAction SilentlyContinue)) { Write-Err "msbuild not found in PATH"; exit 1 }

    # Restore NuGet packages for the project so build has required dependencies (VSSDK packages etc.)
    try {
        Write-Info "Restoring NuGet packages for $Project"
        $nugetCmd = (Get-Command nuget -ErrorAction SilentlyContinue)?.Source
        if ($nugetCmd) {
            Write-Info "Using nuget: $nugetCmd"
            & $nugetCmd restore $Project
            if ($LASTEXITCODE -ne 0) { Write-Err "nuget restore failed."; exit $LASTEXITCODE }
        } else {
            Write-Info "nuget not found; attempting msbuild restore"
            $restoreArgs = @(
                $Project,
                '/t:Restore',
                "/p:Configuration=$Configuration",
                "/p:Platform=$Platform"
            )
            & $msbuild @restoreArgs
            if ($LASTEXITCODE -ne 0) { Write-Err "msbuild restore failed."; exit $LASTEXITCODE }
        }
    } catch {
        Write-Warn "Package restore encountered an error: $_"
    }

    $msbuildArgs = @(
        $Project,
        '/t:Rebuild',
        "/p:Configuration=$Configuration",
        "/p:Platform=$Platform",
        '/p:DeployExtension=false'
    )
    Write-Info "Running: msbuild $($msbuildArgs -join ' ')"
    & $msbuild @msbuildArgs
    if ($LASTEXITCODE -ne 0) { Write-Err "Build failed."; exit $LASTEXITCODE }

    $projXml = Select-Xml -Path $Project -XPath '/Project/PropertyGroup/AssemblyName' -ErrorAction SilentlyContinue
    $assemblyName = if ($projXml) { $projXml.Node.InnerText } else { [IO.Path]::GetFileNameWithoutExtension($Project) }

    $vsixPath = Join-Path (Split-Path $Project) "bin/$Configuration/$assemblyName.vsix"
    if (Test-Path $vsixPath) {
        Write-Info "Built VSIX: $vsixPath"
        $finalOutputPath = $OutputPath
        if ((Test-Path $finalOutputPath) -and (Test-Path $finalOutputPath -PathType Container)) {
            $finalOutputPath = Join-Path $finalOutputPath (Split-Path $vsixPath -Leaf)
        }
        $destDir = Split-Path $finalOutputPath -Parent
        if (-not (Test-Path $destDir)) {
            Write-Info "Creating output directory: $destDir"
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Move-Item -Path $vsixPath -Destination $finalOutputPath -Force
        Write-Info "VSIX moved to: $finalOutputPath"
        $vsixPath = $finalOutputPath
    } else {
        Write-Warn "VSIX not found at expected path: $vsixPath"
    }

    if ($Install) {
        $vswhere = Join-Path ${Env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
        $installerPath = $null
        if (Test-Path $vswhere) {
            $installRoot = & $vswhere -latest -requires Microsoft.Component.MSBuild -property installationPath 2>$null
            if ($LASTEXITCODE -eq 0 -and $installRoot) {
                $candidate = Join-Path $installRoot 'Common7/IDE/VSIXInstaller.exe'
                if (Test-Path $candidate) { $installerPath = $candidate }
            }
        }
        if (-not $installerPath) {
            # Fallback: try directly on PATH
            $cmd = Get-Command VSIXInstaller.exe -ErrorAction SilentlyContinue
            if ($cmd) { $installerPath = $cmd.Source }
        }
        if ($installerPath) {
            Write-Info "Installing via $installerPath"
            & $installerPath $vsixPath
            Write-Info "VSIX installation started. Check the install window for next step."
        } else {
            Write-Warn "VSIXInstaller.exe not found (skipping install). Add -Install after ensuring VS is installed with VSIX support."
        }
    }
}
finally { Pop-Location }
