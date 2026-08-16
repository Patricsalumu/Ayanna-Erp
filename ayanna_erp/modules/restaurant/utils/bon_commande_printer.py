import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas

# Attempt to import EntrepriseController if available
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
try:
    from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
except Exception:
    EntrepriseController = None


class BonCommandePrinter:
    def __init__(self, enterprise_id=None):
        self.enterprise_id = enterprise_id
        self.company_info = {}
        if EntrepriseController is not None:
            try:
                self.company_info = EntrepriseController().get_company_info_for_pdf(enterprise_id) or {}
            except Exception:
                self.company_info = {}

    def _get_company_name(self):
        if isinstance(self.company_info, dict):
            return str(self.company_info.get('name') or 'Ayanna ERP')
        return 'Ayanna ERP'

    def print_ticket(self, ticket_data: dict, filename: str) -> str:
        # Ticket width approximated to 58mm
        ticket_width = 58 * mm
        left_margin = 3 * mm

        items = ticket_data.get('items', [])
        line_count = max(8, 4 + len(items))
        # Hauteur réduite (compact layout)
        page_height = max(90 * mm, (line_count * 6 * mm) + 60 * mm)

        c = canvas.Canvas(filename, pagesize=(ticket_width, page_height))
        
        # Company name
        c.setFont('Helvetica-Bold', 9)
        company_name = self._get_company_name()
        c.drawCentredString(ticket_width / 2, page_height - 10 * mm, company_name)

        # Title: "BON No [numéro]" (au lieu de "BON DE COMMANDE")
        c.setFont('Helvetica-Bold', 12)
        numero_bon = ticket_data.get('numero_bon', 'N/A')
        title_text = f'BON No {numero_bon}'
        if ticket_data.get('copy'):
            title_text = f'{title_text} - COPIE'
        c.drawCentredString(ticket_width / 2, page_height - 16 * mm, title_text)

        # Separator
        y = page_height - 21 * mm
        c.setLineWidth(0.5)
        c.line(left_margin, y, ticket_width - left_margin, y)
        y -= 4 * mm

        # Servi par & Table sur la même ligne
        c.setFont('Helvetica', 8)
        serveuse = ticket_data.get('serveuse', '')[:11]  # Tronquer à 11 caractères
        table = ticket_data.get('table', '')
        c.drawString(left_margin, y, f"Par: {serveuse}")
        c.drawString(left_margin + 28 * mm, y, f"Table: {table}")
        y -= 4 * mm

        # Panier & Date sur la même ligne
        panier_id = ticket_data.get('panier_id', '')
        dt = ticket_data.get('created_at')
        if isinstance(dt, datetime):
            dt = dt.strftime('%d/%m %H:%M')  # Juste jour/mois et heure
        c.drawString(left_margin, y, f"CMD: {panier_id}")
        c.drawString(left_margin + 28 * mm, y, f"Date: {dt}")
        y -= 6 * mm

        c.line(left_margin, y, ticket_width - left_margin, y)
        y -= 5 * mm

        # Products - bold and larger font
        c.setFont('Helvetica-Bold', 10)
        for item in items:
            name = str(item.get('nom', item.get('name', '')) or '')
            quantity = int(item.get('quantite', item.get('quantity', 0)) or 0)
            line_text = f"{name} x{quantity}"
            c.drawString(left_margin, y, line_text[:28])
            y -= 5 * mm

        y -= 3 * mm
        c.line(left_margin, y, ticket_width - left_margin, y)
        y -= 3 * mm

        # Serveuse name - bold at bottom
        serveuse_name = ticket_data.get('serveuse_name') or ticket_data.get('serveuse', '')
        if serveuse_name:
            c.setFont('Helvetica-Bold', 9)
            y -= 1 * mm
            c.drawCentredString(ticket_width / 2, y, f"{serveuse_name}")


        # Footer - Informatisé par Ayanna ERP
        c.setFont('Helvetica', 7)
        y -= 3 * mm
        c.drawCentredString(ticket_width / 2, y, 'Informatisé par Ayanna ERP')

        c.save()
        return filename
