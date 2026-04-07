<#
Build script PowerShell for Windows using PyInstaller.
Usage (PowerShell):
  - Open PowerShell in the project root (C:\Ayanna ERP\Ayanna-Erp)
  - Activate your virtualenv if any (recommended)
    .\venv\Scripts\Activate.ps1
  - Run this script:
    .\scripts\build_windows_pyinstaller.ps1

What it does:
 - Ensures an .ico exists (generates it from PNG using scripts/png_to_ico.py if missing)
 - Verifies PyInstaller is available in the active Python env and attempts an automatic install if not
 - Runs pyinstaller in console mode (--console) to produce a single-file executable
 - Adds the `data` folder as runtime data so assets (images, reports, etc.) are available

Notes:
 - Adjust the --add-data options below if you need to include other folders/files.
 - For a GUI build (no console), change --console to --windowed and optionally adjust logging.
#>

Set-StrictMode -Version Latest

# Resolve script/project paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

$iconPng = Join-Path $projectRoot 'data\images\icone_ayanna_erp.png'
$iconIco = Join-Path $projectRoot 'data\images\icone_ayanna_erp.ico'

# Ensure an .ico is available (generate from PNG if possible)
if (-not (Test-Path $iconIco)) {
    if (Test-Path $iconPng) {
        Write-Host "Icon .ico missing — attempting to generate from PNG..."
        try {
            & python .\scripts\png_to_ico.py
        } catch {
            Write-Warning "Error generating icon via script: $_"
        }

        if (-not (Test-Path $iconIco)) {
            Write-Warning "The .ico file was not created. Build will continue using PNG or without an icon."
            if (Test-Path $iconPng) { $iconToUse = $iconPng } else { $iconToUse = $null }
        } else { $iconToUse = $iconIco }
    } else {
        Write-Warning "No PNG icon found ($iconPng). Build will continue without icon."
        $iconToUse = $null
    }
} else { $iconToUse = $iconIco }

# Verify PyInstaller in the active Python environment; attempt install if missing
Write-Host "Checking for PyInstaller in the active Python environment..."
& python -c "import PyInstaller" 2> $null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "PyInstaller not found. Attempting automatic installation into the active Python environment..."
    try {
        Write-Host "Upgrading pip..."
        & python -m pip install --upgrade pip
        Write-Host "Installing PyInstaller..."
        & python -m pip install pyinstaller
        & python -c "import PyInstaller" 2> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Automatic installation failed. Please install PyInstaller manually in your venv: python -m pip install pyinstaller"
            exit 1
        } else { Write-Host "PyInstaller installed." }
    } catch {
        Write-Error "Automatic install of PyInstaller failed: $_. Please install manually: python -m pip install pyinstaller"
        exit 1
    }
} else { Write-Host "PyInstaller is available." }

# Compose PyInstaller arguments
$exeName = "AyannaERP"
$mainScript = "main.py"
$addDataArgs = @()
if (Test-Path (Join-Path $projectRoot 'data')) { $addDataArgs += "data;data" }

$pyArgs = @('--noconfirm', '--onefile', '--console', '--name', $exeName)
if ($iconToUse) { $pyArgs += '--icon'; $pyArgs += $iconToUse }
foreach ($d in $addDataArgs) { $pyArgs += '--add-data'; $pyArgs += $d }
$pyArgs += $mainScript

Write-Host "Running PyInstaller with arguments: $pyArgs"

try {
    & python -m PyInstaller @pyArgs
} catch {
    Write-Error "Unable to execute PyInstaller via 'python -m PyInstaller'. Verify it's installed in the active environment. Details: $_"
    exit 1
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed. Executable is typically in: dist\$exeName.exe"
} else {
    Write-Error "PyInstaller finished with errors (exit code $LASTEXITCODE). See the output above."
    exit $LASTEXITCODE
}
