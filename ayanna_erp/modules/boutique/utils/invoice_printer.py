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

        # Définir des polices de secours utilisées pour les tickets
        # Ces attributs peuvent être écrasés si des TTF spécifiques sont enregistrés
        self._font_regular = 'Helvetica'
        self._font_bold = 'Helvetica-Bold'

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
        """Formater un montant avec la devise de l'enreprise"""
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
        filigrane_text = f"Informatisé par Ayanna (0997554905) - {generation_time}"
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

        # Footer text: Informatisé par Ayanna ERP — website + print datetime
        try:
            footer_text = "Informatisé par Ayanna ERP — www.ayanna.top"
            canvas.setFont('Helvetica', 8)
            text_width = canvas.stringWidth(footer_text, 'Helvetica', 8)
            x_center = (A4[0] - text_width) / 2
            canvas.drawString(x_center, 34, footer_text)

            # Impression datetime
            printed_ts = datetime.now().strftime('%d/%m/%Y %H:%M')
            printed_text = f"Imprimé le {printed_ts}"
            canvas.setFont('Helvetica', 7)
            text_width2 = canvas.stringWidth(printed_text, 'Helvetica', 7)
            x_center2 = (A4[0] - text_width2) / 2
            canvas.drawString(x_center2, 20, printed_text)
        except Exception:
            pass

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
            ['État:', invoice_data.get('etat', invoice_data.get('status', 'N/A'))],
            ['Paiement:', invoice_data.get('status', 'N/A')]
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
        
        # Ajouter l'utilisateur qui a créé la commande
        user_name_val = invoice_data.get('user_name')
        if user_name_val and user_name_val != comptoiriste_val:
            order_data.append(['Créé par:', str(user_name_val)])

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
            story.append(Spacer(1, 15))
            
            # Afficher le statut de paiement avec change/reste à payer
            payment_status = invoice_data.get('payment_status', 'NON PAYÉE')
            change = invoice_data.get('change', 0.0)
            reste = invoice_data.get('reste_a_payer', 0.0)
            
            status_color = HexColor('#E74C3C')  # Rouge (NON PAYÉE)
            if payment_status == 'PAYÉE':
                status_color = HexColor('#27AE60')  # Vert
            elif payment_status == 'PARTIELLEMENT PAYÉE':
                status_color = HexColor('#F39C12')  # Orange
            
            status_data = []
            if change > 0:
                status_data.append(['MONNAIE:', self.format_amount(change)])
            if reste > 0:
                status_data.append(['RESTE À VERSER:', self.format_amount(reste)])
            
            status_data.append(['STATUT PAIEMENT:', payment_status])
            
            status_table = Table(status_data, colWidths=[6*cm, 10*cm])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, -1), (-1, -1), status_color),
                ('TEXTCOLOR', (0, -1), (-1, -1), white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold')
            ]))
            story.append(status_table)
        else:
            story.append(Paragraph("Aucun paiement effectué", self.styles['CustomNormal']))

        story.append(Spacer(1, 20))

        # Section Notes/Commentaires - afficher SEULEMENT si présentes
        notes = invoice_data.get('notes', '')
        if notes and notes.strip() != '':
            # Barres horizontales
            story.append(Paragraph("―" * 70, self.styles['CustomNormal']))
            story.append(Spacer(1, 6))
            
            # Titre NOTES
            story.append(Paragraph("<b>NOTES</b>", self.styles['CustomHeading']))
            story.append(Spacer(1, 6))
            
            # Contenu de la note
            notes_style = ParagraphStyle(
                'NotesStyle',
                parent=self.styles['CustomNormal'],
                fontSize=10,
                leading=14,
                alignment=0,
                spaceAfter=6,
                leftIndent=10,
                rightIndent=10
            )
            notes_paragraph = Paragraph(notes, notes_style)
            story.append(notes_paragraph)
            
            story.append(Spacer(1, 6))
            # Barres horizontales
            story.append(Paragraph("―" * 70, self.styles['CustomNormal']))

        # Construire le PDF
        doc.build(story, onFirstPage=self.create_header_a4, onLaterPages=self.create_header_a4)

        return filename

    def print_receipt_53mm(self, invoice_data, payments_list, user_name, filename):
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from datetime import datetime
        import os

        def _get_company_slogan():
            return (self.company_info.get('slogan') or '').strip()

        def _to_float(v, default=0.0):
            try:
                if v is None:
                    return default
                if isinstance(v, (int, float)):
                    return float(v)
                s = str(v).lower().strip()
                if s.endswith('%'):
                    s = s[:-1]
                for bad in ['fc', 'f', 'fcfa', 'cdf', 'xof', '€', '$']:
                    if s.endswith(bad):
                        s = s[:-len(bad)]
                s = s.replace('\u00A0', '').replace(' ', '').replace(',', '.')
                return float(s)
            except Exception:
                return default

        # =========================
        # PARAMÈTRES TICKET 80mm
        # =========================
        TICKET_WIDTH = 58 * mm
        LEFT_MARGIN = 2 * mm
        ITEM_NAME_X = LEFT_MARGIN
        ITEM_DETAIL_X = LEFT_MARGIN + 2 * mm

        # =========================
        # SIMULATION HAUTEUR
        # =========================
        y_sim = 160 * mm

        if self._create_temp_logo_file():
            y_sim -= 18 * mm

        for k in ['phone',  'adress','id_nat', 'rccm']:
            if self.company_info.get(k):
                y_sim -= 2.5 * mm

        y_sim -= 10 * mm  # titre + ref + client + date
        y_sim -= len(invoice_data.get('items', [])) * 8 * mm

        if payments_list:
            y_sim -= len(payments_list) * 16 * mm
        else:
            y_sim -= 4 * mm

        y_sim -= 25 * mm  # récap + reste
        # Correspondance devise (ligne optionnelle)
        _taux_sim = self.company_info.get('taux_de_change') if hasattr(self, 'company_info') and self.company_info else None
        if _taux_sim:
            y_sim -= 8 * mm

        # NB estimation
        nb_text = _get_company_slogan()
        if nb_text:
            words = nb_text.split()
            cur = ''
            lines = 0
            for w in words:
                test = f"{cur} {w}".strip()
                if pdfmetrics.stringWidth(test, 'Helvetica', 8) <= (TICKET_WIDTH - 2 * LEFT_MARGIN):
                    cur = test
                else:
                    lines += 1
                    cur = w
            if cur:
                lines += 1
            y_sim -= max(6 * mm, lines * 3.5 * mm)

        # NOTES estimation
        notes_text = invoice_data.get('notes', '')
        if notes_text and notes_text.strip() != '':
            y_sim -= 10 * mm  # titre + barres + espaces
            words = notes_text.split()
            cur = ''
            lines = 0
            for w in words:
                test = f"{cur} {w}".strip()
                if pdfmetrics.stringWidth(test, 'Helvetica', 8) <= (TICKET_WIDTH - 2 * LEFT_MARGIN):
                    cur = test
                else:
                    lines += 1
                    cur = w
            if cur:
                lines += 1
            y_sim -= max(8 * mm, lines * 3 * mm)

        used_height = (260 * mm) - y_sim
        TICKET_HEIGHT = max(used_height + 6 * mm, 70 * mm)

        # =========================
        # CRÉATION PDF
        # =========================
        c = canvas.Canvas(filename, pagesize=(TICKET_WIDTH, TICKET_HEIGHT))

        def _draw_wrapped(text, font, size, max_width, y, center=False, leading=3.5 * mm):
            words = (text or '').split()
            cur = ''
            lines = []
            for w in words:
                test = f"{cur} {w}".strip()
                if c.stringWidth(test, font, size) <= max_width:
                    cur = test
                else:
                    lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)

            for line in lines:
                if center:
                    w = c.stringWidth(line, font, size)
                    c.drawString((TICKET_WIDTH - w) / 2, y, line)
                else:
                    c.drawString(LEFT_MARGIN, y, line)
                y -= leading
            return y

        y = TICKET_HEIGHT - 5 * mm

        # =========================
        # LOGO
        # =========================
        logo = self._create_temp_logo_file()
        if logo and os.path.exists(logo):
            c.drawImage(logo, (TICKET_WIDTH - 15 * mm) / 2, y - 15 * mm,
                        width=15 * mm, height=15 * mm, preserveAspectRatio=True)
            y -= 18 * mm
        # =========================
        # ENTREPRISE
        # =========================
        c.setFont(self._font_bold, 9)
        name = str(self.company_info.get('name', ''))[:30]
        c.drawCentredString(TICKET_WIDTH / 2, y, name)
        y -= 4 * mm

        c.setFont(self._font_regular, 8)
        for k in ['address','phone', 'id_nat', 'rccm']:
            v = self.company_info.get(k)
            if v:
                c.drawCentredString(TICKET_WIDTH / 2, y, str(v)[:35])
                y -= 4 * mm

        # =========================
        # STATUT FACTURE
        # =========================
        total_paid = sum(_to_float(p.get('amount')) for p in payments_list or [])
        net = _to_float(invoice_data.get('total_net', invoice_data.get('net_a_payer', 0)))

        # État du panier (en_cours, validée, annulée)
        etat_panier = invoice_data.get('etat', '')
        if etat_panier and isinstance(etat_panier, str) and len(etat_panier) > 0:
            etat_clean = etat_panier.replace("✅ ", "").replace("❌ ", "").replace("⏳ ", "").upper()
        else:
            etat_clean = ''

        # Statut de paiement
        if total_paid <= 0:
            status = "NON PAYEE"
        elif total_paid >= net:
            status = "PAYEE"
        else:
            status = "PAYEE PARTIELLE"

        y -= 3 * mm
        c.setFont(self._font_bold, 10)
        c.drawCentredString(TICKET_WIDTH / 2, y, f"FACTURE {status}")
        y -= 6 * mm

        # =========================
        # RÉFÉRENCE
        # =========================
        c.setFont(self._font_bold, 12)
        ref = str(invoice_data.get('reference', 'N/A'))
        c.drawCentredString(TICKET_WIDTH / 2, y, ref)
        y -= 6 * mm

        c.setFont(self._font_regular, 8)
        c.drawString(LEFT_MARGIN, y, f"Client: {invoice_data.get('client_nom', '')[:25]}")
        y -= 3 * mm

        date_val = invoice_data.get('order_date')
        if isinstance(date_val, datetime):
            date_val = date_val.strftime('%d/%m/%Y %H:%M')
        c.drawString(LEFT_MARGIN, y, f"Date: {date_val}")
        y -= 3 * mm
        
        # Afficher l'utilisateur qui a passé la commande
        user_display = invoice_data.get('user_name') or user_name or 'Utilisateur'
        c.drawString(LEFT_MARGIN, y, f"Par: {str(user_display)[:25]}")
        y -= 2 * mm
        
        # =========================
        # INFOS RESTAURANT (OPTIONNEL)
        # =========================
        def _pick(inv, *keys):
            for k in keys:
                v = inv.get(k)
                if v not in (None, ''):
                    return v
            return None

        is_restaurant = False
        try:
            if str(invoice_data.get('module', '')).lower() == 'restaurant' or invoice_data.get('is_restaurant'):
                is_restaurant = True
        except Exception:
            is_restaurant = False

        if is_restaurant:
            table_val = _pick(invoice_data, 'table', 'table_number', 'table_no')
            salle_val = _pick(invoice_data, 'salle', 'salle_name', 'room')
            serveuse_val = _pick(invoice_data, 'serveuse', 'serveur', 'waiter', 'serveur_name')

            c.setFont(self._font_regular, 8)

            if table_val:
                c.drawString(LEFT_MARGIN, y, f"Table: {str(table_val)[:20]}")
                y -= 2.5 * mm

            if salle_val:
                c.drawString(LEFT_MARGIN, y, f"Salle: {str(salle_val)[:20]}")
                y -= 2.5 * mm

            if serveuse_val:
                c.drawString(LEFT_MARGIN, y, f"Serveuse: {str(serveuse_val)[:25]}")
                y -= 3 * mm


        c.line(LEFT_MARGIN, y, TICKET_WIDTH - LEFT_MARGIN, y)
        y -= 4 * mm

        # =========================
        # ARTICLES
        # =========================
        c.setFont('Helvetica-Bold', 10)
        c.drawString(LEFT_MARGIN, y, "ARTICLES")
        y -= 6 * mm

        subtotal = 0
        c.setFont('Helvetica', 10)
        for item in invoice_data.get('items', []):
            name = item.get('name', '')[:18]
            qty = _to_float(item.get('quantity'), 1)
            price = _to_float(item.get('unit_price'))
            subtotal += qty * price

            c.drawString(ITEM_NAME_X, y, name)
            c.drawRightString(TICKET_WIDTH - LEFT_MARGIN, y, f"{int(qty)} x {self.format_amount(price)}")
            y -= 4 * mm

        y -= 2 * mm
        c.setFont('Helvetica-Bold', 10)
        c.drawString(LEFT_MARGIN, y, f"Sous-total: {self.format_amount(subtotal)}")
        y -= 5 * mm

        # =========================
        # RÉCAP
        # =========================
        remise = _to_float(invoice_data.get('discount_amount'))
        reste = net - total_paid

        c.setFont('Helvetica', 10)
        c.drawString(LEFT_MARGIN, y, f"Remise: {self.format_amount(remise)}")
        y -= 4 * mm
        c.drawString(LEFT_MARGIN, y, f"Net à payer: {self.format_amount(net)}")
        y -= 4 * mm

        # ------ Correspondance devise ------
        _currency = (self.company_info.get('currency') or 'USD') if hasattr(self, 'company_info') and self.company_info else 'USD'
        _taux = self.company_info.get('taux_de_change') if hasattr(self, 'company_info') and self.company_info else None
        if _taux and _taux > 0 and net > 0:
            _currency_norm = _currency.upper().strip()
            _is_franc = _currency_norm in ('FC', 'CDF', 'XAF', 'XOF', 'CFA', 'FRANC')

            if _is_franc:
                _equiv = net / _taux
                _equiv_str = f"{_equiv:,.2f}".replace(",", " ") + " $"
                _taux_str = f"{_taux:,.0f}".replace(",", " ")
                c.setFont(self._font_regular, 8)
                c.drawString(LEFT_MARGIN, y, f"Soit: {_equiv_str}")
                y -= 4 * mm
                c.drawString(LEFT_MARGIN, y, f"Taux: 1 $ = {_taux_str} FC")
                y -= 4 * mm
            elif _currency_norm in ('USD', '$', 'DOLLAR'):
                _equiv = net * _taux
                _equiv_rounded = int(round(_equiv))
                _equiv_str = f"{_equiv_rounded:,}".replace(",", " ") + " FC"
                _taux_str = f"{_taux:,.0f}".replace(",", " ")
                c.setFont(self._font_regular, 8)
                c.drawString(LEFT_MARGIN, y, f"Soit: {_equiv_str}")
                y -= 4 * mm
                c.drawString(LEFT_MARGIN, y, f"Taux: 1 $ = {_taux_str} FC")
                y -= 4 * mm
        # -----------------------------------

        c.setFont('Helvetica', 10)
        c.drawString(LEFT_MARGIN, y, f"Payé: {self.format_amount(total_paid)}")
        y -= 4 * mm

        # Afficher le change ou le reste à payer
        payment_status = invoice_data.get('payment_status', 'NON PAYÉE')
        change = _to_float(invoice_data.get('change', 0.0))
        reste_a_payer = _to_float(invoice_data.get('reste_a_payer', 0.0))
        
        c.setFont('Helvetica-Bold', 10)
        if change > 0:
            c.drawString(LEFT_MARGIN, y, f"Monnaie: {self.format_amount(change)}")
            y -= 4 * mm
        elif reste_a_payer > 0:
            c.drawString(LEFT_MARGIN, y, f"Reste: {self.format_amount(reste_a_payer)}")
            y -= 4 * mm

        # Afficher l'état du panier (en_cours, validé, annulé)
        if etat_clean:
            c.setFont(self._font_bold, 10)
            c.drawCentredString(TICKET_WIDTH / 2, y, f"État: {etat_clean}")
            y -= 4 * mm

        c.line(LEFT_MARGIN, y, TICKET_WIDTH - LEFT_MARGIN, y)
        y -= 4 * mm

        # =========================
        # NOTES - AFFICHER SI PRÉSENTES
        # =========================
        notes = invoice_data.get('notes', '')
        if notes and notes.strip() != '':
            y -= 2 * mm
            # Barre horizontale haute
            c.setFont(self._font_regular, 8)
            c.drawString(LEFT_MARGIN, y, "―" * 35)
            y -= 3 * mm
            
            # Titre NOTES
            c.setFont(self._font_bold, 9)
            c.drawString(LEFT_MARGIN, y, "NOTES")
            y -= 4 * mm
            
            # Contenu de la note (wrappé)
            c.setFont(self._font_regular, 8)
            y = _draw_wrapped(notes, self._font_regular, 8, TICKET_WIDTH - 2 * LEFT_MARGIN, y, center=False, leading=3 * mm)
            
            y -= 2 * mm
            # Barre horizontale basse
            c.setFont(self._font_regular, 8)
            c.drawString(LEFT_MARGIN, y, "―" * 35)
            y -= 4 * mm

        # =========================
        # NB
        # =========================
        nb = _get_company_slogan()
        if nb:
            c.setFont(self._font_regular, 8)
            y = _draw_wrapped(nb, self._font_regular, 8, TICKET_WIDTH - 2 * LEFT_MARGIN, y, center=True)

        # =========================
        # SIGNATURE / FOOTER
        # =========================
        gen_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        c.setFont(self._font_regular, 7)
        try:
            c.drawCentredString(TICKET_WIDTH / 2, y, "Informatisé par Ayanna ERP")
            y -= 3 * mm
            c.drawCentredString(TICKET_WIDTH / 2, y, "www.ayanna.top")
            y -= 3 * mm
            # Timestamp
            try:
                c.setFont(self._font_regular, 7)
                c.drawCentredString(TICKET_WIDTH / 2, y, f"Imprimé le {gen_time}")
            except Exception:
                pass
        except Exception:
            try:
                c.drawCentredString(TICKET_WIDTH / 2, y, f"Informatisé par Ayanna ERP {gen_time}")
            except Exception:
                pass

        c.save()
        return filename
