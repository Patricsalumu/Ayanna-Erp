from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController


def _build_company_header(styles, enterprise_id=None):
    enterprise_controller = EntrepriseController()
    company_info = enterprise_controller.get_company_info_for_pdf(enterprise_id)

    temp_logo = None
    logo_path = None
    header_data = []

    company_text = (
        f"<b>{company_info.get('name','AYANNA ERP')}</b><br/>{company_info.get('address','')}<br/>"
        f"{company_info.get('city','')}<br/>Tel: {company_info.get('phone','')}"
    )

    if company_info.get('logo'):
        try:
            import tempfile
            temp_logo = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp_logo.write(company_info['logo'])
            logo_path = temp_logo.name
            temp_logo.close()
            logo = Image(logo_path, width=2.3*cm, height=2.3*cm)
            header_data.append([logo, Paragraph(company_text, styles['Normal'])])
        except Exception:
            header_data.append([Paragraph(company_text, styles['Normal']), ''])
    else:
        header_data.append([Paragraph(company_text, styles['Normal']), ''])

    header_table = Table(header_data, colWidths=[3*cm, 12*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))

    return header_table, logo_path, company_info


def generate_daily_report_pdf(rows, date_debut, date_fin, currency_symbol, enterprise_id=None):
    """
    Génère un PDF A4 portrait avec : entête entreprise, période, tableau quotidien, ligne Totaux,
    et mention "Généré par ..." harmonisée avec les exports produits.
    rows: liste de dicts avec clés: label, ca, remises, creances, depenses, espece, marge
    """
    export_dir = os.path.join(os.getcwd(), "exports_commandes")
    os.makedirs(export_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(export_dir, f"rapport_quotidien_{timestamp}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=4*cm,
        rightMargin=4*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle', fontSize=15, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name='SmallInfo', fontSize=9, fontName='Helvetica', textColor="grey"))

    story = []

    # Entête entreprise (aligné export produits)
    header_table, logo_path, company_info = _build_company_header(styles, enterprise_id)
    story.append(header_table)
    story.append(Spacer(1, 0.6*cm))

    # Titre + période
    story.append(Paragraph("RAPPORT QUOTIDIEN DES VENTES", styles['ReportTitle']))
    story.append(Paragraph(f"Période : <b>{date_debut.strftime('%d/%m/%Y')}</b> - <b>{date_fin.strftime('%d/%m/%Y')}</b>", styles['Normal']))
    story.append(Spacer(1, 0.4*cm))

    # Tableau
    headers = [
        "Date", "Chiffre d'affaires", "Remises", "Créances", "Dépenses", "Espèces", "Marge"
    ]

    def fmt(amount):
        try:
            from ayanna_erp.utils.formatting import format_amount_for_pdf as _fmt_pdf
            return _fmt_pdf(amount, currency_symbol)
        except Exception:
            return f"{amount:,.0f} {currency_symbol or ''}"

    data = [headers]

    totals = {k: 0.0 for k in ['ca','remises','creances','depenses','espece','marge']}
    for r in rows:
        data.append([
            r.get('label',''), fmt(r.get('ca',0)), fmt(r.get('remises',0)), fmt(r.get('creances',0)), fmt(r.get('depenses',0)), fmt(r.get('espece',0)), fmt(r.get('marge',0))
        ])
        for k in totals:
            try:
                totals[k] += float(r.get(k, 0.0) or 0.0)
            except Exception:
                pass

    data.append([
        "Total", fmt(totals['ca']), fmt(totals['remises']), fmt(totals['creances']), fmt(totals['depenses']), fmt(totals['espece']), fmt(totals['marge'])
    ])

    table = Table(data, colWidths=[3*cm, 3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), HexColor('#eaeaea')),
        ('GRID', (0,0), (-1,-1), 0.4, black),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.6*cm))

    # Mention généré par ...
    company_name = company_info.get('name') or 'Ayanna ERP'
    story.append(Paragraph(f"Généré par {company_name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['SmallInfo']))

    doc.build(story)

    # Cleanup logo
    if logo_path and os.path.exists(logo_path):
        try:
            os.unlink(logo_path)
        except Exception:
            pass

    return filename
