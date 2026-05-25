"""
Helpers partagés pour le module hôtel.
"""
import os
import tempfile
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
# Calcul jours réels de séjour
# ---------------------------------------------------------------------------

def jours_reels(date_entree) -> int:
    """Calcule le nombre de jours réels de séjour depuis l'entrée jusqu'à maintenant.

    Règles :
    - Le premier jour (même calendaire que l'entrée) compte toujours 1.
    - Chaque jour calendaire supplémentaire ne compte comme complet
      que si l'heure courante est >= 10h00.
    Exemples :
      Entrée 18h00 → à 18h01              : 1 jour
      Entrée 18h00 → lendemain 09h59      : 1 jour
      Entrée 18h00 → lendemain 10h00+     : 2 jours
    """
    if date_entree is None:
        return 1
    now = datetime.now()
    delta_days = (now.date() - date_entree.date()).days
    if delta_days <= 0:
        return 1
    if now.hour >= 11:
        return delta_days + 1
    return delta_days


# ---------------------------------------------------------------------------
# Calcul nombre de nuits
# ---------------------------------------------------------------------------

def nb_nuits(d_entree: datetime, d_sortie: datetime) -> int:
    try:
        delta = (d_sortie.date() - d_entree.date()).days
        return max(delta, 1)
    except Exception:
        return 1


# ---------------------------------------------------------------------------
# Informations entreprise & formatage monétaire avec devise
# ---------------------------------------------------------------------------

def get_hotel_company_info() -> dict:
    """Récupère les infos entreprise (nom, logo, devise…) via EntrepriseController."""
    try:
        from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
        ctrl = EntrepriseController()
        info = ctrl.get_company_info_for_pdf()
        info['currency_symbol'] = ctrl.get_currency_symbol()
        return info
    except Exception:
        return {
            'name': 'HÔTEL', 'address': '', 'city': '', 'phone': '',
            'email': '', 'rccm': '', 'id_nat': '', 'slogan': '',
            'logo': None, 'currency': 'USD', 'currency_symbol': '$',
            'taux_de_change': None,
        }


def fmt_amount(amount, currency_symbol: str = '') -> str:
    """Formate un montant avec séparateur milliers + symbole devise.

    Exemples :
        fmt_amount(1500, '$')  → '1 500 $'
        fmt_amount(1500.5, 'FC') → '1 500,50 FC'
    """
    try:
        val = float(amount or 0)
        rounded = round(val, 2)
        if rounded.is_integer():
            s = f"{int(rounded):,}".replace(',', ' ')
        else:
            s = f"{rounded:,.2f}".replace(',', ' ').replace('.', ',')
        if currency_symbol:
            return f"{s} {currency_symbol}"
        return s
    except Exception:
        return str(amount)


def build_pdf_company_header(story: list, styles, company_info: dict,
                              avail_width_cm: float = 17.0) -> Optional[str]:
    """Ajoute l'en-tête entreprise (logo + coordonnées) à un story ReportLab.

    Retourne le chemin du fichier logo temporaire (ou None) pour nettoyage.
    """
    from reportlab.platypus import Table, TableStyle, Image, Paragraph, Spacer
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT

    logo_path = None
    if company_info.get('logo'):
        try:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(company_info['logo'])
                logo_path = f.name
        except Exception:
            logo_path = None

    lines = [f"<b>{company_info.get('name', 'HÔTEL')}</b>"]
    for key, prefix in [('address', ''), ('city', ''), ('phone', 'Tél : '),
                         ('email', 'Email : '), ('rccm', 'RCCM : '),
                         ('id_nat', 'ID Nat : ')]:
        v = company_info.get(key, '').strip()
        if v:
            lines.append(f"{prefix}{v}")
    slogan = company_info.get('slogan', '').strip()
    if slogan:
        lines.append(f"<i>{slogan}</i>")
    sym = company_info.get('currency_symbol', '$')
    if sym:
        lines.append(f"Devise : {company_info.get('currency', '')} ({sym})")

    company_text = '<br/>'.join(lines)
    txt_para = Paragraph(company_text, styles['Normal'])

    LOGO_W = 2.5 * cm
    txt_w = avail_width_cm * cm - (LOGO_W + 0.4 * cm if logo_path else 0)

    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=LOGO_W, height=LOGO_W)
            hdata = [[logo_img, txt_para]]
            cws = [LOGO_W + 0.2 * cm, txt_w]
        except Exception:
            hdata = [[txt_para]]
            cws = [avail_width_cm * cm]
    else:
        hdata = [[txt_para]]
        cws = [avail_width_cm * cm]

    hdr_tbl = Table(hdata, colWidths=cws)
    hdr_tbl.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 0.4 * cm))
    return logo_path
