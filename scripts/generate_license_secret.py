"""Générateur simple de LICENCE_SECRET.

Usage:
    python scripts/generate_license_secret.py

Ce script génère une clef secrète forte et l'ajoute au fichier `.env` à la racine
du projet si la variable LICENCE_SECRET n'existe pas encore. Il affiche la valeur
générée (ne pas la partager publiquement).
"""
import secrets
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / '.env'


def generate_secret(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def ensure_env_has_secret():
    secret = generate_secret()
    if not ENV_PATH.exists():
        print(f".env not found at {ENV_PATH}, creating a new one with LICENCE_SECRET")
        with open(ENV_PATH, 'w', encoding='utf-8') as f:
            f.write(f"LICENCE_SECRET={secret}\n")
        print("Wrote LICENCE_SECRET to .env")
        return secret

    # Read existing .env
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        if line.strip().startswith('LICENCE_SECRET='):
            print(".env already contains LICENCE_SECRET. No changes made.")
            val = line.strip().split('=', 1)[1]
            return val

    # Append secret to .env
    with open(ENV_PATH, 'a', encoding='utf-8') as f:
        f.write(f"\n# Generated licence secret\nLICENCE_SECRET={secret}\n")
    print("Appended LICENCE_SECRET to .env")
    return secret


if __name__ == '__main__':
    s = ensure_env_has_secret()
    print("LICENCE_SECRET:\n", s)