"""
Utilitaire pour l'export PDF des rapports
Génération de PDF avec en-tête entreprise et contenu formaté
"""

import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt
from PIL import Image as PILImage


class PDFExporter:
    """Classe pour l'export des rapports en PDF format A4"""
    
    def __init__(self):
        self.currency_symbol = "$"  # Fallback par défaut
        try:
            from ayanna_erp.core.entreprise_controller import EntrepriseController
            self.controller = EntrepriseController()
            self.currency_symbol = self.controller.get_currency_symbol()
        except:
            pass
         # Initialiser le contrôleur d'entreprise
        self.entreprise_controller = EntrepriseController() if EntrepriseController else None
        
        # Récupérer les informations de l'entreprise depuis la BDD
        if self.entreprise_controller:
            self.company_info = self.entreprise_controller.get_company_info_for_pdf()
        else:
            # Fallback aux données statiques
            self.company_info = {
                'name': 'AYANNA ERP',
                'address': '123 Avenue de la République',
                'city': 'Kinshasa, RDC',
                'phone': '+243 123 456 789',
                'email': 'contact@ayanna-erp.com',
                'rccm': 'CD/KIN/RCCM/23-B-1234',
                'logo_path': 'assets/logo.png'
            }
        
        # Configuration des styles
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configurer les styles personnalisés"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=HexColor('#2C3E50'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#3498DB'),
            spaceAfter=12,
            spaceBefore=15,
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
        
        # Style pour les statistiques
        self.styles.add(ParagraphStyle(
            name='StatText',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Courier',
            leftIndent=10,
            spaceAfter=4
        ))
    
    def create_header(self, canvas, doc):
        """Créer l'en-tête avec informations entreprise"""
        canvas.saveState()
        
        # FILIGRANE EN BAS - Plus visible
        canvas.setFont('Helvetica-Bold', 11)
        canvas.setFillColor(HexColor('#555555'))  # Gris plus foncé
        generation_time = datetime.now().strftime('%d/%m/%Y à %H:%M')
        filigrane_text = f"Gérée par Ayanna ERP © - Généré le {generation_time}"
        # Position en bas de page - centré
        text_width = canvas.stringWidth(filigrane_text, 'Helvetica-Bold', 11)
        x_center = (A4[0] - text_width) / 2
        canvas.drawString(x_center, 15, filigrane_text)  # 15 points du bas
        
        # Rectangle de fond pour l'en-tête
        canvas.setFillColor(HexColor('#F8F9FA'))
        canvas.rect(0, A4[1] - 120, A4[0], 120, fill=1, stroke=0)
        
        # Ligne de séparation
        canvas.setStrokeColor(HexColor('#3498DB'))
        canvas.setLineWidth(2)
        canvas.line(50, A4[1] - 120, A4[0] - 50, A4[1] - 120)
        
        # Logo (si disponible)
        if self.company_info['logo_path'] and os.path.exists(self.company_info['logo_path']):
            try:
                canvas.drawImage(self.company_info['logo_path'], 50, A4[1] - 110, 
                               width=60, height=60, preserveAspectRatio=True)
            except:
                pass  # Si erreur avec le logo, on continue sans
        
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
    
    def create_footer(self, canvas, doc):
        """Créer le pied de page"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#7F8C8D'))
        
        # Numéro de page - déplacé plus haut pour laisser place au filigrane
        page_num = canvas.getPageNumber()
        page_text = f"Page {page_num}"
        text_width = canvas.stringWidth(page_text, 'Helvetica', 8)
        x_center = (A4[0] - text_width) / 2
        canvas.drawString(x_center, 40, page_text)  # Position plus haute
        
        # Ligne de séparation
        canvas.setStrokeColor(HexColor('#BDC3C7'))
        canvas.setLineWidth(1)
        canvas.line(50, 50, A4[0] - 50, 50)
        
        canvas.restoreState()
    
    def figure_to_image(self, figure):
        """Convertir une figure matplotlib en image pour PDF"""
        # Sauvegarder la figure en mémoire
        img_buffer = io.BytesIO()
        canvas_fig = FigureCanvasAgg(figure)
        
        # Utiliser savefig au lieu de print_png pour plus de compatibilité
        figure.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                      facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        
        # Créer une image ReportLab
        pil_img = PILImage.open(img_buffer)
        
        # Redimensionner pour s'adapter au PDF
        max_width = 450  # Points (environ 16cm)
        max_height = 300  # Points (environ 10cm)
        
        img_width, img_height = pil_img.size
        scale = min(max_width / img_width, max_height / img_height)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Sauvegarder temporairement l'image redimensionnée
        temp_buffer = io.BytesIO()
        pil_img_resized = pil_img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
        pil_img_resized.save(temp_buffer, format='PNG')
        temp_buffer.seek(0)
        
        return Image(temp_buffer, width=new_width * 0.75, height=new_height * 0.75)  # Conversion pixels vers points
    
    def export_monthly_report(self, data, comparison, figure, filename):
        """Exporter le rapport mensuel en PDF"""
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=150, bottomMargin=60)
        story = []
        
        # Titre du rapport
        title = f"Événements du mois - {data['period']}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Graphique
        if figure:
            story.append(Paragraph("Graphique des événements par jour", self.styles['CustomHeading']))
            chart_img = self.figure_to_image(figure)
            story.append(chart_img)
            story.append(Spacer(1, 15))
        
        # Statistiques
        story.append(Paragraph("Résumé mensuel", self.styles['CustomHeading']))
        
        stats_text = f"""
        • Nombre total d'événements: <b>{data['events_count']}</b><br/>
        • Revenus du mois: <b>{data['total_revenue']:.2f} {self.currency_symbol} </b><br/>
        • Total dépenses du mois: <b>{data['total_expenses']:.2f} {self.currency_symbol}</b><br/>
        • Résultat net: <b>{data['net_result']:.2f} {self.currency_symbol}</b><br/>
        • Revenus moyens par événement: <b>{data['average_revenue']:.2f} {self.currency_symbol}</b>
        """
        
        story.append(Paragraph(stats_text, self.styles['CustomNormal']))
        story.append(Spacer(1, 15))
        
        # Comparaison avec mois précédent
        story.append(Paragraph("Comparaison avec le mois précédent", self.styles['CustomHeading']))
        
        comparison_text = f"""
        • Évolution des revenus: <b>{comparison['revenue_evolution']:+.1f}%</b><br/>
        • Évolution du résultat net: <b>{comparison['net_result_evolution']:+.1f}%</b>
        """
        
        story.append(Paragraph(comparison_text, self.styles['CustomNormal']))
        story.append(Spacer(1, 15))
        
        # TOP 5 des services
        story.append(Paragraph("TOP 5 des services", self.styles['CustomHeading']))
        
        if data['top_services']:
            services_data = [['Rang', 'Service', 'Utilisations', 'Total']]
            for i, service in enumerate(data['top_services'], 1):
                services_data.append([
                    str(i),
                    service.name,
                    str(service.count),
                    f"{service.total:.2f} {self.currency_symbol}"
                ])
            
            services_table = Table(services_data, colWidths=[1*cm, 8*cm, 3*cm, 3*cm])
            services_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            story.append(services_table)
        else:
            story.append(Paragraph("Aucun service utilisé ce mois", self.styles['CustomNormal']))
        
        # Construire le PDF avec en-tête et pied de page
        doc.build(story, onFirstPage=self.create_header, onLaterPages=self.create_header)
        
        return filename
    
    def export_yearly_report(self, data, comparison, figure, filename):
        """Exporter le rapport annuel en PDF"""
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=150, bottomMargin=60)
        story = []
        
        # Titre du rapport
        title = f"Événements de l'année - {data['period']}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Graphique
        if figure:
            story.append(Paragraph("Graphique des événements par mois", self.styles['CustomHeading']))
            chart_img = self.figure_to_image(figure)
            story.append(chart_img)
            story.append(Spacer(1, 15))
        
        # Statistiques
        story.append(Paragraph("Résumé annuel", self.styles['CustomHeading']))
        
        stats_text = f"""
        • Nombre total d'événements: <b>{data['events_count']}</b><br/>
        • Revenus de l'année: <b>{data['total_revenue']:.2f} {self.currency_symbol}</b><br/>
        • Total dépenses de l'année: <b>{data['total_expenses']:.2f} {self.currency_symbol}</b><br/>
        • Résultat net: <b>{data['net_result']:.2f} {self.currency_symbol}</b><br/>
        • Revenus moyens par événement: <b>{data['average_revenue']:.2f} {self.currency_symbol}</b>
        """
        
        story.append(Paragraph(stats_text, self.styles['CustomNormal']))
        story.append(Spacer(1, 15))
        
        # Comparaison avec année précédente
        story.append(Paragraph("Comparaison avec l'année précédente", self.styles['CustomHeading']))
        
        comparison_text = f"""
        • Évolution des revenus: <b>{comparison['revenue_evolution']:+.1f}%</b><br/>
        • Évolution du résultat net: <b>{comparison['net_result_evolution']:+.1f}%</b>
        """
        
        story.append(Paragraph(comparison_text, self.styles['CustomNormal']))
        story.append(Spacer(1, 15))
        
        # TOP 5 des services
        story.append(Paragraph("TOP 5 des services de l'année", self.styles['CustomHeading']))
        
        if data['top_services']:
            services_data = [['Rang', 'Service', 'Utilisations', 'Total']]
            for i, service in enumerate(data['top_services'], 1):
                services_data.append([
                    str(i),
                    service.name,
                    str(service.count),
                    f"{service.total:.2f} {self.currency_symbol}"
                ])
            
            services_table = Table(services_data, colWidths=[1*cm, 8*cm, 3*cm, 3*cm])
            services_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#27AE60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            story.append(services_table)
        else:
            story.append(Paragraph("Aucun service utilisé cette année", self.styles['CustomNormal']))
        
        # Construire le PDF
        doc.build(story, onFirstPage=self.create_header, onLaterPages=self.create_header)
        
        return filename
    
    def export_financial_report(self, data, figure, filename):
        """Exporter le rapport financier en PDF"""
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=150, bottomMargin=60)
        story = []
        
        # Titre du rapport
        title = f"Rapport financier - {data['period']}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Graphique
        if figure:
            story.append(Paragraph("Évolution Recettes vs Dépenses", self.styles['CustomHeading']))
            chart_img = self.figure_to_image(figure)
            story.append(chart_img)
            story.append(Spacer(1, 15))
        
        # Résumé financier
        story.append(Paragraph("Résumé financier", self.styles['CustomHeading']))
        
        total_revenue = data['total_revenue']
        total_expenses = data['total_expenses']
        net_result = data['net_result']
        service_revenue = data['service_revenue']
        product_revenue = data['product_revenue']
        
        service_percent = (service_revenue / total_revenue * 100) if total_revenue > 0 else 0
        product_percent = (product_revenue / total_revenue * 100) if total_revenue > 0 else 0
        margin_percent = (net_result / total_revenue * 100) if total_revenue > 0 else 0
        
        financial_text = f"""
        • Total recettes: <b>{total_revenue:.2f} {self.currency_symbol}</b><br/>
        • Total dépenses: <b>{total_expenses:.2f} {self.currency_symbol}</b><br/>
        • Chiffre d'affaires total: <b>{total_revenue:.2f} {self.currency_symbol}</b><br/>
        • Revenus services: <b>{service_revenue:.2f} {self.currency_symbol} ({service_percent:.0f}%)</b><br/>
        • Revenus produits: <b>{product_revenue:.2f} {self.currency_symbol} ({product_percent:.0f}%)</b><br/>
        • Résultat net: <b>{net_result:.2f} {self.currency_symbol}</b><br/>
        • Marge nette: <b>{margin_percent:.1f}%</b>
        """
        
        story.append(Paragraph(financial_text, self.styles['CustomNormal']))
        story.append(Spacer(1, 15))
        
        # Répartition par méthode de paiement
        story.append(Paragraph("Répartition par méthode de paiement", self.styles['CustomHeading']))
        
        if data['payment_methods']:
            payment_data = [['Méthode', 'Montant', 'Pourcentage']]
            for payment_method in data['payment_methods']:
                percent = (payment_method.total / total_revenue * 100) if total_revenue > 0 else 0
                payment_data.append([
                    payment_method.payment_method,
                    f"{payment_method.total:.2f} {self.currency_symbol}",
                    f"{percent:.0f}%"
                ])
            
            payment_table = Table(payment_data, colWidths=[6*cm, 4*cm, 3*cm])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E67E22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            story.append(payment_table)
        else:
            story.append(Paragraph("Aucun paiement enregistré pour cette période", self.styles['CustomNormal']))
        
        story.append(Spacer(1, 15))
        
        # Revenus par type d'événement
        story.append(Paragraph("Revenus par type d'événement", self.styles['CustomHeading']))
        
        if data['revenue_by_type']:
            event_data = [['Type d\'événement', 'Montant', 'Pourcentage']]
            for event_type in data['revenue_by_type']:
                percent = (event_type.total / total_revenue * 100) if total_revenue > 0 else 0
                event_data.append([
                    event_type.event_type,
                    f"{event_type.total:.2f} {self.currency_symbol}",
                    f"{percent:.0f}%"
                ])
            
            event_table = Table(event_data, colWidths=[6*cm, 4*cm, 3*cm])
            event_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#9B59B6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            story.append(event_table)
        else:
            story.append(Paragraph("Aucun événement enregistré pour cette période", self.styles['CustomNormal']))
        
        # Construire le PDF
        doc.build(story, onFirstPage=self.create_header, onLaterPages=self.create_header)
        
        return filename