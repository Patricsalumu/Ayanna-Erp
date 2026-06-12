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
        # Increase height to accommodate client name and footer
        page_height = max(100 * mm, (line_count * 8 * mm) + 80 * mm)

        c = canvas.Canvas(filename, pagesize=(ticket_width, page_height))
        
        # Company name
        c.setFont('Helvetica-Bold', 9)
        company_name = self._get_company_name()
        c.drawCentredString(ticket_width / 2, page_height - 10 * mm, company_name)

        # Title
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(ticket_width / 2, page_height - 15 * mm, 'BON DE COMMANDE')

        # Numero (very large and bold)
        c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(ticket_width / 2, page_height - 24 * mm, str(ticket_data.get('numero_bon', 'N/A')))

        # Separator
        y = page_height - 30 * mm
        c.setLineWidth(0.5)
        c.line(left_margin, y, ticket_width - left_margin, y)
        y -= 4 * mm

        # Server, table, panier, date - normal font (not bold)
        c.setFont('Helvetica', 8)
        c.drawString(left_margin, y, f"Servi par: {ticket_data.get('serveuse', '')}")
        y -= 4 * mm
        c.drawString(left_margin, y, f"Table: {ticket_data.get('table', '')}")
        y -= 4 * mm
        c.drawString(left_margin, y, f"Panier: {ticket_data.get('panier_id', '')}")
        y -= 4 * mm

        dt = ticket_data.get('created_at')
        if isinstance(dt, datetime):
            dt = dt.strftime('%d/%m/%Y %H:%M')
        c.drawString(left_margin, y, f"Date: {dt}")
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
        y -= 5 * mm

        # Client name - bold at bottom
        client_name = ticket_data.get('client_name', '')
        if client_name:
            c.setFont('Helvetica-Bold', 9)
            c.drawCentredString(ticket_width / 2, y, f"Client: {client_name}")
            y -= 5 * mm

        # Footer - Informatisé par Ayanna ERP
        c.setFont('Helvetica', 7)
        c.drawCentredString(ticket_width / 2, 5 * mm, 'Informatisé par Ayanna ERP')

        c.save()
        return filename
