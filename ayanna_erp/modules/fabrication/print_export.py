from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.utils import ImageReader
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import Production, FabricationRule
from ayanna_erp.modules.core.models import CoreProduct
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from datetime import datetime
from decimal import Decimal
import io


def _format_amount(val):
    try:
        return f"{float(val):,.3f}"
    except Exception:
        return str(val)


def _get_layout_config(ent_info: dict):
    # Defaults; allow company preferences to override via ent_info['pdf_layout'] dict
    layout = {
        'logo_align': 'left',  # 'left' or 'right'
        'left_margin_mm': 20,
        'right_margin_mm': 20,
        'top_margin_mm': 20,
        'bottom_margin_mm': 15,
        'heading_font': 'Helvetica-Bold',
        'normal_font': 'Helvetica',
        'heading_size': 14,
        'normal_size': 10,
        'logo_width_mm': 30,
    }
    try:
        pdf_layout = ent_info.get('pdf_layout') or {}
        layout.update({k: pdf_layout[k] for k in pdf_layout if k in layout})
    except Exception:
        pass
    return layout


def _build_header_table(ent_info: dict, styles, layout_cfg):
    # Builds a two-column header: logo + company info (or reversed)
    logo_cell = ''
    info_cell = ''
    elems = []
    # Company info paragraphs
    info_lines = []
    if ent_info.get('name'):
        info_lines.append(Paragraph(f"<b>{ent_info.get('name')}</b>", styles['Normal']))
    if ent_info.get('address'):
        info_lines.append(Paragraph(ent_info.get('address'), styles['Normal']))
    if ent_info.get('phone'):
        info_lines.append(Paragraph(f"Tél: {ent_info.get('phone')}", styles['Normal']))
    if ent_info.get('email'):
        info_lines.append(Paragraph(ent_info.get('email'), styles['Normal']))

    # Logo
    img_flow = None
    if ent_info.get('logo'):
        try:
            img_buf = io.BytesIO(ent_info.get('logo'))
            img = Image(img_buf, width=layout_cfg['logo_width_mm'] * mm, height=layout_cfg['logo_width_mm'] * 0.6 * mm)
            img.hAlign = 'LEFT'
            img_flow = img
        except Exception:
            img_flow = None

    # Compose table depending on logo_align
    if layout_cfg['logo_align'] == 'right':
        left_cell = info_lines
        right_cell = img_flow or ''
    else:
        left_cell = img_flow or ''
        right_cell = info_lines

    table = Table([[left_cell, right_cell]], colWidths=[layout_cfg['logo_width_mm'] * mm + 6 * mm, None])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table


