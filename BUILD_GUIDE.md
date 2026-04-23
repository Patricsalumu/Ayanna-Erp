# Guide de Compilation - Ayanna ERP Executable

Ce guide explique comment compiler l'application Ayanna ERP en exécutable Windows.

## 📋 Prérequis

- Python 3.8+
- Arguments système: `pyinstaller`, `PyQt6`, `SQLAlchemy`, `reportlab`
- Espace disque: ~500 MB pour la compilation

## 🚀 Méthode 1 - PowerShell (Windows - Recommandé)

### Étape 1: Ouvrir PowerShell
```powershell
# Depuis le dossier du projet
cd "c:\Ayanna ERP\Ayanna-Erp"
```

### Étape 2: Lancer la compilation
```powershell
.\build_executable.ps1
```

### Options
```powershell
# Nettoyer les anciens builds avant compilation
.\build_executable.ps1 -Clean

# Ne pas nettoyer les anciens builds
.\build_executable.ps1 -NoClean
```

## 🔧 Méthode 2 - Python Direct

### Étape 1: Vérifier l'environnement
```bash
# Activer le venv (Windows)
venv\Scripts\Activate.ps1

# Ou (Linux/Mac)
source venv/bin/activate
```

### Étape 2: Installer les dépendances
```bash
pip install -r requirements.txt
pip install PyInstaller
```

### Étape 3: Lancer la compilation
```bash
python build_executable.py
```

### Options
```bash
# Nettoyer les anciens builds
python build_executable.py --clean
```

## 📦 Ce qui est inclus dans l'exécutable

✅ **Modules:** Tous les modules du dossier `ayanna_erp/`
✅ **Données:** Dossiers `data/`, `logs/`, `Ayanna ERP/`
✅ **Ressources:** Images, logos, fichiers de configuration
✅ **Icone:** Logo intégré dans l'application

## ✨ Structure de la compilation

```
build_executable.py structure:

1. ✓ Vérification des dépendances
2. ✓ Création du fichier de configuration (spec)
3. ✓ Nettoyage des anciens builds
4. ✓ Compilation avec PyInstaller
5. ✓ Génération de l'exécutable
```

## 📍 Résultat

Après compilation réussie:
- **Exécutable:** `dist/Ayanna ERP.exe`
- **Dossier:** `dist/`
- **Taille:** ~50-100 MB

## ⚙️ Fichiers générés

- `build_ayanna_complete.spec` - Configuration PyInstaller
- `build/` - Fichiers intermédiaires de compilation
- `dist/` - Exécutable final

## 🐛 Dépannage

### Erreur: "Module not found"
```
Solution: Assurez-vous que toutes les dépendances sont installées
python -m pip install PyQt6 SQLAlchemy reportlab Pillow
```

### Erreur: "Icon file not found"
```
Solution: Vérifiez que le logo existe dans data/images/
Créez le dossier si nécessaire
```

### Compilation trop lente
```
Solution: Le premier build est plus lent
Les builds suivants bénéficient de la mise en cache
```

## 📝 Configuration personnalisée

Pour modifier la compilation, éditez `build_executable.py`:

```python
# Ajouter des modules cachés
hidden_imports.append('your_module')

# Ajouter des dossiers
datas.append(('path/to/folder', 'folder_name'))

# Changer le nom de l'exécutable
name='Custom Name',
```

## 🔗 Ressources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)

---

**Version:** 1.0
**Date:** 2026-04-16
**Auteur:** Ayanna ERP Build System
