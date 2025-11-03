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
 - Runs pyinstaller in console mode (--console) to produce a single-file executable
 - Adds the `data` folder as runtime data so assets (images, reports, etc.) are available

Notes:
 - Adjust the --add-data options below if you need to include other folders/files.
 - For a GUI build (no console), change --console to --windowed and optionally adjust logging.
#>

Set-StrictMode -Version Latest

# Paths
# $MyInvocation.MyCommand.Definition is the script path; we want the project root (parent of the scripts folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

$iconPng = Join-Path $projectRoot "..\data\images\icone_ayanna_erp.png"
$iconIco = Join-Path $projectRoot "..\data\images\icone_ayanna_erp.ico"

# If .ico does not exist, try to generate it from the PNG
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
 - Runs pyinstaller in console mode (--console) to produce a single-file executable
 - Adds the `data` folder as runtime data so assets (images, reports, etc.) are available

Notes:
 - Adjust the --add-data options below if you need to include other folders/files.
 - For a GUI build (no console), change --console to --windowed and optionally adjust logging.
#>

Set-StrictMode -Version Latest

# Paths
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $projectRoot

$iconPng = Join-Path $projectRoot "..\data\images\icone_ayanna_erp.png"
$iconIco = Join-Path $projectRoot "..\data\images\icone_ayanna_erp.ico"

# If .ico does not exist, try to generate it from the PNG
if (-not (Test-Path $iconIco)) {
    if (Test-Path $iconPng) {
        Write-Host "Icon .ico missing — generating from PNG..."
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
         - Runs pyinstaller in console mode (--console) to produce a single-file executable
         - Adds the `data` folder as runtime data so assets (images, reports, etc.) are available

        Notes:
         - Adjust the --add-data options below if you need to include other folders/files.
         - For a GUI build (no console), change --console to --windowed and optionally adjust logging.
        #>

        Set-StrictMode -Version Latest

        # Paths
        $projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
        Set-Location $projectRoot

        $iconPng = Join-Path $projectRoot "data\images\icone_ayanna_erp.png"
        $iconIco = Join-Path $projectRoot "data\images\icone_ayanna_erp.ico"

        # If .ico does not exist, try to generate it from the PNG
        if (-not (Test-Path $iconIco)) {
            if (Test-Path $iconPng) {
                Write-Host "Icon .ico missing — generating from PNG..."
                python .\scripts\png_to_ico.py
                if (-not (Test-Path $iconIco)) {
                    Write-Warning "Le fichier .ico n'a pas été créé. Continuer en utilisant le PNG (moins optimal)."
                    $iconToUse = $iconPng
                } else {
                    $iconToUse = $iconIco
                }
            } else {
                Write-Warning "Aucun PNG d'icône trouvé ($iconPng). Le build continuera sans icône."
                $iconToUse = $null
            }
        } else {
            $iconToUse = $iconIco
        }

        # Ensure pyinstaller is installed
        try {
            python -c "import PyInstaller" 2> $null
        } catch {
            Write-Warning "PyInstaller non trouvé dans l'environnement Python actif. Installez-le: pip install pyinstaller"
        }

        # Build options
        $exeName = "AyannaERP"
        $mainScript = "main.py"
        $addDataArgs = @()
        # Add the entire data folder as runtime data (Windows syntax: source;dest)
        if (Test-Path (Join-Path $projectRoot 'data')) {
            $addDataArgs += "data;data"
        }

        # Compose PyInstaller argument list robustly to avoid quoting issues
        $pyArgs = @('--noconfirm', '--onefile', '--console', '--name', $exeName)
        if ($iconToUse) {
            $pyArgs += '--icon'
            $pyArgs += $iconToUse
        }
        foreach ($d in $addDataArgs) {
            $pyArgs += '--add-data'
            $pyArgs += $d
        }
        $pyArgs += $mainScript

        Write-Host "Running PyInstaller with arguments: $pyArgs"

        # Execute PyInstaller via the active Python to ensure venv usage (falls back to instructing installation)
        try {
            & python -m PyInstaller @pyArgs
        } catch {
            Write-Error "Impossible d'exécuter PyInstaller via 'python -m PyInstaller'. Vérifiez que PyInstaller est installé dans l'environnement actif (pip install pyinstaller). Détails: $_"
            exit 1
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Build terminé. L'exécutable se trouve généralement dans 'dist\$exeName.exe'"
        } else {
            Write-Error "PyInstaller a terminé avec des erreurs (exit code $LASTEXITCODE). Consultez la sortie ci-dessus."
        }
# Compose PyInstaller command
