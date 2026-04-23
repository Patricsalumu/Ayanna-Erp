#!/usr/bin/env python3
"""
Script de construction d'exécutable pour Ayanna ERP
Compile l'application avec PyInstaller en intégrant tous les modules et ressources
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).parent.absolute()
OUTPUT_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_FILE = PROJECT_ROOT / "build_ayanna_complete.spec"

def get_all_modules(base_path: Path) -> List[str]:
    """Collecte tous les modules Python du projet"""
    modules = []
    for root, dirs, files in os.walk(base_path):
        # Exclure les dossiers __pycache__, .git, venv
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv', 'build', 'dist']]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
                rel_path = Path(root) / file
                modules.append(str(rel_path.relative_to(PROJECT_ROOT)))
    return modules

def collect_data_folders() -> List[Tuple[str, str]]:
    """Collecte tous les dossiers de données à inclure"""
    datas = []
    
    # Dossiers à inclure
    folders_to_include = [
        'ayanna_erp',
        'data',
        'logs',
        'Ayanna ERP',
    ]
    
    for folder in folders_to_include:
        folder_path = PROJECT_ROOT / folder
        if folder_path.exists():
            # Format: ('source', 'destination_in_bundle')
            datas.append((str(folder_path), folder))
            print(f"✓ Dossier inclus: {folder}")
    
    return datas

def find_icon() -> str:
    """Trouve le fichier icone"""
    possible_icons = [
        PROJECT_ROOT / "data" / "images" / "icone_ayanna_erp.ico",
        PROJECT_ROOT / "data" / "images" / "logo.ico",
        PROJECT_ROOT / "Ayanna ERP" / "images" / "icone.ico",
    ]
    
    for icon in possible_icons:
        if icon.exists():
            print(f"✓ Icone trouvée: {icon}")
            return str(icon)
    
    print("⚠ Aucune icone trouvée")
    return None

def create_spec_file():
    """Crée le fichier .spec personnalisé pour PyInstaller"""
    
    datas = collect_data_folders()
    icon = find_icon()
    
    # Imports cachés requis
    hidden_imports = [
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtSql',
        'reportlab',
        'reportlab.pdfgen.canvas',
        'reportlab.lib',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.lib.colors',
        'reportlab.platypus',
        'logging.handlers',
        'matplotlib',
        'matplotlib.backends.backend_qtagg',
        'pytz',
        'bcrypt',
        'dotenv',
        'PIL',
        'PIL.Image',
    ]
    
    # Construire la liste datas
    datas_str = "[\n"
    for src, dest in datas:
        datas_str += f"    ('{src}', '{dest}'),\n"
    datas_str += "]"
    
    # Construire la liste hidden_imports
    hidden_str = "[\n"
    for imp in hidden_imports:
        hidden_str += f"    '{imp}',\n"
    hidden_str += "]"
    
    # Construction du fichier spec
    icon_line = f"    icon=['{icon}']," if icon else "    icon=None,"
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Imports cachés requis
hiddenimports = {hidden_str}

# Ajouter les sous-modules de reportlab
hiddenimports += collect_submodules('reportlab')
hiddenimports += collect_submodules('sqlalchemy')

# Données à incluire (dossiers et fichiers)
datas = {datas_str}

# Ajouter les fichiers de données additionnels
datas += collect_data_files('reportlab')
datas += collect_data_files('PyQt6')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'PyQt6.Qt3DCore',
        'PyQt6.Qt3DRender',
        'PyQt6.Qt3DExtras',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngine',
        'QtWebEngineCore',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Ayanna ERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
{icon_line}
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Ayanna ERP',
)
'''
    
    with open(SPEC_FILE, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"\n✓ Fichier spec créé: {SPEC_FILE}")

def check_requirements():
    """Vérifie que les dépendances requises sont installées"""
    required = ['PyInstaller', 'PyQt6', 'SQLAlchemy', 'reportlab']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n❌ Dépendances manquantes: {', '.join(missing)}")
        print("\nInstallation des dépendances...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'PyInstaller', 'PyQt6', 'SQLAlchemy', 'reportlab', 'Pillow'
        ])
    else:
        print("✓ Toutes les dépendances requises sont installées")

def clean_build_dirs():
    """Nettoie les anciens fichiers de build"""
    print("\nNettoyage des anciens builds...")
    for directory in [BUILD_DIR, OUTPUT_DIR]:
        if directory.exists():
            try:
                shutil.rmtree(directory)
                print(f"✓ Dossier supprimé: {directory}")
            except Exception as e:
                print(f"⚠ Impossible de supprimer {directory}: {e}")

def build_executable():
    """Lance la compilation PyInstaller"""
    print("\n" + "="*60)
    print("COMPILATION DE L'EXÉCUTABLE AYANNA ERP")
    print("="*60 + "\n")
    
    # Vérifier les dépendances
    print("1️⃣ Vérification des dépendances...")
    check_requirements()
    
    # Créer le fichier spec
    print("\n2️⃣ Création du fichier de configuration...")
    create_spec_file()
    
    # Nettoyer les anciens builds
    print("\n3️⃣ Nettoyage des anciens builds...")
    clean_build_dirs()
    
    # Lancer PyInstaller
    print("\n4️⃣ Compilation de l'exécutable...")
    print(f"   PyInstaller -F {SPEC_FILE}\n")
    
    try:
        os.chdir(PROJECT_ROOT)
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '-F', str(SPEC_FILE)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n" + "="*60)
            print("✅ COMPILATION RÉUSSIE!")
            print("="*60)
            print(f"\n📦 Exécutable généré: {OUTPUT_DIR / 'Ayanna ERP.exe'}")
            print(f"📁 Emplacement: {OUTPUT_DIR}")
            return True
        else:
            print(result.stdout)
            print(result.stderr)
            print("\n" + "="*60)
            print("❌ ERREUR PENDANT LA COMPILATION")
            print("="*60)
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1 and sys.argv[1] == '--clean':
        clean_build_dirs()
        print("✓ Nettoyage complété")
        return
    
    success = build_executable()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