def export_production_pdf(production_id: int, file_path: str, paper: str = 'A4') -> bool:
    db = DatabaseManager()
    session = db.get_session()
    try:
        prod: Production = session.query(Production).filter_by(id=production_id).first()
        if not prod:
            raise Exception('Production introuvable')

        prod_code = prod.production_code or f"#{prod.id}"
        prod_name = prod.product.name if prod.product else str(prod.product_id)
        date_str = (prod.created_at or datetime.utcnow()).strftime('%Y-%m-%d %H:%M')

        ent_ctrl = EntrepriseController()
        ent_info = ent_ctrl.get_company_info_for_pdf() or {}
        layout_cfg = _get_layout_config(ent_info)

        if paper == '80mm':
            # narrow receipt style using canvas
            width = 80 * mm
            height = 300 * mm
            c = canvas.Canvas(file_path, pagesize=(width, height))
            y = height - 6 * mm
            # header on canvas
            if ent_info.get('logo'):
                try:
                    img = ImageReader(io.BytesIO(ent_info.get('logo')))
                    c.drawImage(img, 6 * mm, y - 18 * mm, width=20 * mm, height=18 * mm)
                    x_offset = 28 * mm
                except Exception:
                    x_offset = 6 * mm
            else:
                x_offset = 6 * mm
            c.setFont('Helvetica-Bold', 10)
            c.drawString(x_offset, y, ent_info.get('name', ''))
            y -= 8 * mm
            c.setFont('Helvetica', 9)
            c.drawString(6 * mm, y, f"Production: {prod_code}")
            y -= 6 * mm
            c.drawString(6 * mm, y, f"Date: {date_str}")
            y -= 6 * mm
            c.drawString(6 * mm, y, f"Produit: {prod_name}")
            y -= 8 * mm
            c.drawString(6 * mm, y, f"Qté prévue: {_format_amount(prod.planned_quantity)} | Produite: {_format_amount(prod.produced_quantity)}")
            y -= 8 * mm
            c.drawString(6 * mm, y, "--- Matières consommées ---")
            y -= 6 * mm
            for it in prod.items:
                name = (it.raw_material.name if it.raw_material else str(it.raw_material_id))
                line = f"{name[:20]} {_format_amount(it.consumed_quantity)}"
                c.drawString(6 * mm, y, line)
                y -= 5 * mm
                if y < 20 * mm:
                    c.showPage()
                    y = height - 10 * mm
            c.save()
            return True

        # A4 flow using Platypus
        left_margin = layout_cfg['left_margin_mm'] * mm
        right_margin = layout_cfg['right_margin_mm'] * mm
        top_margin = layout_cfg['top_margin_mm'] * mm
        bottom_margin = layout_cfg['bottom_margin_mm'] * mm
        doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=left_margin, rightMargin=right_margin, topMargin=top_margin, bottomMargin=bottom_margin)
        styles = getSampleStyleSheet()
        # override base font sizes
        styles.add(ParagraphStyle(name='ProductionHeading', fontName=layout_cfg['heading_font'], fontSize=layout_cfg['heading_size'], leading=layout_cfg['heading_size'] + 2))
        styles['Normal'].fontName = layout_cfg['normal_font']
        styles['Normal'].fontSize = layout_cfg['normal_size']

        elems = []
        # header table
        header = _build_header_table(ent_info, styles, layout_cfg)
        elems.append(header)
        elems.append(Spacer(1, 6))

        elems.append(Paragraph(f"Production: {prod_code}", styles['ProductionHeading']))
        elems.append(Paragraph(f"Date: {date_str}", styles['Normal']))
        elems.append(Paragraph(f"Produit: {prod_name}", styles['Normal']))
        elems.append(Paragraph(f"Quantité prévue: {_format_amount(prod.planned_quantity)} — Produite: {_format_amount(prod.produced_quantity)}", styles['Normal']))
        elems.append(Paragraph(f"Opérateur: {prod.operator_name or ''}", styles['Normal']))
        elems.append(Spacer(1, 6))

        # Materials table
        data = [["Matière première", "Qté prévue", "Qté consommée"]]
        for it in prod.items:
            name = it.raw_material.name if it.raw_material else str(it.raw_material_id)
            planned = _format_amount(it.planned_quantity)
            consumed = _format_amount(it.consumed_quantity)
            data.append([name, planned, consumed])

        table = Table(data, colWidths=[100 * mm, 35 * mm, 35 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#dddddd')),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("VALIGN", (0, 0), (-1, -1), 'MIDDLE')
        ]))
        elems.append(table)

        if prod.notes:
            elems.append(Spacer(1, 6))
            elems.append(Paragraph("Notes:", styles['Normal']))
            elems.append(Paragraph(prod.notes, styles['Normal']))

        doc.build(elems)
        return True

    except Exception as e:
        print(f"Erreur export production PDF: {e}")
        return False
    finally:
        try:
            session.close()
        except Exception:
            pass


