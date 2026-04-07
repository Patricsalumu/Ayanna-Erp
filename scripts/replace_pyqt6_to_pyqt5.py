"""
Script to replace PyQt5 imports with PyQt5 across the repository.
Usage (from project root):
    venv\Scripts\python.exe scripts\replace_pyqt6_to_pyqt5.py
This will:
- Replace occurrences of 'from PyQt6' -> 'from PyQt6'
- Replace occurrences of 'import PyQt6' -> 'import PyQt6'
- Update any textual mentions in `ayanna_erp/__init__.py` description
- Create a backup copy for each modified file with suffix .bak
"""
import os
import sys
import fnmatch

import re

root = os.path.abspath(os.getcwd())
changed = []

# Common pattern replacements to adapt PyQt5 → PyQt5 API differences
replacements = [
    # enums and flags
    (r'Qt\.AlignmentFlag\.AlignCenter', 'Qt.AlignmentFlag.AlignCenter'),
    (r'Qt\.AlignmentFlag\.AlignLeft', 'Qt.AlignmentFlag.AlignLeft'),
    (r'Qt\.AlignmentFlag\.AlignRight', 'Qt.AlignmentFlag.AlignRight'),
    (r'Qt\.AlignmentFlag\.AlignVCenter', 'Qt.AlignmentFlag.AlignVCenter'),
    (r'Qt\.WindowType\.WindowStaysOnTopHint', 'Qt.WindowType.WindowStaysOnTopHint'),
    (r'QFont\.Weight\.Bold', 'QFont.Weight.Bold'),
    (r'QFont\.Weight\.Normal', 'QFont.Weight.Normal'),
    (r'QFrame\.Shape\.HLine', 'QFrame.Shape.HLine'),
    (r'QFrame\.Shape\.VLine', 'QFrame.Shape.VLine'),
    (r'QFrame\.Shadow\.Sunken', 'QFrame.Shadow.Sunken'),
    (r'QFrame\.Shadow\.Raised', 'QFrame.Shadow.Raised'),
    (r'QSizePolicy\.Policy\.Expanding', 'QSizePolicy.Policy.Expanding'),
    (r'QLineEdit\.EchoMode\.Password', 'QLineEdit.EchoMode.Password'),
    (r'Qt\.WindowModality\.WindowModal', 'Qt.WindowModality.WindowModal'),
    (r'Qt\.AspectRatioMode\.KeepAspectRatio', 'Qt.AspectRatioMode.KeepAspectRatio'),
]

def apply_replacements(content: str) -> str:
    new = content
    # basic textual replacement for PyQt5 -> PyQt5
    new = new.replace('from PyQt6', 'from PyQt6').replace('import PyQt6', 'import PyQt6').replace('PyQt5', 'PyQt5')

    # apply regex replacements for enums and flags
    for pattern, repl in replacements:
        new = re.sub(pattern, repl, new)

    # remove CSS transform properties not supported by Qt stylesheets
    new = re.sub(r'transform\s*:\s*[^;]+;', '', new)

    return new


for dirpath, dirnames, filenames in os.walk(root):
    # skip virtual env and dist/build folders
    if any(part in ('venv', 'build', 'dist', '__pycache__') for part in dirpath.split(os.sep)):
        continue
    for fname in filenames:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        new = apply_replacements(content)
        if new != content:
            # backup
            with open(fpath + '.bak', 'w', encoding='utf-8') as b:
                b.write(content)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new)
            changed.append(fpath)

print('Modified files:')
for p in changed:
    print(' -', os.path.relpath(p, root))
print('\nDone. Please run tests and report any remaining API mismatches.')
