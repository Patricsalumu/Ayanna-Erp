"""
Utilitaire pour l'impression des réservations et reçus de paiement
Génération de PDF A4 (réservation complète) et tickets 53mm (reçus)
"""

import os
import io
import sys
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas

# Import du contrôleur d'entreprise
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
try:
    from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
except ImportError:
    EntrepriseController = None


class PaymentPrintManager:
    """Gestionnaire d'impression pour les paiements et réservations"""
    
    def __init__(self, enterprise_id=None):
        # Initialiser le contrôleur d'entreprise
        self.entreprise_controller = EntrepriseController() if EntrepriseController else None
        self.enterprise_id = enterprise_id  # Stocker l'ID de l'entreprise
        
        # Récupérer les informations de l'entreprise depuis la BDD
        if self.entreprise_controller:
            self.company_info = self.entreprise_controller.get_company_info_for_pdf(enterprise_id)
        else:
            # Fallback aux données statiques
            self.company_info = {
                'name': 'AYANNA ERP',
                'address': '123 Avenue de la République',
                'city': 'Kinshasa, RDC',
                'phone': '+243 123 456 789',
                'email': 'contact@ayanna-erp.com',
                'rccm': 'CD/KIN/RCCM/23-B-1234',
                'logo': None  # BLOB au lieu de logo_path
            }
        
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
        if self.entreprise_controller:
            self.company_info = self.entreprise_controller.get_company_info_for_pdf(enterprise_id)
            
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
            return "$"  # Fallback
    
    def format_amount(self, amount):
        """Formater un montant avec la devise de l'entreprise"""
        if self.entreprise_controller:
            return self.entreprise_controller.format_amount(amount, self.enterprise_id)
        else:
            return f"{amount:.2f} €"  # Fallback
    
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
    
    def print_reservation_a4(self, reservation_data, payment_history, filename):
        """Imprimer une réservation complète sur A4 (une seule page)"""
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=130, bottomMargin=55)
        story = []

        # ── Titre ────────────────────────────────────────────────────────────
        title = f"RÉSERVATION N° {reservation_data.get('reference', 'N/A')}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 6))

        # ── Informations client (nom + téléphone sur la même ligne) ─────────
        story.append(Paragraph("INFORMATIONS CLIENT", self.styles['CustomHeading']))

        client_data = [
            ['Nom du client:',
             reservation_data.get('client_nom', 'N/A'),
             'Téléphone:',
             reservation_data.get('client_telephone', 'N/A')],
        ]

        client_table = Table(client_data, colWidths=[3*cm, 7*cm, 2.5*cm, 3.5*cm])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#ECF0F1')),
            ('BACKGROUND', (2, 0), (2, -1), HexColor('#ECF0F1')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
        ]))
        story.append(client_table)
        story.append(Spacer(1, 8))

        # ── Détails de l'événement (compactés) ────────────────────────────────
        story.append(Paragraph("DÉTAILS DE L'ÉVÉNEMENT", self.styles['CustomHeading']))

        # Ligne 1 : Type | valeur | Invités | valeur | Thème | valeur
        # Ligne 2 : Date événement | valeur | Date création | valeur | (vide) | (vide)
        event_data = [
            ['Type:',
             reservation_data.get('event_type', 'N/A'),
             'Invités:',
             str(reservation_data.get('guest_count', 0)),
             'Thème:',
             reservation_data.get('theme', 'N/A')],
            ['Date événement:',
             reservation_data.get('event_date', 'N/A'),
             'Date création:',
             reservation_data.get('created_at', 'N/A'),
             '', ''],
        ]

        event_table = Table(event_data,
                            colWidths=[2.8*cm, 4.3*cm, 2.2*cm, 2.0*cm, 1.8*cm, 2.9*cm])
        event_table.setStyle(TableStyle([
            # Fond sur les colonnes "label" (0, 2, 4)
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#E8F6F3')),
            ('BACKGROUND', (2, 0), (2, -1), HexColor('#E8F6F3')),
            ('BACKGROUND', (4, 0), (4, -1), HexColor('#E8F6F3')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (4, 0), (4, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
            # Fusionner les cellules vides de la ligne "dates"
            ('SPAN', (4, 1), (5, 1)),
        ]))
        story.append(event_table)
        story.append(Spacer(1, 8))

        # ── Services sélectionnés ─────────────────────────────────────────────
        if reservation_data.get('services'):
            story.append(Paragraph("SERVICES SÉLECTIONNÉS", self.styles['CustomHeading']))

            services_data = [['Service', 'Quantité', 'Prix unitaire', 'Total']]
            total_services = 0

            for service in reservation_data['services']:
                total_line = service['quantity'] * service['unit_price']
                total_services += total_line
                currency_symbol = self.get_currency_symbol()
                services_data.append([
                    service['name'],
                    str(service['quantity']),
                    f"{service['unit_price']:.2f} {currency_symbol}",
                    f"{total_line:.2f} {currency_symbol}"
                ])

            currency_symbol = self.get_currency_symbol()
            services_data.append(['', '', 'TOTAL SERVICES:', f"{total_services:.2f} {currency_symbol}"])

            services_table = Table(services_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
            services_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, -1), (-1, -1), HexColor('#D5DBDB')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            story.append(services_table)
            story.append(Spacer(1, 8))

        # ── Produits sélectionnés ─────────────────────────────────────────────
        if reservation_data.get('products'):
            story.append(Paragraph("PRODUITS SÉLECTIONNÉS", self.styles['CustomHeading']))

            products_data = [['Produit', 'Quantité', 'Prix unitaire', 'Total']]
            total_products = 0

            for product in reservation_data['products']:
                total_line = product['quantity'] * product['unit_price']
                total_products += total_line
                currency_symbol = self.get_currency_symbol()
                products_data.append([
                    product['name'],
                    str(product['quantity']),
                    f"{product['unit_price']:.2f} {currency_symbol}",
                    f"{total_line:.2f} {currency_symbol}"
                ])

            currency_symbol = self.get_currency_symbol()
            products_data.append(['', '', 'TOTAL PRODUITS:', f"{total_products:.2f} {currency_symbol}"])

            products_table = Table(products_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
            products_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E67E22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, -1), (-1, -1), HexColor('#D5DBDB')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            story.append(products_table)
            story.append(Spacer(1, 8))

        # ── Récapitulatif financier ────────────────────────────────────────────
        story.append(Paragraph("RÉCAPITULATIF FINANCIER", self.styles['CustomHeading']))

        currency_symbol = self.get_currency_symbol()
        financial_data = [
            ['Total Services:', f"{reservation_data.get('total_services', 0):.2f} {currency_symbol}"],
            ['Total Produits:', f"{reservation_data.get('total_products', 0):.2f} {currency_symbol}"],
            ['Sous-total HT:', f"{reservation_data.get('subtotal_ht', 0):.2f} {currency_symbol}"],
            ['TVA:', f"{reservation_data.get('tax_amount', 0):.2f} {currency_symbol}"],
            ['Total TTC:', f"{reservation_data.get('total_ttc', 0):.2f} {currency_symbol}"],
            ['Remise:', f"-{reservation_data.get('discount_amount', 0):.2f} {currency_symbol}"],
            ['NET À PAYER:', f"{reservation_data.get('total_net', 0):.2f} {currency_symbol}"]
        ]

        financial_table = Table(financial_data, colWidths=[12*cm, 4*cm])
        financial_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), HexColor('#2ECC71')),
            ('TEXTCOLOR', (0, -1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
        ]))
        story.append(financial_table)
        story.append(Spacer(1, 8))

        # ── Historique des paiements ──────────────────────────────────────────
        story.append(Paragraph("HISTORIQUE DES PAIEMENTS", self.styles['CustomHeading']))

        if payment_history:
            payment_data = [['Date', 'Montant', 'Méthode', 'Utilisateur']]
            total_paid = 0

            for payment in payment_history:
                total_paid += payment.get('amount', 0)

                payment_date = payment.get('payment_date', 'N/A')
                if payment_date != 'N/A' and isinstance(payment_date, str):
                    try:
                        from datetime import datetime
                        for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                                    '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M']:
                            try:
                                dt = datetime.strptime(payment_date, fmt)
                                payment_date = dt.strftime('%d/%m/%Y %H:%M')
                                break
                            except ValueError:
                                continue
                    except Exception:
                        payment_date = payment_date[:16] if len(payment_date) > 16 else payment_date

                user_name = payment.get('user_name', 'N/A')
                if user_name and user_name != 'N/A':
                    keywords_to_remove = [
                        'acompte automatique pour réservation',
                        'automatique pour réservation',
                        'pour réservation',
                        'acompte automatique',
                        'paiement automatique'
                    ]
                    user_name_clean = user_name
                    for keyword in keywords_to_remove:
                        if keyword.lower() in user_name_clean.lower():
                            index = user_name_clean.lower().find(keyword.lower())
                            user_name_clean = user_name_clean[:index].strip()
                            break
                    if not user_name_clean or len(user_name_clean) < 3:
                        user_name_clean = "N/A"
                    user_name = user_name_clean[:30] if len(user_name_clean) > 30 else user_name_clean

                currency_symbol = self.get_currency_symbol()
                payment_data.append([
                    payment_date,
                    f"{payment.get('amount', 0):.2f} {currency_symbol}",
                    payment.get('payment_method', 'N/A'),
                    user_name
                ])

            net_a_payer = reservation_data.get('total_net', reservation_data.get('net_a_payer', 0))
            balance = net_a_payer - total_paid
            currency_symbol = self.get_currency_symbol()
            payment_data.append(['', '', 'TOTAL PAYÉ:', f"{total_paid:.2f} {currency_symbol}"])
            payment_data.append(['', '', 'RESTE À PAYER:', f"{balance:.2f} {currency_symbol}"])

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

        story.append(Spacer(1, 8))

        # ── Notes (affichées seulement si présentes) ───────────────────────────
        notes = (reservation_data.get('notes', '') or
                 reservation_data.get('comments', '') or
                 reservation_data.get('note', '') or
                 reservation_data.get('comment', '') or
                 reservation_data.get('description', ''))

        if notes and notes.strip() and notes.lower() not in ['aucune', 'n/a', 'null', 'none']:
            story.append(Paragraph("NOTES ET COMMENTAIRES", self.styles['CustomHeading']))

            notes_style = ParagraphStyle(
                'NotesStyle',
                parent=self.styles['CustomNormal'],
                fontSize=9,
                leading=11,
                alignment=0,
                spaceAfter=4,
                leftIndent=8,
                rightIndent=8
            )

            notes_table = Table([[Paragraph(notes, notes_style)]], colWidths=[16*cm])
            notes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#FAFBFC')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7')),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
            ]))
            story.append(notes_table)

        # Construire le PDF
        doc.build(story, onFirstPage=self.create_header_a4, onLaterPages=self.create_header_a4)

        return filename

    # ──────────────────────────────────────────────────────────────────────────
    # LISTE DES RÉSERVATIONS (A4 paysage)
    # ──────────────────────────────────────────────────────────────────────────

    def _make_header_landscape(self, page_size):
        """Retourne un callback d'en-tête adapté au format paysage."""
        pw, ph = page_size

        def _header(canv, doc):
            canv.saveState()

            # Filigrane bas de page
            canv.setFont('Helvetica-Bold', 9)
            canv.setFillColor(HexColor('#555555'))
            gen_text = f"Généré par Ayanna Erp App © - {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
            tw = canv.stringWidth(gen_text, 'Helvetica-Bold', 9)
            canv.drawString((pw - tw) / 2, 12, gen_text)

            # Fond en-tête
            canv.setFillColor(HexColor('#F8F9FA'))
            canv.rect(0, ph - 100, pw, 100, fill=1, stroke=0)

            # Ligne de séparation
            canv.setStrokeColor(HexColor('#3498DB'))
            canv.setLineWidth(2)
            canv.line(40, ph - 100, pw - 40, ph - 100)

            # Logo
            logo_path = self._create_temp_logo_file()
            if logo_path and os.path.exists(logo_path):
                try:
                    canv.drawImage(logo_path, 40, ph - 92,
                                   width=50, height=50, preserveAspectRatio=True)
                except Exception:
                    pass

            # Nom entreprise + coordonnées (gauche)
            canv.setFont('Helvetica-Bold', 14)
            canv.setFillColor(HexColor('#2C3E50'))
            canv.drawString(100, ph - 45, self.company_info['name'])
            canv.setFont('Helvetica', 9)
            canv.setFillColor(black)
            canv.drawString(100, ph - 58, self.company_info['address'])
            canv.drawString(100, ph - 69, self.company_info['city'])
            canv.drawString(100, ph - 80, f"Tél: {self.company_info['phone']}")

            # Coordonnées droite
            canv.drawRightString(pw - 40, ph - 58, f"Email: {self.company_info['email']}")
            canv.drawRightString(pw - 40, ph - 69, f"RCCM: {self.company_info['rccm']}")
            canv.drawRightString(pw - 40, ph - 80, f"Date: {datetime.now().strftime('%d/%m/%Y')}")

            # Numéro de page
            canv.setFont('Helvetica', 8)
            canv.setFillColor(HexColor('#7F8C8D'))
            p_text = f"Page {canv.getPageNumber()}"
            canv.drawString((pw - canv.stringWidth(p_text, 'Helvetica', 8)) / 2, 30, p_text)
            canv.setStrokeColor(HexColor('#BDC3C7'))
            canv.setLineWidth(1)
            canv.line(40, 42, pw - 40, 42)

            canv.restoreState()

        return _header

    def print_reservations_list_pdf(self, reservations, period_label, filename):
        """
        Génère un PDF A4 paysage listant toutes les réservations passées en paramètre.

        Args:
            reservations (list): liste de dicts réservation (avec 'created_by_name')
            period_label (str): texte décrivant la période filtrée, ex "Du 24/05/2026 au 25/05/2026"
            filename (str): chemin complet du fichier PDF à créer
        Returns:
            str: chemin du fichier créé
        """
        PAGE_SIZE = landscape(A4)
        pw, ph = PAGE_SIZE

        doc = SimpleDocTemplate(
            filename,
            pagesize=PAGE_SIZE,
            topMargin=115,
            bottomMargin=55,
            leftMargin=40,
            rightMargin=40
        )

        story = []

        # ── Titre ───────────────────────────────────────────────────────────
        title_style = ParagraphStyle(
            'ListTitle',
            parent=self.styles['Normal'],
            fontSize=14, fontName='Helvetica-Bold',
            textColor=HexColor('#2C3E50'),
            alignment=TA_CENTER, spaceAfter=4
        )
        sub_style = ParagraphStyle(
            'ListSub',
            parent=self.styles['Normal'],
            fontSize=9, fontName='Helvetica',
            textColor=HexColor('#7F8C8D'),
            alignment=TA_CENTER, spaceAfter=12
        )
        story.append(Paragraph("LISTE DES RÉSERVATIONS", title_style))
        story.append(Paragraph(period_label, sub_style))

        if not reservations:
            story.append(Paragraph("Aucune réservation pour cette période.", self.styles['Normal']))
            doc.build(story, onFirstPage=self._make_header_landscape(PAGE_SIZE),
                      onLaterPages=self._make_header_landscape(PAGE_SIZE))
            return filename

        cur = self.get_currency_symbol()

        # ── En-tête du tableau ───────────────────────────────────────────────
        header = [
            'Réf.', 'Client', 'Téléphone',
            'Type événement', 'Date événement',
            f'Total TTC\n({cur})', f'Payé\n({cur})', f'Solde\n({cur})',
            'Créé le', 'Créé par'
        ]
        header_row = [Paragraph(f'<b>{h}</b>', ParagraphStyle(
            'TH', parent=self.styles['Normal'],
            fontSize=8, fontName='Helvetica-Bold',
            textColor=white, alignment=TA_CENTER
        )) for h in header]

        data = [header_row]

        # Totaux
        sum_total = sum_paid = sum_balance = 0.0

        cell_style = ParagraphStyle(
            'TD', parent=self.styles['Normal'],
            fontSize=8, fontName='Helvetica',
            textColor=HexColor('#2C3E50'), alignment=TA_LEFT,
            leading=10
        )
        cell_center = ParagraphStyle(
            'TDC', parent=cell_style, alignment=TA_RIGHT
        )

        for idx, r in enumerate(reservations):
            ref_id = r.get('id') or r.get('reference', '')
            ref = f"RES-{ref_id}"

            ev_date = r.get('event_date')
            ev_str = (ev_date.strftime('%d/%m/%Y %H:%M')
                      if ev_date and not isinstance(ev_date, str) else (ev_date or ''))

            cr_date = r.get('created_at')
            cr_str = (cr_date.strftime('%d/%m/%Y %H:%M')
                      if cr_date and not isinstance(cr_date, str) else (cr_date or ''))

            total  = float(r.get('total_amount', 0) or 0)
            balance = float(r.get('balance', 0) or 0)
            paid   = total - balance

            sum_total   += total
            sum_paid    += paid
            sum_balance += balance

            row = [
                Paragraph(ref,                                     cell_style),
                Paragraph(r.get('client_nom', '') or '',          cell_style),
                Paragraph(r.get('client_telephone', '') or '',    cell_style),
                Paragraph(r.get('event_type', '') or '',          cell_style),
                Paragraph(ev_str,                                  cell_style),
                Paragraph(f"{total:.2f}",                          cell_center),
                Paragraph(f"{paid:.2f}",                           cell_center),
                Paragraph(f"{balance:.2f}",                        cell_center),
                Paragraph(cr_str,                                  cell_style),
                Paragraph(r.get('created_by_name', 'Inconnu') or 'Inconnu', cell_style),
            ]
            data.append(row)

        # ── Ligne de totaux ──────────────────────────────────────────────────
        total_label_style = ParagraphStyle(
            'TotLbl', parent=self.styles['Normal'],
            fontSize=8, fontName='Helvetica-Bold',
            textColor=HexColor('#2C3E50'), alignment=TA_RIGHT
        )
        total_val_style = ParagraphStyle(
            'TotVal', parent=self.styles['Normal'],
            fontSize=8, fontName='Helvetica-Bold',
            textColor=HexColor('#2C3E50'), alignment=TA_RIGHT
        )
        data.append([
            Paragraph(f'<b>TOTAL ({len(reservations)} rés.)</b>', total_label_style),
            '', '', '', '',
            Paragraph(f"<b>{sum_total:.2f}</b>",   total_val_style),
            Paragraph(f"<b>{sum_paid:.2f}</b>",    total_val_style),
            Paragraph(f"<b>{sum_balance:.2f}</b>", total_val_style),
            '', ''
        ])

        # ── Largeurs colonnes (total ≈ pw - 80 mm) ──────────────────────────
        # paysage A4 utilisable ≈ 717 pt - 80 pt marges = 637 pt
        col_widths = [
            1.8*cm,  # Réf
            3.5*cm,  # Client
            2.4*cm,  # Téléphone
            2.8*cm,  # Type événement
            2.8*cm,  # Date événement
            2.2*cm,  # Total TTC
            2.2*cm,  # Payé
            2.2*cm,  # Solde
            2.6*cm,  # Créé le
            3.0*cm,  # Créé par
        ]

        tbl = Table(data, colWidths=col_widths, repeatRows=1)

        n_rows = len(data)
        last_data_row = n_rows - 2  # avant ligne total

        tbl.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND',   (0, 0), (-1, 0),  HexColor('#2980B9')),
            ('TEXTCOLOR',    (0, 0), (-1, 0),  white),
            ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',     (0, 0), (-1, 0),  8),
            ('ALIGN',        (0, 0), (-1, 0),  'CENTER'),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            # Grille
            ('GRID',         (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
            # Alternance de couleur
            *[('BACKGROUND', (0, r), (-1, r),
               HexColor('#EBF5FB') if r % 2 == 1 else white)
              for r in range(1, n_rows - 1)],
            # Ligne total
            ('BACKGROUND',   (0, -1), (-1, -1), HexColor('#D5DBDB')),
            ('FONTNAME',     (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN',         (0, -1), (4, -1)),
            # Padding
            ('TOPPADDING',   (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
            ('LEFTPADDING',  (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        story.append(tbl)

        cb = self._make_header_landscape(PAGE_SIZE)
        doc.build(story, onFirstPage=cb, onLaterPages=cb)
        return filename

    # ──────────────────────────────────────────────────────────────────────────
    # CALENDRIER MENSUEL (A4 portrait)
    # ──────────────────────────────────────────────────────────────────────────

    def print_calendar_month_pdf(self, year, month, events_by_date, filename):
        """
        Génère un PDF A4 paysage représentant le calendrier d'un mois.
        Dates futures en orange, passées en gris fondu. Nom client complet affiché.
        """
        import calendar as cal_module
        from datetime import date as date_type

        PAGE_SIZE = landscape(A4)
        pw, ph = PAGE_SIZE        # 841.89 × 595.28 pt

        c = canvas.Canvas(filename, pagesize=PAGE_SIZE)

        # ── En-tête paysage ──────────────────────────────────────────────────
        header_fn = self._make_header_landscape(PAGE_SIZE)
        header_fn(c, None)

        # ── Titre mois / année ───────────────────────────────────────────────
        MONTH_FR = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        month_title = f"CALENDRIER  –  {MONTH_FR[month - 1].upper()}  {year}"
        c.setFont('Helvetica-Bold', 14)
        c.setFillColor(HexColor('#2C3E50'))
        tw = c.stringWidth(month_title, 'Helvetica-Bold', 14)
        c.drawString((pw - tw) / 2, ph - 112, month_title)

        # ── Dimensions de la grille ──────────────────────────────────────────
        MARGIN_LEFT  = 30
        MARGIN_RIGHT = 30
        cal_width    = pw - MARGIN_LEFT - MARGIN_RIGHT   # ≈ 782 pt
        cell_width   = cal_width / 7                     # ≈ 111 pt par colonne

        GRID_TOP  = ph - 128   # Juste sous le titre
        DAY_ROW_H = 22
        BOTTOM    = 50

        weeks       = cal_module.monthcalendar(year, month)
        num_weeks   = len(weeks)
        avail_h     = GRID_TOP - DAY_ROW_H - BOTTOM
        cell_height = avail_h / num_weeks               # ≈ 83-100 pt selon nb semaines

        today = datetime.now().date()

        # ── Ligne noms des jours ─────────────────────────────────────────────
        DAY_NAMES = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI', 'DIMANCHE']
        for i, dn in enumerate(DAY_NAMES):
            x     = MARGIN_LEFT + i * cell_width
            y     = GRID_TOP - DAY_ROW_H
            is_we = i >= 5
            c.setFillColor(HexColor('#95A5A6') if is_we else HexColor('#2980B9'))
            c.rect(x, y, cell_width, DAY_ROW_H, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont('Helvetica-Bold', 8)
            twd = c.stringWidth(dn, 'Helvetica-Bold', 8)
            c.drawString(x + (cell_width - twd) / 2, y + 7, dn)

        # ── Grille des semaines ──────────────────────────────────────────────
        for wk_idx, week in enumerate(weeks):
            row_top    = GRID_TOP - DAY_ROW_H - wk_idx * cell_height
            row_bottom = row_top - cell_height

            for di, day in enumerate(week):
                x = MARGIN_LEFT + di * cell_width

                if day == 0:
                    c.setFillColor(HexColor('#F2F3F4'))
                    c.setStrokeColor(HexColor('#D5D8DC'))
                    c.rect(x, row_bottom, cell_width, cell_height, fill=1, stroke=1)
                    continue

                day_date  = date_type(year, month, day)
                events    = events_by_date.get(day_date, [])
                is_future = day_date >= today
                is_today  = day_date == today

                # Couleur de fond de la cellule
                if events:
                    bg_cell    = HexColor('#FFF3E0') if is_future else HexColor('#EAECEE')
                    border_clr = HexColor('#F39C12') if is_future else HexColor('#AEB6BF')
                else:
                    bg_cell    = white
                    border_clr = HexColor('#D5D8DC')

                c.setFillColor(bg_cell)
                c.setStrokeColor(border_clr)
                c.setLineWidth(0.8)
                c.rect(x, row_bottom, cell_width, cell_height, fill=1, stroke=1)

                # Numéro du jour
                day_str = str(day)
                c.setFont('Helvetica-Bold', 9)
                if is_today:
                    cx_d = x + 10
                    cy_d = row_top - 10
                    c.setFillColor(HexColor('#2980B9'))
                    c.circle(cx_d, cy_d, 9, fill=1, stroke=0)
                    c.setFillColor(white)
                    twd = c.stringWidth(day_str, 'Helvetica-Bold', 9)
                    c.drawString(cx_d - twd / 2, cy_d - 3.5, day_str)
                else:
                    c.setFillColor(HexColor('#E67E22') if (events and is_future)
                                   else HexColor('#566573') if (events and not is_future)
                                   else HexColor('#2C3E50'))
                    c.drawString(x + 4, row_top - 14, day_str)

                # Badges événements (nom complet sur 2 lignes)
                if events:
                    BADGE_H = 22          # Assez pour 2 lignes
                    GAP     = 2
                    ev_top  = row_top - 20
                    max_fit = int((ev_top - row_bottom - 4) / (BADGE_H + GAP))
                    visible  = events[:max(1, max_fit)]
                    overflow = len(events) - len(visible)

                    for ev in visible:
                        if ev_top - BADGE_H < row_bottom + 4:
                            break

                        ev_bg   = HexColor('#F39C12') if is_future else HexColor('#AEB6BF')
                        ev_text = HexColor('#7D6608') if is_future else HexColor('#2C3E50')

                        c.setFillColor(ev_bg)
                        c.roundRect(x + 3, ev_top - BADGE_H,
                                    cell_width - 6, BADGE_H, 2, fill=1, stroke=0)

                        ref    = f"RES-{ev['id']}"
                        client = ev['client_name']   # Nom complet, pas tronqué

                        # Ligne 1 : référence (bold)
                        c.setFillColor(ev_text)
                        c.setFont('Helvetica-Bold', 6.5)
                        c.drawString(x + 5, ev_top - 9, ref)

                        # Ligne 2 : nom client complet (ajusté si trop long)
                        c.setFont('Helvetica', 6.5)
                        max_w = cell_width - 10
                        while (c.stringWidth(client, 'Helvetica', 6.5) > max_w
                               and len(client) > 4):
                            client = client[:-1]
                        if client != ev['client_name']:
                            client += '.'
                        c.drawString(x + 5, ev_top - BADGE_H + 4, client)

                        ev_top -= BADGE_H + GAP

                    if overflow > 0:
                        c.setFillColor(HexColor('#7F8C8D'))
                        c.setFont('Helvetica-Oblique', 5.5)
                        c.drawString(x + 3, row_bottom + 3, f"+{overflow} autre(s)")

        # ── Bordure extérieure ───────────────────────────────────────────────
        total_h = DAY_ROW_H + num_weeks * cell_height
        c.setStrokeColor(HexColor('#2980B9'))
        c.setLineWidth(1.5)
        c.rect(MARGIN_LEFT, GRID_TOP - total_h, cal_width, total_h, fill=0, stroke=1)

        # ── Légende ──────────────────────────────────────────────────────────
        leg_y = BOTTOM - 14
        leg_x = MARGIN_LEFT
        for color_hex, label in [('#F39C12', 'Événement à venir'),
                                  ('#AEB6BF', 'Événement passé')]:
            c.setFillColor(HexColor(color_hex))
            c.rect(leg_x, leg_y, 11, 9, fill=1, stroke=0)
            c.setFillColor(HexColor('#2C3E50'))
            c.setFont('Helvetica', 7)
            c.drawString(leg_x + 14, leg_y + 1, label)
            leg_x += 130
        # Aujourd'hui
        c.setFillColor(HexColor('#2980B9'))
        c.circle(leg_x + 6, leg_y + 4.5, 5.5, fill=1, stroke=0)
        c.setFillColor(HexColor('#2C3E50'))
        c.setFont('Helvetica', 7)
        c.drawString(leg_x + 14, leg_y + 1, "Aujourd'hui")

        c.showPage()
        c.save()
        return filename

    def print_receipt_53mm(self, reservation_data, payments_list, user_name, filename):
        """Imprimer un reçu de paiement sur format 53mm avec détail de tous les paiements"""
        # Taille du ticket 53mm de large (format imprimante thermique)
        TICKET_WIDTH = 53 * mm
        # Estimer la hauteur nécessaire
        base_height = 80  # En-tête et pied de page
        payment_height = len(payments_list) * 30 if payments_list else 20  # 30mm par paiement
        TICKET_HEIGHT = (base_height + payment_height) * mm
        
        # Créer le document PDF
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate
        doc = SimpleDocTemplate(filename, pagesize=(TICKET_WIDTH, TICKET_HEIGHT),
                              rightMargin=1*mm, leftMargin=1*mm, 
                              topMargin=1*mm, bottomMargin=1*mm)
        
        # Créer le canvas pour dessiner
        c = canvas.Canvas(filename, pagesize=(TICKET_WIDTH, TICKET_HEIGHT))
        
        y_position = TICKET_HEIGHT - 5*mm  # Commencer en haut
        line_height = 4*mm  # Espacement entre les lignes
        
        # Logo et en-tête entreprise (taille réduite pour 53mm)
        logo_path = self._create_temp_logo_file()
        if logo_path and os.path.exists(logo_path):
            try:
                logo_width = 15*mm
                logo_height = 10*mm
                c.drawImage(logo_path, 
                           (TICKET_WIDTH - logo_width) / 2, y_position - logo_height, 
                           width=logo_width, height=logo_height, preserveAspectRatio=True)
                y_position -= logo_height + 2*mm
            except Exception as e:
                print(f"Erreur logo: {e}")
                pass
        
        # Nom de l'entreprise
        c.setFont('Helvetica-Bold', 11)  # Augmenté de 7 à 12
        text = self.company_info['name'][:30]  # Limiter la longueur
        text_width = c.stringWidth(text, 'Helvetica-Bold', 11)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, text)
        y_position -= line_height
        
        # Coordonnées entreprise (police très petite)
        c.setFont('Helvetica', 8)  # Augmenté de 5 à 10
        for info in [self.company_info['phone'], self.company_info['email']]:
            if info:
                info_text = info[:35]  # Limiter la longueur
                text_width = c.stringWidth(info_text, 'Helvetica', 8)
                c.drawString((TICKET_WIDTH - text_width) / 2, y_position, info_text)
                y_position -= 2.5*mm
        
        # Adresse sur une ligne
        if self.company_info['address']:
            address_text = self.company_info['address'][:40]
            text_width = c.stringWidth(address_text, 'Helvetica', 8)
            c.drawString((TICKET_WIDTH - text_width) / 2, y_position, address_text)
            y_position -= 2.5*mm
        
        # RCCM
        if self.company_info['rccm']:
            rccm_text = self.company_info['rccm'][:30]
            text_width = c.stringWidth(rccm_text, 'Helvetica', 8)
            c.drawString((TICKET_WIDTH - text_width) / 2, y_position, rccm_text)
            y_position -= 2.5*mm
        
        # Ligne de séparation
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        # Titre du reçu
        c.setFont('Helvetica-Bold', 8   )  # Augmenté de 8 à 14
        title = "RECU DE PAIEMENT"
        text_width = c.stringWidth(title, 'Helvetica-Bold', 11)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, title)
        y_position -= line_height + 2*mm
        
        # Informations de base de la réservation (format compact)
        c.setFont('Helvetica', 8)  # Augmenté de 5 à 10
        
        # Référence
        ref_text = f"Ref: {reservation_data.get('reference', 'N/A')[:15]}"
        c.drawString(2*mm, y_position, ref_text)
        y_position -= 2.5*mm
        
        # Client (limiter la longueur)
        client_name = reservation_data.get('client_nom', 'N/A')[:30]
        client_text = f"Client: {client_name}"
        c.drawString(2*mm, y_position, client_text)
        y_position -= 2.5*mm
        
        # Téléphone
        phone_text = f"Tel: {reservation_data.get('client_telephone', 'N/A')[:15]}"
        c.drawString(2*mm, y_position, phone_text)
        y_position -= 2.5*mm
        
        # Type
        event_type = reservation_data.get('event_type', 'N/A')[:15]
        type_text = f"Type: {event_type}"
        c.drawString(2*mm, y_position, type_text)
        y_position -= 2.5*mm
        
        # Date événement
        event_date = reservation_data.get('event_date', 'N/A')[:20]
        date_text = f"Date: {event_date}"
        c.drawString(2*mm, y_position, date_text)
        y_position -= 2.5*mm
        
        # Ligne de séparation
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        # Détail de chaque paiement
        c.setFont('Helvetica-Bold', 7)  # Augmenté de 6 à 11
        c.drawString(2*mm, y_position, "DETAIL PAIEMENTS:")
        y_position -= 3*mm
        
        total_paid = 0
        
        if payments_list:
            for i, payment in enumerate(payments_list, 1):
                payment_amount = payment.get('amount', 0)
                total_paid += payment_amount
                
                # Numéro et montant sur une ligne
                c.setFont('Helvetica-Bold', 7)  # Augmenté de 5 à 10
                currency_symbol = self.get_currency_symbol()
                payment_line = f"#{i}: {payment_amount:.2f} {currency_symbol}"
                c.drawString(2*mm, y_position, payment_line)
                y_position -= 3.5*mm
                
                # Méthode
                c.setFont('Helvetica', 6)  # Augmenté de 4 à 8
                method_text = payment.get('payment_method', 'N/A')[:20]
                c.drawString(3*mm, y_position, method_text)
                y_position -= 2*mm
                
                # Date
                date_text = payment.get('payment_date', 'N/A')[:20]
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
            c.setFont('Helvetica', 6)  # Augmenté de 5 à 10
            c.drawString(2*mm, y_position, "Aucun paiement")
            y_position -= 3*mm
        
        # Récapitulatif final
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        c.setFont('Helvetica-Bold', 7)  # Augmenté de 6 à 11
        c.drawString(2*mm, y_position, "RECAPITULATIF:")
        y_position -= 3*mm
        
        c.setFont('Helvetica', 7)  # Augmenté de 5 à 10
        # Utiliser le net à payer (après remise) au lieu du total brut
        net_a_payer = reservation_data.get('total_net', reservation_data.get('net_a_payer', 0))
        balance = net_a_payer - total_paid
        currency_symbol = self.get_currency_symbol()
        
        # Net à payer (après remise)
        total_text = f"Net a payer: {net_a_payer:.2f} {currency_symbol}"
        c.drawString(2*mm, y_position, total_text)
        y_position -= 3.5*mm
        
        # Total payé
        paid_text = f"Paye: {total_paid:.2f} {currency_symbol}"
        c.drawString(2*mm, y_position, paid_text)
        y_position -= 3.5*mm
        
        # Reste à payer
        c.setFont('Helvetica-Bold', 8)  # Augmenté de 5 à 10
        balance_text = f"Reste: {balance:.2f} {currency_symbol}"
        c.drawString(2*mm, y_position, balance_text)
        y_position -= 3*mm
        
        # Ligne de séparation finale
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        # Filigrane avec nom d'entreprise dynamique
        c.setFont('Helvetica', 6)  # Augmenté de 4 à 8
        generation_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        filigrane_text = f"Ayanna Erp App (c) {generation_time}"
        text_width = c.stringWidth(filigrane_text, 'Helvetica', 8)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, filigrane_text)
        
        # Sauvegarder le PDF
        c.save()
        
        return filename