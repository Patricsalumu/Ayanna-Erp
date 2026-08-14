Placement de SumatraPDF pour le build et le déploiement

But: inclure SumatraPDF portable dans le dossier `printers` du projet permet à l'application d'exécuter l'impression silencieuse sans dépendre des associations Windows.

Recommandation :
- Créez un dossier `printers` à la racine du projet (même niveau que `main.py`).
- Extrayez le binaire `SumatraPDF.exe` (portable) dans ce dossier.
- Pour tester localement, exécutez :

```bat
build\build_pyinstaller.bat
```

- Pour produire un unique exécutable `--onefile` (testez d'abord en `--onedir`), exécutez :

```bat
build\build_pyinstaller.bat onefile
```

Notes :
- Si vous embarquez `SumatraPDF.exe`, choisissez la version correspondant à l'architecture cible.
- L'application recherche `SumatraPDF.exe` dans cet ordre :
  1) dossier `_MEIPASS/printers` (extraction PyInstaller --onefile)
  2) `printers` à côté de l'exécutable (pour déploiements clients)
  3) `printers` dans le répertoire de travail actuel
  4) `PATH` système
  5) `C:\Program Files\SumatraPDF` et `C:\Program Files (x86)\SumatraPDF`

- Testez le binaire sur une machine propre pour valider le fonctionnement offline.
