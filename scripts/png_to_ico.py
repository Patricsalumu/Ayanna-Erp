#!/usr/bin/env python3
"""Convertit un fichier PNG en fichier ICO multi-tailles.
Usage: python scripts/png_to_ico.py

Le script cherche par défaut "data/images/icone ayanna erp.png" et écrit
"data/images/icone_ayanna_erp.ico".
"""
from PIL import Image
import os

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, 'data', 'images', 'icone_ayanna_erp.png')
OUT = os.path.join(ROOT, 'data', 'images', 'icone_ayanna_erp.ico')

SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main():
    if not os.path.exists(SRC):
        print(f"Fichier source introuvable: {SRC}")
        return 1

    try:
        im = Image.open(SRC)
        # Convertir en RGBA si nécessaire
        if im.mode not in ('RGBA', 'RGB'):
            im = im.convert('RGBA')

        im.save(OUT, format='ICO', sizes=SIZES)
        print(f"ICO créé: {OUT}")
        return 0
    except Exception as e:
        print(f"Erreur lors de la conversion: {e}")
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