def export_rule_pdf(rule_id: int, file_path: str, paper: str = 'A4') -> bool:
    db = DatabaseManager()
    session = db.get_session()
    try:
        rule: FabricationRule = session.query(FabricationRule).filter_by(id=rule_id).first()
        if not rule:
            raise Exception('Règle introuvable')

        title = f"Nomenclature #{rule.id} - Produit {rule.product.name if rule.product else rule.product_id}"
        ent_ctrl = EntrepriseController()
        ent_info = ent_ctrl.get_company_info_for_pdf() or {}
        layout_cfg = _get_layout_config(ent_info)

        if paper == '80mm':
            width = 80 * mm
            height = 250 * mm
            c = canvas.Canvas(file_path, pagesize=(width, height))
            y = height - 8 * mm
            if ent_info.get('logo'):
                try:
                    img = ImageReader(io.BytesIO(ent_info.get('logo')))
                    c.drawImage(img, 6 * mm, y - 16 * mm, width=18 * mm, height=16 * mm)
                    x_offset = 26 * mm
                except Exception:
                    x_offset = 6 * mm
            else:
                x_offset = 6 * mm
            c.setFont('Helvetica-Bold', 10)
            c.drawString(x_offset, y, ent_info.get('name', ''))
            y -= 6 * mm
            c.setFont('Helvetica', 9)
            c.drawString(6 * mm, y, f"{title}")
            y -= 8 * mm
            c.drawString(6 * mm, y, "-- Composants --")
            y -= 6 * mm
            for it in rule.items:
                name = it.raw_material.name if it.raw_material else str(it.raw_material_id)
                line = f"{name[:20]} {_format_amount(it.quantity_required)}"
                c.drawString(6 * mm, y, line)
                y -= 5 * mm
                if y < 20 * mm:
                    c.showPage()
                    y = height - 8 * mm
            c.save()
            return True

        # A4
        left_margin = layout_cfg['left_margin_mm'] * mm
        right_margin = layout_cfg['right_margin_mm'] * mm
        top_margin = layout_cfg['top_margin_mm'] * mm
        bottom_margin = layout_cfg['bottom_margin_mm'] * mm
        doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=left_margin, rightMargin=right_margin, topMargin=top_margin, bottomMargin=bottom_margin)
        styles = getSampleStyleSheet()
        styles['Normal'].fontName = layout_cfg['normal_font']
        styles['Normal'].fontSize = layout_cfg['normal_size']
        elems = []
        elems.append(_build_header_table(ent_info, styles, layout_cfg))
        elems.append(Spacer(1, 6))
        elems.append(Paragraph(title, styles['Heading2']))
        elems.append(Paragraph(f"Quantité sortie: {_format_amount(rule.output_quantity)}", styles['Normal']))
        elems.append(Spacer(1, 6))
        data = [["Composant", "Qté requise"]]
        for it in rule.items:
            name = it.raw_material.name if it.raw_material else str(it.raw_material_id)
            data.append([name, _format_amount(it.quantity_required)])
        table = Table(data, colWidths=[130 * mm, 40 * mm])
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.black), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#eeeeee'))]))
        elems.append(table)
        if rule.notes:
            elems.append(Spacer(1, 6))
            elems.append(Paragraph("Notes:", styles['Normal']))
            elems.append(Paragraph(rule.notes, styles['Normal']))
        doc.build(elems)
        return True

    except Exception as e:
        print(f"Erreur export règle PDF: {e}")
        return False
    finally:
        try:
            session.close()
        except Exception:
            pass


