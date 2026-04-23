# Script PowerShell pour compiler l'executable Ayanna ERP
# Usage: .\build_executable.ps1

param(
    [switch]$Clean = $false,
    [switch]$NoClean = $false
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPath = Join-Path $ProjectRoot "venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

# Vérifier l'existence du venv
if (-not (Test-Path $VenvPath)) {
    Write-Host "❌ Environnement virtuel non trouvé: $VenvPath" -ForegroundColor Red
    Write-Host "Création d'un nouvel environnement virtuel..." -ForegroundColor Yellow
    python -m venv $VenvPath
}

# Activer le venv
Write-Host "📦 Activation de l'environnement virtuel..." -ForegroundColor Cyan
& "$VenvPath\Scripts\Activate.ps1"

# Installer les dépendances si nécessaire
Write-Host "📥 Vérification des dépendances..." -ForegroundColor Cyan
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $RequirementsFile) {
    & python -m pip install -q -r $RequirementsFile
}
& python -m pip install -q PyInstaller

# Lancer le script de compilation
Write-Host "`n🚀 Lancement de la compilation..." -ForegroundColor Green
$BuildScript = Join-Path $ProjectRoot "build_executable.py"

if ($Clean) {
    Write-Host "🧹 Mode nettoyage activé" -ForegroundColor Yellow
    & python $BuildScript --clean
} else {
    & python $BuildScript
}

$ExitCode = $LASTEXITCODE
if ($ExitCode -eq 0) {
    Write-Host "`n✅ Compilation terminée avec succès!" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "`n❌ La compilation a échoué (code: $ExitCode)" -ForegroundColor Red
}

exit $ExitCode
