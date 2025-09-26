"""
Utilitaire pour l'impression des réservations et reçus de paiement
Génération de PDF A4 (réservation complète) et tickets 53mm (reçus)
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
        filigrane_text = f"Généré par {self.company_info['name']} © - {generation_time}"
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
        """Imprimer une réservation complète sur A4"""
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=150, bottomMargin=60)
        story = []
        
        # Titre du document
        title = f"RÉSERVATION N° {reservation_data.get('reference', 'N/A')}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Informations client
        story.append(Paragraph("INFORMATIONS CLIENT", self.styles['CustomHeading']))
        
        client_data = [
            ['Nom du client:', reservation_data.get('client_nom', 'N/A')],
            ['Téléphone:', reservation_data.get('client_telephone', 'N/A')],
            ['Email:', reservation_data.get('client_email', 'N/A')],
            ['Adresse:', reservation_data.get('client_adresse', 'N/A')]
        ]
        
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
        
        # Informations événement
        story.append(Paragraph("DÉTAILS DE L'ÉVÉNEMENT", self.styles['CustomHeading']))
        
        event_data = [
            ['Type d\'événement:', reservation_data.get('event_type', 'N/A')],
            ['Date de l\'événement:', reservation_data.get('event_date', 'N/A')],
            ['Date de création:', reservation_data.get('created_at', 'N/A')],
            ['Nombre d\'invités:', str(reservation_data.get('guest_count', 0))],
            ['Thème:', reservation_data.get('theme', 'N/A')]
        ]
        
        event_table = Table(event_data, colWidths=[4*cm, 12*cm])
        event_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#E8F6F3')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
        ]))
        story.append(event_table)
        story.append(Spacer(1, 15))
        
        # Services sélectionnés
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
            story.append(Spacer(1, 15))
        
        # Produits sélectionnés
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
            story.append(Spacer(1, 15))
        
        # Récapitulatif financier
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
        
        if payment_history:
            payment_data = [['Date', 'Montant', 'Méthode', 'Utilisateur']]
            total_paid = 0
            
            for payment in payment_history:
                total_paid += payment.get('amount', 0)
                
                # Formater la date pour enlever les millisecondes et secondes
                payment_date = payment.get('payment_date', 'N/A')
                if payment_date != 'N/A' and isinstance(payment_date, str):
                    try:
                        # Essayer de parser la date et la reformater
                        from datetime import datetime
                        # Gérer plusieurs formats possibles
                        for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M']:
                            try:
                                dt = datetime.strptime(payment_date, fmt)
                                payment_date = dt.strftime('%d/%m/%Y %H:%M')
                                break
                            except ValueError:
                                continue
                    except:
                        # Si le parsing échoue, garder les 16 premiers caractères (sans millisecondes)
                        payment_date = payment_date[:16] if len(payment_date) > 16 else payment_date
                
                # Nettoyer le nom d'utilisateur pour enlever les notes de paiement
                user_name = payment.get('user_name', 'N/A')
                if user_name and user_name != 'N/A':
                    # Supprimer les mots-clés indiquant des notes automatiques
                    keywords_to_remove = [
                        'acompte automatique pour réservation',
                        'automatique pour réservation', 
                        'pour réservation',
                        'acompte automatique',
                        'paiement automatique'
                    ]
                    
                    user_name_clean = user_name
                    for keyword in keywords_to_remove:
                        # Recherche insensible à la casse
                        if keyword.lower() in user_name_clean.lower():
                            # Supprimer le keyword et ce qui suit
                            index = user_name_clean.lower().find(keyword.lower())
                            user_name_clean = user_name_clean[:index].strip()
                            break
                    
                    # Si le nom devient vide ou trop court, utiliser une valeur par défaut
                    if not user_name_clean or len(user_name_clean) < 3:
                        user_name_clean = "Système"
                    
                    # Limiter la longueur pour éviter le débordement
                    user_name = user_name_clean[:20] if len(user_name_clean) > 20 else user_name_clean
                
                currency_symbol = self.get_currency_symbol()
                payment_data.append([
                    payment_date,
                    f"{payment.get('amount', 0):.2f} {currency_symbol}",
                    payment.get('payment_method', 'N/A'),
                    user_name
                ])
            
            # Calculer le solde sur le net à payer (après remise)
            net_a_payer = reservation_data.get('total_net', reservation_data.get('net_a_payer', 0))
            balance = net_a_payer - total_paid
            currency_symbol = self.get_currency_symbol()
            payment_data.append(['', '', 'TOTAL PAYÉ:', f"{total_paid:.2f} {currency_symbol}"])
            payment_data.append(['', '', 'RESTE À PAYER:', f"{balance:.2f} {currency_symbol}"])
            
            # Ajuster les largeurs de colonnes pour éviter le débordement (4 colonnes maintenant)
            payment_table = Table(payment_data, colWidths=[4*cm, 3*cm, 4*cm, 5*cm])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#9B59B6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # Police plus petite
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
        
        # Récupérer les vraies notes/commentaires depuis les données de réservation
        # Essayer plusieurs champs possibles pour les commentaires
        notes = (reservation_data.get('notes', '') or 
                reservation_data.get('comments', '') or 
                reservation_data.get('note', '') or 
                reservation_data.get('comment', '') or 
                reservation_data.get('description', ''))
        
        # Nettoyer les notes
        if not notes or notes.strip() == '' or notes.lower() in ['aucune', 'n/a', 'null', 'none']:
            notes = "Aucune note particulière pour cette réservation."
        
        # Créer une zone de texte flexible pour les commentaires
        # Utiliser un style qui permet le retour à la ligne automatique
        notes_style = ParagraphStyle(
            'NotesStyle',
            parent=self.styles['CustomNormal'],
            fontSize=10,
            leading=12,
            alignment=0,  # Alignement à gauche
            spaceAfter=6,
            leftIndent=10,
            rightIndent=10
        )
        
        notes_paragraph = Paragraph(notes, notes_style)
        
        # Créer un tableau simple avec une seule cellule pour les notes
        notes_data = [[notes_paragraph]]
        notes_table = Table(notes_data, colWidths=[16*cm])  # Toute la largeur
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
        line_height = 3*mm  # Espacement entre les lignes
        
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
        c.setFont('Helvetica-Bold', 12)  # Augmenté de 7 à 12
        text = self.company_info['name'][:30]  # Limiter la longueur
        text_width = c.stringWidth(text, 'Helvetica-Bold', 12)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, text)
        y_position -= line_height
        
        # Coordonnées entreprise (police très petite)
        c.setFont('Helvetica', 10)  # Augmenté de 5 à 10
        for info in [self.company_info['phone'], self.company_info['email']]:
            if info:
                info_text = info[:35]  # Limiter la longueur
                text_width = c.stringWidth(info_text, 'Helvetica', 10)
                c.drawString((TICKET_WIDTH - text_width) / 2, y_position, info_text)
                y_position -= 2.5*mm
        
        # Adresse sur une ligne
        if self.company_info['address']:
            address_text = self.company_info['address'][:40]
            text_width = c.stringWidth(address_text, 'Helvetica', 10)
            c.drawString((TICKET_WIDTH - text_width) / 2, y_position, address_text)
            y_position -= 2.5*mm
        
        # RCCM
        if self.company_info['rccm']:
            rccm_text = self.company_info['rccm'][:30]
            text_width = c.stringWidth(rccm_text, 'Helvetica', 10)
            c.drawString((TICKET_WIDTH - text_width) / 2, y_position, rccm_text)
            y_position -= 2.5*mm
        
        # Ligne de séparation
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        # Titre du reçu
        c.setFont('Helvetica-Bold', 14)  # Augmenté de 8 à 14
        title = "RECU DE PAIEMENT"
        text_width = c.stringWidth(title, 'Helvetica-Bold', 14)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, title)
        y_position -= line_height + 2*mm
        
        # Informations de base de la réservation (format compact)
        c.setFont('Helvetica', 10)  # Augmenté de 5 à 10
        
        # Référence
        ref_text = f"Ref: {reservation_data.get('reference', 'N/A')[:15]}"
        c.drawString(2*mm, y_position, ref_text)
        y_position -= 2.5*mm
        
        # Client (limiter la longueur)
        client_name = reservation_data.get('client_nom', 'N/A')[:20]
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
        event_date = reservation_data.get('event_date', 'N/A')[:12]
        date_text = f"Date: {event_date}"
        c.drawString(2*mm, y_position, date_text)
        y_position -= 2.5*mm
        
        # Ligne de séparation
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        # Détail de chaque paiement
        c.setFont('Helvetica-Bold', 11)  # Augmenté de 6 à 11
        c.drawString(2*mm, y_position, "DETAIL PAIEMENTS:")
        y_position -= 3*mm
        
        total_paid = 0
        
        if payments_list:
            for i, payment in enumerate(payments_list, 1):
                payment_amount = payment.get('amount', 0)
                total_paid += payment_amount
                
                # Numéro et montant sur une ligne
                c.setFont('Helvetica-Bold', 10)  # Augmenté de 5 à 10
                currency_symbol = self.get_currency_symbol()
                payment_line = f"#{i}: {payment_amount:.2f} {currency_symbol}"
                c.drawString(2*mm, y_position, payment_line)
                y_position -= 2.5*mm
                
                # Méthode
                c.setFont('Helvetica', 8)  # Augmenté de 4 à 8
                method_text = payment.get('payment_method', 'N/A')[:20]
                c.drawString(3*mm, y_position, method_text)
                y_position -= 2*mm
                
                # Date
                date_text = payment.get('payment_date', 'N/A')[:15]
                c.drawString(3*mm, y_position, date_text)
                y_position -= 2*mm
                
                # Caissier
                cashier_name = payment.get('user_name', 'N/A')[:15]
                cashier_text = f"Par: {cashier_name}"
                c.drawString(3*mm, y_position, cashier_text)
                y_position -= 2*mm
                
                # Petite ligne de séparation entre paiements
                if i < len(payments_list):
                    c.line(3*mm, y_position, TICKET_WIDTH - 3*mm, y_position)
                    y_position -= 2*mm
        else:
            c.setFont('Helvetica', 10)  # Augmenté de 5 à 10
            c.drawString(2*mm, y_position, "Aucun paiement")
            y_position -= 3*mm
        
        # Récapitulatif final
        y_position -= 2*mm
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        c.setFont('Helvetica-Bold', 11)  # Augmenté de 6 à 11
        c.drawString(2*mm, y_position, "RECAPITULATIF:")
        y_position -= 3*mm
        
        c.setFont('Helvetica', 10)  # Augmenté de 5 à 10
        # Utiliser le net à payer (après remise) au lieu du total brut
        net_a_payer = reservation_data.get('total_net', reservation_data.get('net_a_payer', 0))
        balance = net_a_payer - total_paid
        currency_symbol = self.get_currency_symbol()
        
        # Net à payer (après remise)
        total_text = f"Net a payer: {net_a_payer:.2f} {currency_symbol}"
        c.drawString(2*mm, y_position, total_text)
        y_position -= 2.5*mm
        
        # Total payé
        paid_text = f"Paye: {total_paid:.2f} {currency_symbol}"
        c.drawString(2*mm, y_position, paid_text)
        y_position -= 2.5*mm
        
        # Reste à payer
        c.setFont('Helvetica-Bold', 10)  # Augmenté de 5 à 10
        balance_text = f"Reste: {balance:.2f} {currency_symbol}"
        c.drawString(2*mm, y_position, balance_text)
        y_position -= 3*mm
        
        # Ligne de séparation finale
        c.line(2*mm, y_position, TICKET_WIDTH - 2*mm, y_position)
        y_position -= 3*mm
        
        # Filigrane avec nom d'entreprise dynamique
        c.setFont('Helvetica', 8)  # Augmenté de 4 à 8
        generation_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        filigrane_text = f"{self.company_info['name']} (c) {generation_time}"
        text_width = c.stringWidth(filigrane_text, 'Helvetica', 8)
        c.drawString((TICKET_WIDTH - text_width) / 2, y_position, filigrane_text)
        
        # Sauvegarder le PDF
        c.save()
        
        return filename