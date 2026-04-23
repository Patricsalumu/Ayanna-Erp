@echo off
REM Script batch pour compiler l'executable Ayanna ERP
REM Double-cliquez sur ce fichier ou lancez-le depuis cmd.exe

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Couleurs
for /F %%A in ('echo prompt $H ^| cmd') do set "BS=%%A"

echo.
echo ================================================
echo    COMPILATION AYANNA ERP EXECUTABLE
echo ================================================
echo.

REM Vérifier l'existence du venv
if not exist "venv\" (
    echo [ERREUR] Environnement virtuel non trouvé
    echo Création d'un nouvel environnement...
    python -m venv venv
)

REM Activer le venv
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERREUR] Impossible d'activer l'environnement virtuel
    pause
    exit /b 1
)

echo [OK] Environnement virtuel activé

REM Installer les dépendances
echo.
echo [INFO] Installation des dépendances...
python -m pip install -q -r requirements.txt 2>nul
python -m pip install -q PyInstaller 2>nul

if errorlevel 1 (
    echo [ERREUR] Erreur lors de l'installation des dépendances
    pause
    exit /b 1
)

echo [OK] Dépendances installées

REM Lancer la compilation
echo.
echo [INFO] Lancement de la compilation Python...
echo.

python build_executable.py
if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation a échoué
    pause
    exit /b 1
)

echo.
echo ================================================
echo [OK] Compilation terminée avec succes!
echo ================================================
echo.

REM Afficher le chemin de l'exécutable
if exist "dist\Ayanna ERP.exe" (
    echo [OK] Executables genere: dist\Ayanna ERP.exe
    echo.
    pause
)

endlocal
