import tempfile
import os
import weakref
import atexit
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Ensemble des chemins temporaires écrits pour les logos (pour nettoyage de secours)
_TEMP_LOGO_PATHS = set()


def _remove_temp_path(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    try:
        _TEMP_LOGO_PATHS.discard(path)
    except Exception:
        pass


# Nettoyage au exit pour s'assurer qu'aucun fichier temporaire ne demeure
atexit.register(lambda: [ _remove_temp_path(p) for p in list(_TEMP_LOGO_PATHS) ])


def _write_logo_temp(logo_blob, suffix='.png'):
    if not logo_blob:
        return None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(logo_blob)
        tmp.flush()
        tmp.close()
        # Enregistrer le path pour un nettoyage éventuel
        _TEMP_LOGO_PATHS.add(tmp.name)
        return tmp.name
    except Exception:
        return None


def get_entreprise_info(controller=None, entreprise_id=None):
    """Retourne un dict avec keys: name, address, phone, email, logo (bytes)"""
    try:
        from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
        ec = EntrepriseController() if controller is None else getattr(controller, 'entreprise_controller', EntrepriseController())
        if entreprise_id is None:
            entreprise_id = getattr(controller, 'entreprise_id', None) if controller is not None else None
        return ec.get_current_enterprise(entreprise_id) or {}
    except Exception:
        return {}


def prepare_header_elements(controller=None, entreprise_id=None, title=None):
    """Renvoie une liste d'éléments ReportLab (Image/Paragraph/Spacer) pour l'entête.
    Inclut le logo si disponible et le nom de l'entreprise.
    """
    styles = getSampleStyleSheet()
    elems = []
    info = get_entreprise_info(controller, entreprise_id)
    company_name = info.get('name') if isinstance(info, dict) else None
    logo_blob = None
    if isinstance(info, dict):
        logo_blob = info.get('logo')

    # Mention générée
    from datetime import datetime
    mention_style = ParagraphStyle('Mention', parent=styles['Normal'], alignment=1, textColor=colors.HexColor('#666666'), fontSize=9)
    mention = Paragraph(f"Généré par {company_name or 'Ayanna ERP'} - {datetime.now().strftime('%d/%m/%Y %H:%M')}", mention_style)

    # Logo handling
    logo_path = None
    if logo_blob:
        logo_path = _write_logo_temp(logo_blob)
    # fallback to local favicon if exists
    if not logo_path:
        try:
            base = os.path.dirname(__file__)
            candidate = os.path.join(base, '../../images/favicon.ico')
            if os.path.exists(candidate):
                logo_path = candidate
        except Exception:
            logo_path = None

    # Build a two-column header: logo | company info
    left = []
    if logo_path:
        try:
            img = Image(logo_path, width=2*72/2.54, height=2*72/2.54)  # approx 2cm
            # Attacher un finalize pour supprimer le fichier temporaire lorsque
            # l'objet Image sera garbage-collected. Ceci permet un nettoyage
            # automatique sans avoir à modifier tous les appels producteurs de PDF.
            try:
                weakref.finalize(img, _remove_temp_path, logo_path)
            except Exception:
                # Au minimum laisser le chemin enregistré pour le nettoyage atexit
                pass
            left.append(img)
        except Exception:
            left.append(Spacer(1, 2*72/2.54))
    else:
        left.append(Spacer(1, 2*72/2.54))

    # Right column: company name and contact details
    right_lines = []
    name_style = ParagraphStyle('CompanyName', parent=styles['Heading3'], fontSize=12, leading=14)
    info_style = ParagraphStyle('CompanyInfo', parent=styles['Normal'], fontSize=9, leading=11)
    if company_name:
        right_lines.append(Paragraph(f"<b>{company_name}</b>", name_style))

    # Address, phone, email, rccm
    if isinstance(info, dict):
        address = info.get('address')
        phone = info.get('phone')
        email = info.get('email')
        rccm = info.get('rccm') or info.get('rccm_number') or info.get('rccm_no')
        if address:
            right_lines.append(Paragraph(address, info_style))
        if phone:
            right_lines.append(Paragraph(f"Tél : {phone}", info_style))
        if email:
            right_lines.append(Paragraph(f"Email : {email}", info_style))
        if rccm:
            right_lines.append(Paragraph(f"RCCM : {rccm}", info_style))

    # Combine left and right into a Table for horizontal layout
    right_box = []
    for p in right_lines:
        right_box.append(p)
    # Ensure at least one spacer to avoid empty cell problems
    if not right_box:
        right_box = [Spacer(1, 12)]

    data = [[left[0], right_box]]
    tbl = Table(data, colWidths=[2*72/2.54 + 6, None])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 6))

    if title:
        title_style = ParagraphStyle('Titre', parent=styles['Heading2'], alignment=1, fontSize=14)
        elems.append(Paragraph(title, title_style))
    elems.append(Spacer(1, 4))
    elems.append(mention)
    elems.append(Spacer(1, 8))
    return elems


def format_amount(value, controller=None):
    """Format a numeric value using controller.format_amount if available, otherwise fallback to 2 decimals."""
    try:
        if controller and hasattr(controller, 'format_amount'):
            return controller.format_amount(value)
    except Exception:
        pass
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return str(value)


def cleanup_temp_path(path):
    """Supprime un chemin temporaire précédemment enregistré par _write_logo_temp.
    Ne fera rien si le chemin n'est pas géré comme temporaire par ce module.
    """
    try:
        if path in _TEMP_LOGO_PATHS:
            _remove_temp_path(path)
    except Exception:
        pass