def export_product_pdf(product_id: int, file_path: str, paper: str = 'A4') -> bool:
    db = DatabaseManager()
    session = db.get_session()
    try:
        prod: CoreProduct = session.query(CoreProduct).filter_by(id=product_id).first()
        if not prod:
            raise Exception('Produit introuvable')

        title = f"Fiche produit: {prod.name or prod.id}"
        ent_ctrl = EntrepriseController()
        ent_info = ent_ctrl.get_company_info_for_pdf() or {}
        layout_cfg = _get_layout_config(ent_info)

        if paper == '80mm':
            width = 80 * mm
            height = 160 * mm
            c = canvas.Canvas(file_path, pagesize=(width, height))
            y = height - 8 * mm
            if ent_info.get('logo'):
                try:
                    img = ImageReader(io.BytesIO(ent_info.get('logo')))
                    c.drawImage(img, 6 * mm, y - 16 * mm, width=18 * mm, height=16 * mm)
                    x_offset = 26 * mm
                except Exception:
                    x_offset = 6 * mm
            else:
                x_offset = 6 * mm
            c.setFont('Helvetica-Bold', 10)
            c.drawString(x_offset, y, ent_info.get('name', ''))
            y -= 6 * mm
            c.setFont('Helvetica', 9)
            c.drawString(6 * mm, y, f"Réf: {prod.reference or ''}")
            y -= 6 * mm
            c.drawString(6 * mm, y, f"Prix: {prod.selling_price if hasattr(prod, 'selling_price') else ''}")
            y -= 6 * mm
            c.drawString(6 * mm, y, f"Type: {getattr(prod, 'product_type', '')}")
            y -= 6 * mm
            c.save()
            return True

        left_margin = layout_cfg['left_margin_mm'] * mm
        right_margin = layout_cfg['right_margin_mm'] * mm
        top_margin = layout_cfg['top_margin_mm'] * mm
        bottom_margin = layout_cfg['bottom_margin_mm'] * mm
        doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=left_margin, rightMargin=right_margin, topMargin=top_margin, bottomMargin=bottom_margin)
        styles = getSampleStyleSheet()
        styles['Normal'].fontName = layout_cfg['normal_font']
        styles['Normal'].fontSize = layout_cfg['normal_size']
        elems = []
        elems.append(_build_header_table(ent_info, styles, layout_cfg))
        elems.append(Spacer(1, 6))
        elems.append(Paragraph(title, styles['Heading2']))
        elems.append(Paragraph(f"Référence: {prod.reference or ''}", styles['Normal']))
        elems.append(Paragraph(f"Prix vente: {getattr(prod, 'selling_price', '')}", styles['Normal']))
        elems.append(Paragraph(f"Type produit: {getattr(prod, 'product_type', '')}", styles['Normal']))
        if getattr(prod, 'description', None):
            elems.append(Spacer(1, 6))
            elems.append(Paragraph(prod.description, styles['Normal']))
        doc.build(elems)
        return True

    except Exception as e:
        print(f"Erreur export produit PDF: {e}")
        return False
    finally:
        try:
            session.close()
        except Exception:
            pass
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.utils import ImageReader
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import Production, FabricationRule, FabricationRuleItem
from ayanna_erp.modules.core.models import CoreProduct
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from datetime import datetime
from decimal import Decimal
import io


def _format_amount(val):
    try:
        return f"{float(val):,.3f}"
    except Exception:
        return str(val)


def _get_pdf_margins(ent_info):
    # ent_info may contain custom margins in mm as dict: {'left':10,'right':10,'top':20,'bottom':15}
    m = ent_info.get('pdf_margins') if ent_info else None
    if not m or not isinstance(m, dict):
        return (20 * mm, 20 * mm, 20 * mm, 15 * mm)  # left, right, top, bottom
    return (m.get('left', 20) * mm, m.get('right', 20) * mm, m.get('top', 20) * mm, m.get('bottom', 15) * mm)


