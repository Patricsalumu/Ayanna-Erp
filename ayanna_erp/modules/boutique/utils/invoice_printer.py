"""
Utilitaire pour l'impression des factures de commande
Génération de PDF A4 (facture complète) et tickets 53mm (reçus)
"""

import os
import io
import sys
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas

# Import du contrôleur d'entreprise
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
try:
    from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
except ImportError:
    EntrepriseController = None


class InvoicePrintManager:
    """Gestionnaire d'impression pour les factures de commande"""

    def __init__(self, enterprise_id=None):
        # Initialiser le contrôleur d'entreprise
        self.entreprise_controller = EntrepriseController() if EntrepriseController else None
        self.enterprise_id = enterprise_id  # Stocker l'ID de l'entreprise


        try:
            self.company_info = self.entreprise_controller.get_company_info_for_pdf(enterprise_id)
        except Exception as e:
            print(f"Erreur récupération informations entreprise: {e}")



        # Styles pour les documents
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

        # Fichier temporaire pour le logo
        self._temp_logo_path = None

    def set_enterprise(self, enterprise_id):
        """
        Changer l'entreprise utilisée pour l'impression

        Args:
            enterprise_id (int): ID de l'entreprise à utiliser
        """
        self.enterprise_id = enterprise_id

        # Recharger les informations de l'entreprise
        
        try:
            self.company_info = self.entreprise_controller.get_company_info_for_pdf(enterprise_id)
        except Exception as e:
            print(f"Erreur récupération informations entreprise: {e}")


        # Nettoyer l'ancien logo temporaire
        self._cleanup_temp_logo()

    def get_current_enterprise_id(self):
        """
        Récupérer l'ID de l'entreprise actuellement utilisée

        Returns:
            int: ID de l'entreprise ou None si pas défini
        """
        return self.enterprise_id

    def _create_temp_logo_file(self):
        """Créer un fichier temporaire pour le logo BLOB"""
        if self.company_info.get('logo') and not self._temp_logo_path:
            try:
                # Créer un fichier temporaire
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    temp_file.write(self.company_info['logo'])
                    self._temp_logo_path = temp_file.name
            except Exception as e:
                print(f"Erreur création fichier temporaire logo: {e}")
                self._temp_logo_path = None

        return self._temp_logo_path

    def _cleanup_temp_logo(self):
        """Nettoyer le fichier temporaire du logo"""
        if self._temp_logo_path and os.path.exists(self._temp_logo_path):
            try:
                os.unlink(self._temp_logo_path)
                self._temp_logo_path = None
            except Exception as e:
                print(f"Erreur suppression fichier temporaire: {e}")

    def __del__(self):
        """Destructeur pour nettoyer les fichiers temporaires"""
        self._cleanup_temp_logo()

    def get_currency_symbol(self):
        """Récupérer le symbole de devise de l'entreprise"""
        if self.entreprise_controller:
            return self.entreprise_controller.get_currency_symbol(self.enterprise_id)
        else:
            return "F"  # Fallback

    def format_amount(self, amount):
        """Formater un montant avec la devise de l'entreprise"""
        if self.entreprise_controller:
            return self.entreprise_controller.format_amount(amount, self.enterprise_id)
        else:
            # Fallback: format with space as thousands separator and omit .00 when integer
            try:
                val = float(amount)
            except Exception:
                return str(amount)

            # Round to 2 decimals, but drop decimals when .00
            rounded = round(val, 2)
            if rounded.is_integer():
                s = f"{int(rounded):,}".replace(",", " ")
            else:
                s = f"{rounded:,.2f}".replace(",", " ")

            currency = self.get_currency_symbol() or "F"
            return f"{s} {currency}"

    def setup_custom_styles(self):
        """Configurer les styles personnalisés"""
        # Style pour les titres
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=20,
            textColor=HexColor('#2C3E50'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=HexColor('#34495E'),
            fontName='Helvetica-Bold'
        ))

        # Style pour le texte normal
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            fontName='Helvetica'
        ))

    def create_header_a4(self, canvas, doc):
        """Créer l'en-tête pour les documents A4"""
        canvas.saveState()

        # FILIGRANE EN BAS
        canvas.setFont('Helvetica-Bold', 11)
        canvas.setFillColor(HexColor('#555555'))
        generation_time = datetime.now().strftime('%d/%m/%Y à %H:%M')
        filigrane_text = f"Généré par Ayanna Erp App © - {generation_time}"
        text_width = canvas.stringWidth(filigrane_text, 'Helvetica-Bold', 11)
        x_center = (A4[0] - text_width) / 2
        canvas.drawString(x_center, 15, filigrane_text)

        # Rectangle de fond pour l'en-tête
        canvas.setFillColor(HexColor('#F8F9FA'))
        canvas.rect(0, A4[1] - 120, A4[0], 120, fill=1, stroke=0)

        # Ligne de séparation
        canvas.setStrokeColor(HexColor('#3498DB'))
        canvas.setLineWidth(2)
        canvas.line(50, A4[1] - 120, A4[0] - 50, A4[1] - 120)

        # Logo (si disponible)
        logo_path = self._create_temp_logo_file()
        if logo_path and os.path.exists(logo_path):
            try:
                canvas.drawImage(logo_path, 50, A4[1] - 110,
                               width=60, height=60, preserveAspectRatio=True)
            except Exception as e:
                print(f"Erreur affichage logo: {e}")
                pass

        # Informations entreprise
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(HexColor('#2C3E50'))
        canvas.drawString(130, A4[1] - 60, self.company_info['name'])

        canvas.setFont('Helvetica', 10)
        canvas.setFillColor(black)
        canvas.drawString(130, A4[1] - 75, self.company_info['address'])
        canvas.drawString(130, A4[1] - 88, self.company_info['city'])
        canvas.drawString(130, A4[1] - 101, f"Tél: {self.company_info['phone']}")

        # Informations à droite
        canvas.drawRightString(A4[0] - 50, A4[1] - 75, f"Email: {self.company_info['email']}")
        canvas.drawRightString(A4[0] - 50, A4[1] - 88, f"RCCM: {self.company_info['rccm']}")
        canvas.drawRightString(A4[0] - 50, A4[1] - 101, f"Date: {datetime.now().strftime('%d/%m/%Y')}")

        canvas.restoreState()

    def create_footer_a4(self, canvas, doc):
        """Créer le pied de page pour les documents A4"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#7F8C8D'))

        # Numéro de page
        page_num = canvas.getPageNumber()
        page_text = f"Page {page_num}"
        text_width = canvas.stringWidth(page_text, 'Helvetica', 8)
        x_center = (A4[0] - text_width) / 2
        canvas.drawString(x_center, 40, page_text)

        # Ligne de séparation
        canvas.setStrokeColor(HexColor('#BDC3C7'))
        canvas.setLineWidth(1)
        canvas.line(50, 50, A4[0] - 50, 50)

        canvas.restoreState()

    def print_invoice_a4(self, invoice_data, filename):
        """Imprimer une facture complète sur A4"""
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=150, bottomMargin=60)
        story = []

        # Titre du document
        title = f"FACTURE N° {invoice_data.get('reference', 'N/A')}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))

        # Informations client
        story.append(Paragraph("INFORMATIONS CLIENT", self.styles['CustomHeading']))

        client_data = [
            ['Nom du client:', invoice_data.get('client_nom', 'N/A')],
            ['Téléphone:', invoice_data.get('client_telephone', 'N/A')],
            ['Email:', invoice_data.get('client_email', 'N/A')],
            ['Adresse:', invoice_data.get('client_adresse', 'N/A')]
        ]

        # Ajouter la ligne "Servi par" si une serveuse/comptoiriste est fournie
        served_by = invoice_data.get('serveuse') or invoice_data.get('comptoiriste') or invoice_data.get('serveuse_name')
        if served_by:
            client_data.append(['Servi par:', served_by])

        client_table = Table(client_data, colWidths=[4*cm, 12*cm])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#ECF0F1')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
        ]))
        story.append(client_table)
        story.append(Spacer(1, 15))

        # Informations commande
        story.append(Paragraph("DÉTAILS DE LA COMMANDE", self.styles['CustomHeading']))

        order_data = [
            ['Référence commande:', invoice_data.get('reference', 'N/A')],
            ['Date de commande:', invoice_data.get('order_date', 'N/A')],
            ['Date de création:', invoice_data.get('created_at', 'N/A')],
            ['Statut:', invoice_data.get('status', 'N/A')]
        ]

        # Ajouter informations restaurant (table / salle / serveuse / comptoiriste) si présentes
        # Supporter plusieurs clés possibles pour compatibilité
        def _pick(*keys):
            for k in keys:
                v = invoice_data.get(k)
                if v:
                    return v
            return None

        table_val = _pick('table', 'table_number', 'table_no')
        salle_val = _pick('salle', 'salle_name', 'room')
        serveuse_val = _pick('serveuse', 'serveur', 'waiter', 'serveur_name')
        comptoiriste_val = _pick('comptoiriste', 'comptoir', 'clerk', 'cashier')

        if table_val:
            order_data.append(['Table:', str(table_val)])
        if salle_val:
            order_data.append(['Salle:', str(salle_val)])
        if serveuse_val:
            order_data.append(['Serveuse:', str(serveuse_val)])
        if comptoiriste_val:
            order_data.append(['Comptoiriste:', str(comptoiriste_val)])

        order_table = Table(order_data, colWidths=[4*cm, 12*cm])
        order_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#E8F6F3')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
        ]))
        story.append(order_table)
        story.append(Spacer(1, 15))

        # Produits commandés
        if invoice_data.get('items'):
            story.append(Paragraph("PRODUITS COMMANDÉS", self.styles['CustomHeading']))

            products_data = [['Produit', 'Quantité', 'Prix unitaire', 'Total']]
            total_products = 0

            for item in invoice_data['items']:
                total_line = item['quantity'] * item['unit_price']
                total_products += total_line
                products_data.append([
                    item['name'],
                    str(item['quantity']),
                    self.format_amount(item['unit_price']),
                    self.format_amount(total_line)
                ])

            products_data.append(['', '', 'TOTAL PRODUITS:', self.format_amount(total_products)])

            products_table = Table(products_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
            products_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, -1), (-1, -1), HexColor('#D5DBDB')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            story.append(products_table)
            story.append(Spacer(1, 15))

        # Récapitulatif financier
        story.append(Paragraph("RÉCAPITULATIF FINANCIER", self.styles['CustomHeading']))

        currency_symbol = self.get_currency_symbol()
        financial_data = [
            ['Sous-total HT:', self.format_amount(invoice_data.get('subtotal_ht', 0))],
            ['TVA:', self.format_amount(invoice_data.get('tax_amount', 0))],
            ['Total TTC:', self.format_amount(invoice_data.get('total_ttc', 0))],
            ['Remise:', f"-{self.format_amount(invoice_data.get('discount_amount', 0))}"],
            ['NET À PAYER:', self.format_amount(invoice_data.get('total_net', 0))]
        ]

        financial_table = Table(financial_data, colWidths=[12*cm, 4*cm])
        financial_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), HexColor('#2ECC71')),
            ('TEXTCOLOR', (0, -1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
        ]))
        story.append(financial_table)
        story.append(Spacer(1, 20))

        # Historique des paiements
        story.append(Paragraph("HISTORIQUE DES PAIEMENTS", self.styles['CustomHeading']))

        if invoice_data.get('payments'):
            payment_data = [['Date', 'Montant', 'Méthode', 'Utilisateur']]
            total_paid = 0

            for payment in invoice_data['payments']:
                total_paid += payment['amount']
                payment_data.append([
                    payment['payment_date'].strftime('%d/%m/%Y %H:%M') if hasattr(payment['payment_date'], 'strftime') else str(payment['payment_date']),
                    self.format_amount(payment['amount']),
                    payment.get('payment_method', 'N/A'),
                    payment.get('user_name', 'N/A')
                ])

            # Calculer le solde
            net_a_payer = invoice_data.get('total_net', 0)
            balance = net_a_payer - total_paid
            payment_data.append(['', '', 'TOTAL PAYÉ:', self.format_amount(total_paid)])
            payment_data.append(['', '', 'RESTE À PAYER:', self.format_amount(balance)])

            payment_table = Table(payment_data, colWidths=[4*cm, 3*cm, 4*cm, 5*cm])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#9B59B6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, -2), (-1, -1), HexColor('#D5DBDB')),
                ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            story.append(payment_table)
        else:
            story.append(Paragraph("Aucun paiement effectué", self.styles['CustomNormal']))

        story.append(Spacer(1, 20))

        # Section Notes/Commentaires
        story.append(Paragraph("NOTES ET COMMENTAIRES", self.styles['CustomHeading']))

        notes = invoice_data.get('notes', '')
        if not notes or notes.strip() == '':
            notes = "Aucune note particulière pour cette commande."

        notes_style = ParagraphStyle(
            'NotesStyle',
            parent=self.styles['CustomNormal'],
            fontSize=10,
            leading=12,
            alignment=0,
            spaceAfter=6,
            leftIndent=10,
            rightIndent=10
        )

        notes_paragraph = Paragraph(notes, notes_style)
        notes_data = [[notes_paragraph]]
        notes_table = Table(notes_data, colWidths=[16*cm])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#FAFBFC')),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12)
        ]))
        story.append(notes_table)

        # Construire le PDF
        doc.build(story, onFirstPage=self.create_header_a4, onLaterPages=self.create_header_a4)

        return filename

    def print_receipt_53mm(self, invoice_data, payments_list, user_name, filename):
        # Debug prints removed in production
        """Imprimer un reçu de paiement sur format 53mm avec détail de tous les paiements"""
        # Taille du ticket 53mm de large (format imprimante thermique)
        TICKET_WIDTH = 53 * mm

        # --- Pré-passage (simulation) pour calculer la hauteur exacte nécessaire ---
        from reportlab.pdfbase import pdfmetrics

        # utiliser une hauteur de départ suffisante pour la simulation
        simulate_start_height = 300 * mm
        y_sim = simulate_start_height - 5 * mm

        # Estimer logo
        logo_path = self._create_temp_logo_file()
        if logo_path and os.path.exists(logo_path):
            y_sim -= 18 * mm

        # Coordonnées entreprise (approx. 2.5mm par ligne)
        for info in [self.company_info.get('phone'), self.company_info.get('email')]:
            if info:
                y_sim -= 2.5 * mm

        if self.company_info.get('rccm'):
            y_sim -= 2.5 * mm

        # séparation
        y_sim -= 2 * mm
        y_sim -= 3 * mm

        # titre
        line_height = 3.5 * mm
        y_sim -= (line_height + 2 * mm)

        # info commande (ref, client, date)
        y_sim -= 2.5 * mm  # ref
        y_sim -= 2.5 * mm  # client
        y_sim -= 2.5 * mm  # date

        # séparation
        y_sim -= 2 * mm
        y_sim -= 3 * mm

        # articles title
        y_sim -= 3 * mm

        # articles (nom + detail)
        if invoice_data.get('items'):
            for item in invoice_data['items']:
                # nom (dans le rendu actuel on tronque à 30 chars)
                y_sim -= 2 * mm
                # détail quantité x prix
                y_sim -= 2.5 * mm

        # séparation avant paiements
        y_sim -= 2 * mm
        y_sim -= 3 * mm

        # paiements
        if payments_list:
            for i, payment in enumerate(payments_list, 1):
                # #, montant, méthode, date, caissier
                y_sim -= 2 * mm  # numéro
                y_sim -= 2 * mm  # montant
                y_sim -= 2 * mm  # méthode
                y_sim -= 2 * mm  # date
                y_sim -= 2 * mm  # caissier
                if i < len(payments_list):
                    y_sim -= 3 * mm  # séparation
        else:
            y_sim -= 3 * mm

        # récapitulatif
        y_sim -= 2 * mm
        y_sim -= 3 * mm
        y_sim -= 3.5 * mm  # sous total
        y_sim -= 3.5 * mm  # remise
        y_sim -= 3.5 * mm  # net a payer
        y_sim -= 3.5 * mm  # total payé
        y_sim -= 3 * mm    # reste

        # séparation finale
        y_sim -= 3 * mm

        # notes (simuler wrapping en fonction de la largeur utile)
        usable_width = TICKET_WIDTH - (6 * mm)
        notes = (invoice_data.get('notes') or '').strip()
        if notes:
            y_sim -= 3 * mm  # titre NOTES
            words = notes.split()
            cur_line = ''
            lines = 0
            for word in words:
                test = (cur_line + ' ' + word).strip() if cur_line else word
                if pdfmetrics.stringWidth(test, 'Helvetica', 5) < usable_width:
                    cur_line = test
                else:
                    lines += 1
                    cur_line = word
            if cur_line:
                lines += 1
            y_sim -= max(6 * mm, lines * 2.5 * mm)
            y_sim -= 3 * mm  # séparation après notes

        # filigrane
        y_sim -= 10 * mm

        used_height = simulate_start_height - y_sim
        # ajouter petite marge
        TICKET_HEIGHT = used_height + 12 * mm
        # garantir une hauteur minimale
        min_height = 85 * mm
        if TICKET_HEIGHT < min_height:
            TICKET_HEIGHT = min_height

        # Créer le document PDF avec la hauteur calculée
        c = canvas.Canvas(filename, pagesize=(TICKET_WIDTH, TICKET_HEIGHT))

        y_position = TICKET_HEIGHT - 5 * mm  # point de départ en haut

        # Logo et en-tête entreprise (taille réduite pour 53mm)
        logo_path = self._create_temp_logo_file()
        if logo_path and os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, (TICKET_WIDTH - 20*mm) / 2, y_position - 15*mm,
                           width=15*mm, height=15*mm, preserveAspectRatio=True)
                y_position -= 18*mm
            except Exception as e:
                print(f"Erreur affichage logo: {e}")

        # Nom de l'entreprise
        c.setFont('Helvetica-Bold', 8)
        text = self.company_info['name'][:25]  # Limiter la longueur
        text_width = c.stringWidth(text, 'Helvetica-Bold', 8)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, text)
        y_position -= line_height

        # Coordonnées entreprise (police très petite)
        c.setFont('Helvetica', 6)
        for info in [self.company_info['phone'], self.company_info['email']]:
            if info:
                info_text = info[:25]
                text_width = c.stringWidth(info_text, 'Helvetica', 6)
                c.drawString((TICKET_WIDTH - text_width) / 2, y_position, info_text)
                y_position -= 2.5*mm

        # RCCM
        if self.company_info['rccm']:
            rccm_text = self.company_info['rccm'][:25]
            text_width = c.stringWidth(rccm_text, 'Helvetica', 6)
            c.drawString((TICKET_WIDTH - text_width) / 2, y_position, rccm_text)
            y_position -= 2.5*mm

        # Ligne de séparation
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm

        # Titre du reçu
        c.setFont('Helvetica-Bold', 7)
        title = "RECU DE PAIEMENT"
        text_width = c.stringWidth(title, 'Helvetica-Bold', 7)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, title)
        y_position -= line_height + 2*mm

        # Informations de base de la commande (format compact)
        c.setFont('Helvetica', 6)

        # Référence
        ref_text = f"Ref: {invoice_data.get('reference', 'N/A')[:15]}"
        c.drawString(2*mm, y_position, ref_text)
        y_position -= 2.5*mm

        # Client (limiter la longueur)
        client_name = invoice_data.get('client_nom', 'N/A')[:25]
        client_text = f"Client: {client_name}"
        c.drawString(2*mm, y_position, client_text)
        y_position -= 2.5*mm

        # Date commande
        order_date_obj = invoice_data.get('order_date', 'N/A')
        if isinstance(order_date_obj, datetime):
            order_date = order_date_obj.strftime('%d/%m/%Y %H:%M')[:20]
        else:
            order_date = str(order_date_obj)[:20]
        date_text = f"Date: {order_date}"
        c.drawString(2*mm, y_position, date_text)
        y_position -= 2.5*mm

        # Afficher table / salle / serveuse / comptoiriste exceptionnellement pour le module restaurant
        def _pick_local(inv, *keys):
            for k in keys:
                v = inv.get(k)
                if v:
                    return v
            return None

        # Détection explicite du module restaurant : invoice_data peut contenir 'module' ou 'is_restaurant'
        is_restaurant = False
        try:
            if str(invoice_data.get('module', '')).lower() == 'restaurant' or invoice_data.get('is_restaurant'):
                is_restaurant = True
        except Exception:
            is_restaurant = False
        serveuse_val = _pick_local(invoice_data, 'serveuse', 'serveur', 'waiter', 'serveur_name')
        table_val = _pick_local(invoice_data, 'table', 'table_number', 'table_no')
        salle_val = _pick_local(invoice_data, 'salle', 'salle_name', 'room')
        comptoiriste_val = _pick_local(invoice_data, 'comptoiriste', 'comptoir', 'clerk', 'cashier')

        # Afficher uniquement si c'est bien un ticket du module restaurant ou si la table est explicitement fournie
        if is_restaurant or table_val:
            if table_val:
                c.drawString(2*mm, y_position, f"Table: {str(table_val)[:20]}")
                y_position -= 2.5*mm
            if salle_val:
                c.drawString(2*mm, y_position, f"Salle: {str(salle_val)[:20]}")
                y_position -= 2.5*mm
            if serveuse_val:
                c.drawString(2*mm, y_position, f"Serveuse: {str(serveuse_val)[:25]}")
                y_position -= 2.5*mm
            if comptoiriste_val:
                c.drawString(2*mm, y_position, f"Comptoir: {str(comptoiriste_val)[:25]}")
                y_position -= 2.5*mm

        # Ligne de séparation
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm

        # Détail des articles
        c.setFont('Helvetica-Bold', 6)
        c.drawString(2*mm, y_position, "ARTICLES:")
        y_position -= 3*mm

        # Lister chaque article
        if invoice_data.get('items'):
            # helper to format amounts for 53mm (lowercase currency suffix)
            def _fmt_ticket_amount(val):
                try:
                    s = self.format_amount(val)
                    if isinstance(s, str) and ' ' in s:
                        head, tail = s.rsplit(' ', 1)
                        return f"{head} {tail.lower()}"
                    return s
                except Exception:
                    try:
                        return str(val)
                    except Exception:
                        return ''

            subtotal_articles = 0
            for item in invoice_data['items']:
                # Nom de l'article (tronqué si nécessaire)
                item_name = item.get('name', 'N/A')[:30]
                c.setFont('Helvetica', 6)
                c.drawString(3*mm, y_position, item_name)
                y_position -= 2*mm

                # Quantité x Prix = Total
                quantity = item.get('quantity', 0)
                unit_price = item.get('unit_price', 0)
                try:
                    total_line = quantity * unit_price
                except Exception:
                    total_line = 0
                subtotal_articles += total_line
                # Utiliser format_amount pour un affichage uniforme
                item_detail = f"{int(quantity)} x {_fmt_ticket_amount(unit_price)} = {_fmt_ticket_amount(total_line)}"
                c.drawString(5*mm, y_position, item_detail)
                y_position -= 2.5*mm

            # Afficher le sous-total des articles juste après la liste
            try:
                c.setFont('Helvetica-Bold', 6)
                c.drawString(3*mm, y_position, f"Sous-total articles: {_fmt_ticket_amount(subtotal_articles)}")
                y_position -= 3.5*mm
            except Exception:
                pass

        # Ligne de séparation avant les paiements
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm

        # Détail de chaque paiement
        c.setFont('Helvetica-Bold', 6)
        c.drawString(2*mm, y_position, "DETAIL PAIEMENTS:")
        y_position -= 3*mm

        total_paid = 0

        if payments_list:
            for i, payment in enumerate(payments_list, 1):
                # Numéro du paiement
                c.setFont('Helvetica-Bold', 6)
                payment_num_text = f"#{i}"
                c.drawString(2*mm, y_position, payment_num_text)
                y_position -= 2*mm

                # Montant (formaté)
                c.setFont('Helvetica', 6)
                amount = payment.get('amount', 0)
                try:
                    total_paid += amount
                except Exception:
                    pass
                amount_text = _fmt_ticket_amount(amount)
                c.drawString(3*mm, y_position, amount_text)
                y_position -= 2*mm

                # Méthode
                method_text = payment.get('payment_method', 'N/A')[:20]
                c.drawString(3*mm, y_position, method_text)
                y_position -= 2*mm

                # Date
                payment_date = payment.get('payment_date', 'N/A')
                if isinstance(payment_date, datetime):
                    date_text = payment_date.strftime('%d/%m/%Y %H:%M')[:20]
                else:
                    date_text = str(payment_date)[:20]
                c.drawString(3*mm, y_position, date_text)
                y_position -= 2*mm

                # Caissier
                cashier_name = payment.get('user_name', 'N/A')[:25]
                cashier_text = f"Par: {cashier_name}"
                c.drawString(3*mm, y_position, cashier_text)
                y_position -= 2*mm

                # Petite ligne de séparation entre paiements
                if i < len(payments_list):
                    c.line(3*mm, y_position, TICKET_WIDTH - 3*mm, y_position)
                    y_position -= 3*mm
        else:
            c.setFont('Helvetica', 6)
            c.drawString(2*mm, y_position, "Aucun paiement")
            y_position -= 3*mm

        # Récapitulatif final
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm

        c.setFont('Helvetica-Bold', 6)
        c.drawString(2*mm, y_position, "RECAPITULATIF:")
        y_position -= 3*mm

        c.setFont('Helvetica', 6)
        # Utiliser le net à payer (après remise)
        net_a_payer = invoice_data.get('total_net', invoice_data.get('net_a_payer', 0))
        sous_total_val = invoice_data.get('subtotal_ht', 0)
        remise_val = invoice_data.get('discount_amount', 0)
        balance = net_a_payer - total_paid

        # Sous total (avant remise)
        sous_total_text = f"Sous total: {_fmt_ticket_amount(sous_total_val)}"
        c.drawString(2*mm, y_position, sous_total_text)
        y_position -= 3.5*mm

        # Remise
        remise_text = f"Remise: {_fmt_ticket_amount(remise_val)}"
        c.drawString(2*mm, y_position, remise_text)
        y_position -= 3.5*mm

        # Net à payer (après remise)
        total_text = f"Net à payer: {_fmt_ticket_amount(net_a_payer)}"
        c.drawString(2*mm, y_position, total_text)
        y_position -= 3.5*mm

        # Total payé
        paid_text = f"Paye: {_fmt_ticket_amount(total_paid)}"
        c.drawString(2*mm, y_position, paid_text)
        y_position -= 3.5*mm

        # Reste à payer
        c.setFont('Helvetica-Bold', 7)
        balance_text = f"Reste: {_fmt_ticket_amount(balance)}"
        c.drawString(2*mm, y_position, balance_text)
        y_position -= 3*mm

        # Ligne de séparation finale
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        # Section Notes (si présentes)
        # Afficher les notes si présentes (toujours après le récapitulatif)
        notes = (invoice_data.get('notes') or '').strip()
        if notes:
            c.setFont('Helvetica-Bold', 6)
            c.drawString(2*mm, y_position, "NOTES:")
            y_position -= 3*mm

            c.setFont('Helvetica', 5)
            # Diviser les notes en lignes si nécessaire (limiter la longueur)
            words = notes.split()
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if c.stringWidth(test_line, 'Helvetica', 5) < TICKET_WIDTH - 4*mm:
                    current_line = test_line
                else:
                    if current_line:
                        c.drawString(3*mm, y_position, current_line.strip())
                        y_position -= 2.5*mm
                    current_line = word

            # Dernière ligne
            if current_line:
                c.drawString(3*mm, y_position, current_line.strip())
                y_position -= 3*mm

            # Ligne de séparation après les notes
            c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
            y_position -= 3*mm


        # Filigrane avec nom d'entreprise dynamique
        c.setFont('Helvetica', 6)
        generation_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        filigrane_text = f"Ayanna Erp App (c) {generation_time}"
        text_width = c.stringWidth(filigrane_text, 'Helvetica', 6)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, filigrane_text)

        # Sauvegarder le PDF
        c.save()

        return filename