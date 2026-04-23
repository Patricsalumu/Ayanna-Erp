"""
Helpers partagés pour le module hôtel.
"""
from datetime import datetime, date
from typing import Optional


# ---------------------------------------------------------------------------
# Formatage monétaire
# ---------------------------------------------------------------------------

def fmt_money(amount, symbol: str = 'FC') -> str:
    try:
        return f"{int(round(float(amount or 0))):,}".replace(',', ' ') + f" {symbol}"
    except Exception:
        return str(amount)


# ---------------------------------------------------------------------------
# Formatage dates
# ---------------------------------------------------------------------------

def fmt_date(dt, fmt: str = '%d/%m/%Y') -> str:
    if dt is None:
        return '-'
    if isinstance(dt, (datetime, date)):
        return dt.strftime(fmt)
    return str(dt)


def fmt_datetime(dt, fmt: str = '%d/%m/%Y %H:%M') -> str:
    if dt is None:
        return '-'
    if isinstance(dt, (datetime, date)):
        return dt.strftime(fmt)
    return str(dt)


# ---------------------------------------------------------------------------
# Couleurs de statut (QSS / CSS compatible hex)
# ---------------------------------------------------------------------------

ROOM_STATUS_COLORS = {
    'disponible':  '#27AE60',   # vert
    'occupee':     '#E74C3C',   # rouge
    'menage':      '#E67E22',   # orange
    'maintenance': '#95A5A6',   # gris
}

RESERVATION_STATUS_COLORS = {
    'en_attente': '#F39C12',
    'confirmee':  '#2980B9',
    'en_cours':   '#27AE60',
    'terminee':   '#7F8C8D',
    'annulee':    '#E74C3C',
}

PAYMENT_STATUS_COLORS = {
    'nonpaye': '#E74C3C',
    'partiel': '#E67E22',
    'paye':    '#27AE60',
    'credit':  '#8E44AD',
}


def room_status_label(status: str) -> str:
    labels = {
        'disponible':  'Disponible',
        'occupee':     'Occupée',
        'menage':      'Ménage',
        'maintenance': 'Maintenance',
    }
    return labels.get(status, status)


def reservation_status_label(status: str) -> str:
    labels = {
        'en_attente': 'En attente',
        'confirmee':  'Confirmée',
        'en_cours':   'En cours',
        'terminee':   'Terminée',
        'annulee':    'Annulée',
    }
    return labels.get(status, status)


def payment_status_label(status: str) -> str:
    labels = {
        'nonpaye': 'Non payé',
        'partiel': 'Partiel',
        'paye':    'Payé',
        'credit':  'Crédit',
    }
    return labels.get(status, status)


# ---------------------------------------------------------------------------
# Calcul nombre de nuits
# ---------------------------------------------------------------------------

def nb_nuits(d_entree: datetime, d_sortie: datetime) -> int:
    try:
        delta = (d_sortie.date() - d_entree.date()).days
        return max(delta, 1)
    except Exception:
        return 1