def _build_header_flowable(ent_info, styles, max_logo_width=40 * mm, logo_height=25 * mm, logo_align='left'):
    # Returns a list of flowables (Table) to place as header with logo on left or right
    elems = []
    name = ent_info.get('name', '') if ent_info else ''
    address = ent_info.get('address', '') if ent_info else ''
    phone = ent_info.get('phone', '') if ent_info else ''

    logo_flow = None
    if ent_info and ent_info.get('logo'):
        try:
            img = Image(io.BytesIO(ent_info.get('logo')))
            # scale preserving aspect ratio
            img.drawWidth = max_logo_width
            img.drawHeight = logo_height
            logo_flow = img
        except Exception:
            logo_flow = None

    header_text = []
    if name:
        header_text.append(Paragraph(f"<b>{name}</b>", styles['Heading3']))
    if address:
        header_text.append(Paragraph(address, styles['Normal']))
    if phone:
        header_text.append(Paragraph(phone, styles['Normal']))

    # Build table: either [logo | text] or [text | logo]
    if logo_flow:
        if logo_align == 'right':
            data = [[header_text, logo_flow]]
            col_widths = [None, max_logo_width + 6 * mm]
        else:
            data = [[logo_flow, header_text]]
            col_widths = [max_logo_width + 6 * mm, None]
        tbl = Table(data, colWidths=col_widths)
        tbl.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
        elems.append(tbl)
    else:
        # No logo -> just text
        for p in header_text:
            elems.append(p)
    elems.append(Spacer(1, 6))
    return elems


def export_production_pdf(production_id: int, file_path: str, paper: str = 'A4') -> bool:
    db = DatabaseManager()
    session = db.get_session()
    ent_ctrl = EntrepriseController()
    ent_info = ent_ctrl.get_company_info_for_pdf() or {}

    try:
        prod = session.query(Production).filter_by(id=production_id).first()
        if not prod:
            raise Exception("Production introuvable")

        prod_code = prod.production_code or f"#{prod.id}"
        prod_name = prod.product.name if prod.product else str(prod.product_id)
        date_str = (prod.created_at or datetime.utcnow()).strftime('%Y-%m-%d %H:%M')

        if paper == '80mm':
            width = 80 * mm
            height = 300 * mm
            c = canvas.Canvas(file_path, pagesize=(width, height))
            y = height - 10 * mm
            c.setFont('Helvetica-Bold', 10)
            # header: simple
            if ent_info.get('logo'):
                try:
                    img = ImageReader(io.BytesIO(ent_info.get('logo')))
                    c.drawImage(img, 6 * mm, y - 18 * mm, width=20 * mm, height=18 * mm)
                    x_offset = 28 * mm
                except Exception:
                    x_offset = 6 * mm
            else:
                x_offset = 6 * mm
            c.drawString(x_offset, y, ent_info.get('name', ''))
            y -= 6 * mm
            c.setFont('Helvetica', 9)
            c.drawString(6 * mm, y, f"Date: {date_str}")
            y -= 6 * mm
            c.drawString(6 * mm, y, f"Produit: {prod_name}")
            y -= 8 * mm
            c.drawString(6 * mm, y, f"Qté prévue: {_format_amount(prod.planned_quantity)} | Produite: {_format_amount(prod.produced_quantity)}")
            y -= 8 * mm
            c.drawString(6 * mm, y, f"Opérateur: {prod.operator_name or ''}")
            y -= 10 * mm
            c.drawString(6 * mm, y, "--- Matières consommées ---")
            y -= 6 * mm
            for it in prod.items:
                name = (it.raw_material.name if it.raw_material else str(it.raw_material_id))
                line = f"{name[:20]} { _format_amount(it.consumed_quantity)}"
                c.drawString(6 * mm, y, line)
                y -= 5 * mm
                if y < 20 * mm:
                    c.showPage()
                    y = height - 10 * mm
            c.save()
            return True

        # A4 flow using platypus
        left_m, right_m, top_m, bottom_m = _get_pdf_margins(ent_info)
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=right_m, leftMargin=left_m, topMargin=top_m, bottomMargin=bottom_m)
        base_styles = getSampleStyleSheet()
        # tweak styles
        base_styles.add(ParagraphStyle(name='Heading2Centered', parent=base_styles['Heading2'], alignment=TA_CENTER))
        base_styles.add(ParagraphStyle(name='Heading3', parent=base_styles['Heading3'], alignment=TA_LEFT))

        elems = []
        # header with configurable logo align
        logo_align = ent_info.get('logo_align', 'left')
        elems.extend(_build_header_flowable(ent_info, base_styles, max_logo_width=40 * mm, logo_height=25 * mm, logo_align=logo_align))

        elems.append(Paragraph(f"Production: {prod_code}", base_styles['Heading2']))
        elems.append(Paragraph(f"Date: {date_str}", base_styles['Normal']))
        elems.append(Paragraph(f"Produit: {prod_name}", base_styles['Normal']))
        elems.append(Paragraph(f"Quantité prévue: {_format_amount(prod.planned_quantity)} — Produite: {_format_amount(prod.produced_quantity)}", base_styles['Normal']))
        elems.append(Paragraph(f"Opérateur: {prod.operator_name or ''}", base_styles['Normal']))
        elems.append(Spacer(1, 6))

        data = [["Matière première", "Qté prévue", "Qté consommée"]]
        for it in prod.items:
            name = it.raw_material.name if it.raw_material else str(it.raw_material_id)
            planned = _format_amount(it.planned_quantity)
            consumed = _format_amount(it.consumed_quantity)
            data.append([name, planned, consumed])

        table = Table(data, colWidths=[100 * mm, 35 * mm, 35 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#dddddd')),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("VALIGN", (0, 0), (-1, -1), 'MIDDLE')
        ]))
        elems.append(table)

        if prod.notes:
            elems.append(Spacer(1, 6))
            elems.append(Paragraph("Notes:", base_styles['Normal']))
            elems.append(Paragraph(prod.notes, base_styles['Normal']))

        doc.build(elems)
        return True

    except Exception as e:
        print(f"Erreur export production PDF: {e}")
        return False
    finally:
        try:
            session.close()
        except Exception:
            pass


