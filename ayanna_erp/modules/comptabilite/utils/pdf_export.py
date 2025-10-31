import tempfile
import os
from reportlab.platypus import Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def _write_logo_temp(logo_blob, suffix='.png'):
    if not logo_blob:
        return None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(logo_blob)
        tmp.flush()
        tmp.close()
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

    # Build header
    if logo_path:
        try:
            img = Image(logo_path, width=2*72/2.54, height=2*72/2.54)  # approx 2cm
            elems.append(img)
        except Exception:
            pass

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
