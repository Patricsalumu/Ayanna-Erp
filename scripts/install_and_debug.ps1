<#
PowerShell helper to install Visual C++ Redistributable and run the application
with QT plugin debug enabled.

Usage examples:
  # Download & install x64 redistributable, then run debug
  .\install_and_debug.ps1 -ExePath "C:\path\to\YourApp.exe" -Arch x64 -InstallVC -RunDebug

  # Only run the exe with debug and save output
  .\install_and_debug.ps1 -ExePath "C:\path\to\YourApp.exe" -RunDebug

This script will:
- optionally download and silently install the VC++ redistributable (2015-2022)
- run the specified executable with $env:QT_DEBUG_PLUGINS='1' and save output to debug_plugins.txt

Note: To install VC++ the script must be run as Administrator. The script will
attempt to relaunch itself elevated if needed.
#>

Param(
    [Parameter(Mandatory=$false)]
    [string]$ExePath = ".\YourApp.exe",

    [Parameter(Mandatory=$false)]
    [ValidateSet('x86','x64')]
    [string]$Arch = 'x64',

    [Parameter(Mandatory=$false)]
    [switch]$InstallVC,

    [Parameter(Mandatory=$false)]
    [switch]$RunDebug
)

function Test-Admin {
    $current = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $current.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$tempDir = Join-Path $scriptDir 'temp_vc'
if (-not (Test-Path $tempDir)) { New-Item -Path $tempDir -ItemType Directory | Out-Null }

if ($InstallVC) {
    $vcFile = if ($Arch -eq 'x64') { 'vc_redist.x64.exe' } else { 'vc_redist.x86.exe' }
    # Microsoft redirect to latest stable redistributable
    $vcUrl = "https://aka.ms/vs/17/release/$vcFile"
    $vcLocal = Join-Path $tempDir $vcFile

    if (-not (Test-Path $vcLocal)) {
        Write-Host "Téléchargement de $vcFile depuis $vcUrl ..."
        try {
            Invoke-WebRequest -Uri $vcUrl -OutFile $vcLocal -UseBasicParsing -ErrorAction Stop
        } catch {
            Write-Error "Échec du téléchargement: $_.Exception.Message"
            exit 2
        }
    } else {
        Write-Host "$vcFile déjà présent dans $tempDir"
    }

    if (-not (Test-Admin)) {
        Write-Warning "L'installation du Visual C++ Redistributable nécessite des privilèges administrateur."
        Write-Host "Relancer le script en tant qu'administrateur ou taper 'Y' pour tenter l'élévation (UAC)."
        $resp = Read-Host "Élever et continuer ? (Y/N)"
        if ($resp -ne 'Y') { Write-Host 'Annulation de l installation.'; exit 1 }

        # Relaunch elevated with same arguments
        $argList = @()
        if ($PSBoundParameters.ContainsKey('ExePath')) { $argList += "-ExePath `"$ExePath`"" }
        if ($PSBoundParameters.ContainsKey('Arch')) { $argList += "-Arch $Arch" }
        if ($PSBoundParameters.ContainsKey('InstallVC')) { $argList += '-InstallVC' }
        if ($PSBoundParameters.ContainsKey('RunDebug')) { $argList += '-RunDebug' }
        $argString = $argList -join ' '
        Start-Process -FilePath 'powershell.exe' -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`" $argString" -Verb RunAs -Wait
        exit $LASTEXITCODE
    }

    Write-Host "Installation silencieuse de $vcLocal ..."
    Start-Process -FilePath $vcLocal -ArgumentList '/install','/quiet','/norestart' -Wait
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "L'installateur a retourné le code $LASTEXITCODE (possible erreur)."
    } else {
        Write-Host "Installation terminée."
    }
}

# Resolve full path to exe
try {
    $exeFull = Resolve-Path -Path $ExePath -ErrorAction Stop
} catch {
    Write-Error "Executable introuvable: $ExePath"
    exit 3
}

$exeFull = $exeFull.Path

if ($RunDebug) {
    $exeDir = Split-Path -Parent $exeFull
    $outFile = Join-Path $exeDir 'debug_plugins.txt'
    Write-Host "Lancement de $exeFull avec QT_DEBUG_PLUGINS=1. Sortie -> $outFile"

    # Set env for current process and start the exe piping stdout+stderr to file
    $env:QT_DEBUG_PLUGINS = '1'
    try {
        & "$exeFull" *>&1 | Tee-Object -FilePath $outFile
    } catch {
        Write-Error "Erreur lors de l'exécution: $_.Exception.Message"
        exit 4
    }
    Write-Host "Execution terminée. Fichier de log: $outFile"
}

Write-Host 'Script terminé.'