def export_rule_pdf(rule_id: int, file_path: str, paper: str = 'A4') -> bool:
    db = DatabaseManager()
    session = db.get_session()
    ent_ctrl = EntrepriseController()
    ent_info = ent_ctrl.get_company_info_for_pdf() or {}
    try:
        rule = session.query(FabricationRule).filter_by(id=rule_id).first()
        if not rule:
            raise Exception("Règle introuvable")

        title = f"Nomenclature #{rule.id} - Produit {rule.product.name if rule.product else rule.product_id}"

        if paper == '80mm':
            width = 80 * mm
            height = 250 * mm
            c = canvas.Canvas(file_path, pagesize=(width, height))
            y = height - 8 * mm
            c.setFont('Helvetica-Bold', 10)
            if ent_info.get('logo'):
                try:
                    img = ImageReader(io.BytesIO(ent_info.get('logo')))
                    c.drawImage(img, 6 * mm, y - 16 * mm, width=18 * mm, height=16 * mm)
                    x_offset = 26 * mm
                except Exception:
                    x_offset = 6 * mm
            else:
                x_offset = 6 * mm
            c.drawString(x_offset, y, ent_info.get('name', ''))
            y -= 6 * mm
            c.setFont('Helvetica', 9)
            c.drawString(6 * mm, y, f"{title}")
            y -= 8 * mm
            c.drawString(6 * mm, y, "-- Composants --")
            y -= 6 * mm
            for it in rule.items:
                name = it.raw_material.name if it.raw_material else str(it.raw_material_id)
                line = f"{name[:20]} { _format_amount(it.quantity_required)}"
                c.drawString(6 * mm, y, line)
                y -= 5 * mm
                if y < 20 * mm:
                    c.showPage()
                    y = height - 8 * mm
            c.save()
            return True

        left_m, right_m, top_m, bottom_m = _get_pdf_margins(ent_info)
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=right_m, leftMargin=left_m, topMargin=top_m, bottomMargin=bottom_m)
        base_styles = getSampleStyleSheet()
        base_styles.add(ParagraphStyle(name='Heading3', parent=base_styles['Heading3'], alignment=TA_LEFT))

        elems = []
        elems.extend(_build_header_flowable(ent_info, base_styles, max_logo_width=35 * mm, logo_height=20 * mm, logo_align=ent_info.get('logo_align', 'left')))
        elems.append(Paragraph(title, base_styles['Heading2']))
        elems.append(Paragraph(f"Quantité sortie: {_format_amount(rule.output_quantity)}", base_styles['Normal']))
        elems.append(Spacer(1, 6))

        data = [["Composant", "Qté requise"]]
        for it in rule.items:
            name = it.raw_material.name if it.raw_material else str(it.raw_material_id)
            data.append([name, _format_amount(it.quantity_required)])

        table = Table(data, colWidths=[130 * mm, 40 * mm])
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.black), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#eeeeee'))]))
        elems.append(table)
        if rule.notes:
            elems.append(Spacer(1, 6))
            elems.append(Paragraph("Notes:", base_styles['Normal']))
            elems.append(Paragraph(rule.notes, base_styles['Normal']))

        doc.build(elems)
        return True

    except Exception as e:
        print(f"Erreur export règle PDF: {e}")
        return False
    finally:
        try:
            session.close()
        except Exception:
            pass


def export_product_pdf(product_id: int, file_path: str, paper: str = 'A4') -> bool:
    db = DatabaseManager()
    session = db.get_session()
    ent_ctrl = EntrepriseController()
    ent_info = ent_ctrl.get_company_info_for_pdf() or {}
    try:
        prod = session.query(CoreProduct).filter_by(id=product_id).first()
        if not prod:
            raise Exception("Produit introuvable")

        title = f"Fiche produit: {prod.name or prod.id}"

        if paper == '80mm':
            width = 80 * mm
            height = 160 * mm
            c = canvas.Canvas(file_path, pagesize=(width, height))
            y = height - 8 * mm
            c.setFont('Helvetica-Bold', 10)
            if ent_info.get('logo'):
                try:
                    img = ImageReader(io.BytesIO(ent_info.get('logo')))
                    c.drawImage(img, 6 * mm, y - 16 * mm, width=18 * mm, height=16 * mm)
                    x_offset = 26 * mm
                except Exception:
                    x_offset = 6 * mm
            else:
                x_offset = 6 * mm
            c.drawString(x_offset, y, ent_info.get('name', ''))
            y -= 6 * mm
            c.setFont('Helvetica', 9)
            c.drawString(6 * mm, y, f"Réf: {prod.reference or ''}")
            y -= 6 * mm
            c.drawString(6 * mm, y, f"Prix: {prod.selling_price if hasattr(prod, 'selling_price') else ''}")
            y -= 6 * mm
            c.drawString(6 * mm, y, f"Type: {getattr(prod, 'product_type', '')}")
            y -= 6 * mm
            c.save()
            return True

        left_m, right_m, top_m, bottom_m = _get_pdf_margins(ent_info)
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=right_m, leftMargin=left_m, topMargin=top_m, bottomMargin=bottom_m)
        base_styles = getSampleStyleSheet()
        base_styles.add(ParagraphStyle(name='Heading3', parent=base_styles['Heading3'], alignment=TA_LEFT))

        elems = []
        elems.extend(_build_header_flowable(ent_info, base_styles, max_logo_width=35 * mm, logo_height=20 * mm, logo_align=ent_info.get('logo_align', 'left')))
        elems.append(Paragraph(title, base_styles['Heading2']))
        elems.append(Paragraph(f"Référence: {prod.reference or ''}", base_styles['Normal']))
        elems.append(Paragraph(f"Prix vente: {getattr(prod, 'selling_price', '')}", base_styles['Normal']))
        elems.append(Paragraph(f"Type produit: {getattr(prod, 'product_type', '')}", base_styles['Normal']))
        if getattr(prod, 'description', None):
            elems.append(Spacer(1, 6))
            elems.append(Paragraph(prod.description, base_styles['Normal']))
        doc.build(elems)
        return True

    except Exception as e:
        print(f"Erreur export produit PDF: {e}")
        return False
    finally:
        try:
            session.close()
        except Exception:
            pass
