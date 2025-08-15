"""
Onglet Rapports pour le module Salle de Fête
Génération et affichage des rapports
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView, QDateEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime, timedelta
from ayanna_erp.database.database_manager import DatabaseManager


class RapportIndex(QWidget):
    """Onglet pour la génération et visualisation des rapports"""
    
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Zone de sélection des rapports
        reports_selection_group = QGroupBox("Sélection du rapport")
        selection_layout = QGridLayout(reports_selection_group)
        
        # Différents types de rapports
        self.daily_events_button = QPushButton("📊 Événements du jour")
        self.daily_events_button.setStyleSheet(self.get_button_style("#3498DB"))
        
        self.weekly_events_button = QPushButton("📈 Événements de la semaine")
        self.weekly_events_button.setStyleSheet(self.get_button_style("#27AE60"))
        
        self.monthly_events_button = QPushButton("📉 Événements du mois")
        self.monthly_events_button.setStyleSheet(self.get_button_style("#9B59B6"))
        
        self.revenue_report_button = QPushButton("💰 Rapport de revenus")
        self.revenue_report_button.setStyleSheet(self.get_button_style("#E67E22"))
        
        self.client_report_button = QPushButton("👥 Rapport clients")
        self.client_report_button.setStyleSheet(self.get_button_style("#E74C3C"))
        
        self.product_report_button = QPushButton("📦 Rapport produits")
        self.product_report_button.setStyleSheet(self.get_button_style("#1ABC9C"))
        
        self.service_report_button = QPushButton("🔧 Rapport services")
        self.service_report_button.setStyleSheet(self.get_button_style("#34495E"))
        
        self.financial_summary_button = QPushButton("💼 Résumé financier")
        self.financial_summary_button.setStyleSheet(self.get_button_style("#F39C12"))
        
        # Disposition des boutons
        selection_layout.addWidget(self.daily_events_button, 0, 0)
        selection_layout.addWidget(self.weekly_events_button, 0, 1)
        selection_layout.addWidget(self.monthly_events_button, 0, 2)
        selection_layout.addWidget(self.revenue_report_button, 1, 0)
        selection_layout.addWidget(self.client_report_button, 1, 1)
        selection_layout.addWidget(self.product_report_button, 1, 2)
        selection_layout.addWidget(self.service_report_button, 2, 0)
        selection_layout.addWidget(self.financial_summary_button, 2, 1)
        
        # Zone de filtres personnalisés
        filters_group = QGroupBox("Filtres personnalisés")
        filters_layout = QHBoxLayout(filters_group)
        
        # Filtre par période
        filters_layout.addWidget(QLabel("De:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        filters_layout.addWidget(self.start_date)
        filters_layout.addWidget(QLabel("À:"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        filters_layout.addWidget(self.end_date)
        
        # Bouton de génération personnalisée
        self.generate_custom_button = QPushButton("🔄 Générer rapport personnalisé")
        self.generate_custom_button.setStyleSheet(self.get_button_style("#8E44AD"))
        filters_layout.addWidget(self.generate_custom_button)
        
        filters_layout.addStretch()
        
        # Boutons d'export
        self.export_pdf_button = QPushButton("📄 Exporter PDF")
        self.export_pdf_button.setStyleSheet(self.get_button_style("#C0392B"))
        
        self.export_excel_button = QPushButton("📊 Exporter Excel")
        self.export_excel_button.setStyleSheet(self.get_button_style("#27AE60"))
        
        filters_layout.addWidget(self.export_pdf_button)
        filters_layout.addWidget(self.export_excel_button)
        
        # Zone d'affichage des rapports
        display_group = QGroupBox("Résultat du rapport")
        display_layout = QVBoxLayout(display_group)
        
        # En-tête du rapport
        header_layout = QHBoxLayout()
        self.report_title = QLabel("Sélectionnez un type de rapport")
        self.report_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.report_title.setStyleSheet("color: #2C3E50; padding: 10px;")
        
        self.report_date = QLabel(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        self.report_date.setStyleSheet("color: #7F8C8D; padding: 10px;")
        
        header_layout.addWidget(self.report_title)
        header_layout.addStretch()
        header_layout.addWidget(self.report_date)
        
        # Zone de contenu du rapport
        self.reports_display = QTextEdit()
        self.reports_display.setReadOnly(True)
        self.reports_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
                padding: 15px;
                font-family: 'Courier New';
                font-size: 12px;
            }
        """)
        
        display_layout.addLayout(header_layout)
        display_layout.addWidget(self.reports_display)
        
        # Assemblage du layout principal
        layout.addWidget(reports_selection_group)
        layout.addWidget(filters_group)
        layout.addWidget(display_group)
        
        # Connexion des signaux
        self.daily_events_button.clicked.connect(lambda: self.generate_report("daily_events"))
        self.weekly_events_button.clicked.connect(lambda: self.generate_report("weekly_events"))
        self.monthly_events_button.clicked.connect(lambda: self.generate_report("monthly_events"))
        self.revenue_report_button.clicked.connect(lambda: self.generate_report("revenue"))
        self.client_report_button.clicked.connect(lambda: self.generate_report("clients"))
        self.product_report_button.clicked.connect(lambda: self.generate_report("products"))
        self.service_report_button.clicked.connect(lambda: self.generate_report("services"))
        self.financial_summary_button.clicked.connect(lambda: self.generate_report("financial"))
        self.generate_custom_button.clicked.connect(lambda: self.generate_report("custom"))
        
        # Affichage du rapport par défaut
        self.generate_report("daily_events")
    
    def get_button_style(self, color):
        """Obtenir le style CSS pour les boutons"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {color}AA;
                transform: translateY(-2px);
            }}
            QPushButton:pressed {{
                background-color: {color}CC;
            }}
        """
    
    def generate_report(self, report_type):
        """Générer un rapport selon le type demandé"""
        self.report_date.setText(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        
        if report_type == "daily_events":
            self.generate_daily_events_report()
        elif report_type == "weekly_events":
            self.generate_weekly_events_report()
        elif report_type == "monthly_events":
            self.generate_monthly_events_report()
        elif report_type == "revenue":
            self.generate_revenue_report()
        elif report_type == "clients":
            self.generate_client_report()
        elif report_type == "products":
            self.generate_product_report()
        elif report_type == "services":
            self.generate_service_report()
        elif report_type == "financial":
            self.generate_financial_summary()
        elif report_type == "custom":
            self.generate_custom_report()
    
    def generate_daily_events_report(self):
        """Générer le rapport des événements du jour"""
        self.report_title.setText("📊 Rapport des événements du jour")
        
        report_content = f"""
=== RAPPORT DES ÉVÉNEMENTS DU JOUR ===
Date: {datetime.now().strftime('%d/%m/%Y')}

RÉSUMÉ:
• Nombre d'événements: 3
• Revenus du jour: 2,150.00 €
• Nouveaux clients: 2
• Événements confirmés: 2
• Événements en attente: 1

DÉTAIL DES ÉVÉNEMENTS:
┌─────────────────────────────────────────────────────────────────┐
│ 14:00 - Baptême Moreau                                         │
│ Client: Jean Moreau                                             │
│ Services: Décoration florale, Buffet (50 pers.)                │
│ Montant: 1,250.00 €                                           │
│ Statut: Confirmé ✓                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 18:00 - Anniversaire Bernard                                   │
│ Client: Sophie Bernard                                          │
│ Services: DJ, Animation enfants                                 │
│ Montant: 600.00 €                                             │
│ Statut: Confirmé ✓                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 20:00 - Cocktail Entreprise ABC                                │
│ Client: Directeur ABC Corp                                      │
│ Services: Cocktail, Service traiteur                           │
│ Montant: 300.00 €                                             │
│ Statut: En attente ⏳                                           │
└─────────────────────────────────────────────────────────────────┘

SERVICES LES PLUS DEMANDÉS:
1. Décoration florale (2 fois)
2. Service traiteur (3 fois)
3. Animation (1 fois)

RECOMMANDATIONS:
• Contacter le client ABC Corp pour confirmer la réservation
• Prévoir stock supplémentaire pour les fleurs (forte demande)
• Vérifier la disponibilité du matériel de sonorisation
        """
        
        self.reports_display.setPlainText(report_content.strip())
    
    def generate_weekly_events_report(self):
        """Générer le rapport des événements de la semaine"""
        self.report_title.setText("📈 Rapport des événements de la semaine")
        
        report_content = f"""
=== RAPPORT DES ÉVÉNEMENTS DE LA SEMAINE ===
Période: {(datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y')} - {datetime.now().strftime('%d/%m/%Y')}

RÉSUMÉ HEBDOMADAIRE:
• Nombre total d'événements: 12
• Revenus de la semaine: 15,750.00 €
• Nouveaux clients: 8
• Taux d'occupation: 85%
• Événements annulés: 1

RÉPARTITION PAR JOUR:
┌─────────────┬──────────────┬─────────────┬──────────────┐
│ Jour        │ Événements   │ Revenus     │ Taux occup.  │
├─────────────┼──────────────┼─────────────┼──────────────┤
│ Lundi       │ 1           │ 800.00 €    │ 30%          │
│ Mardi       │ 2           │ 1,500.00 €  │ 60%          │
│ Mercredi    │ 1           │ 1,200.00 €  │ 40%          │
│ Jeudi       │ 2           │ 2,100.00 €  │ 70%          │
│ Vendredi    │ 3           │ 4,200.00 €  │ 90%          │
│ Samedi      │ 2           │ 4,800.00 €  │ 100%         │
│ Dimanche    │ 1           │ 1,150.00 €  │ 50%          │
└─────────────┴──────────────┴─────────────┴──────────────┘

TYPES D'ÉVÉNEMENTS:
• Mariages: 4 (33%) - 8,500.00 €
• Anniversaires: 3 (25%) - 2,800.00 €
• Baptêmes: 2 (17%) - 2,200.00 €
• Événements d'entreprise: 2 (17%) - 1,750.00 €
• Autres: 1 (8%) - 500.00 €

ANALYSE DES TENDANCES:
• Week-end très demandé (100% d'occupation samedi)
• Mariages génèrent 54% du chiffre d'affaires
• Croissance de 15% par rapport à la semaine précédente
        """
        
        self.reports_display.setPlainText(report_content.strip())
    
    def generate_monthly_events_report(self):
        """Générer le rapport des événements du mois"""
        self.report_title.setText("📉 Rapport des événements du mois")
        
        report_content = f"""
=== RAPPORT DES ÉVÉNEMENTS DU MOIS ===
Mois: Août 2025

RÉSUMÉ MENSUEL:
• Nombre total d'événements: 48
• Revenus du mois: 62,300.00 €
• Revenus moyens par événement: 1,297.92 €
• Nouveaux clients: 28
• Clients fidèles: 20
• Taux de satisfaction: 96%

ÉVOLUTION PAR SEMAINE:
Semaine 1: 11 événements - 14,200.00 €
Semaine 2: 13 événements - 16,800.00 €
Semaine 3: 12 événements - 15,750.00 €
Semaine 4: 12 événements - 15,550.00 €

TOP 5 DES SERVICES:
1. Service traiteur: 35 utilisations - 26,250.00 €
2. Décoration florale: 28 utilisations - 12,600.00 €
3. DJ et sonorisation: 22 utilisations - 8,800.00 €
4. Animation enfants: 15 utilisations - 4,500.00 €
5. Photobooth: 12 utilisations - 2,400.00 €

CLIENTS LES PLUS ACTIFS:
1. Entreprise XYZ Corp (3 événements)
2. Famille Martin (2 événements)
3. Association locale (2 événements)

OBJECTIFS DU MOIS:
✓ Atteindre 45 événements (48 réalisés)
✓ Générer 60,000€ de revenus (62,300€ réalisés)
✓ Maintenir 95% de satisfaction (96% réalisé)
        """
        
        self.reports_display.setPlainText(report_content.strip())
    
    def generate_revenue_report(self):
        """Générer le rapport de revenus"""
        self.report_title.setText("💰 Rapport de revenus")
        
        report_content = f"""
=== RAPPORT DE REVENUS DÉTAILLÉ ===
Période d'analyse: {datetime.now().strftime('%d/%m/%Y')}

RÉSUMÉ FINANCIER:
• Chiffre d'affaires total: 62,300.00 €
• Revenus services: 45,200.00 € (73%)
• Revenus produits: 17,100.00 € (27%)
• Marge brute: 38,650.00 € (62%)

RÉPARTITION PAR MÉTHODE DE PAIEMENT:
┌─────────────────┬─────────────┬─────────────┐
│ Méthode         │ Montant     │ %           │
├─────────────────┼─────────────┼─────────────┤
│ Virement       │ 32,500.00 € │ 52%         │
│ Carte bancaire  │ 18,200.00 € │ 29%         │
│ Espèces        │ 8,100.00 €  │ 13%         │
│ Chèque         │ 3,500.00 €  │ 6%          │
└─────────────────┴─────────────┴─────────────┘

REVENUS PAR TYPE D'ÉVÉNEMENT:
• Mariages: 28,500.00 € (46%)
• Événements d'entreprise: 15,200.00 € (24%)
• Anniversaires: 12,800.00 € (21%)
• Baptêmes: 5,800.00 € (9%)

ANALYSE DES COÛTS:
• Coût des marchandises vendues: 23,650.00 €
• Charges fixes: 8,500.00 €
• Charges variables: 6,200.00 €
• Résultat net: 23,950.00 €

INDICATEURS CLÉS:
• Panier moyen: 1,297.92 €
• Marge nette: 38.4%
• ROI mensuel: 45.2%
• Croissance vs mois précédent: +12.5%

PRÉVISIONS:
• Objectif mois prochain: 68,000.00 €
• Croissance prévue: +9.1%
        """
        
        self.reports_display.setPlainText(report_content.strip())
    
    def generate_client_report(self):
        """Générer le rapport clients"""
        self.report_title.setText("👥 Rapport clients")
        
        report_content = f"""
=== RAPPORT CLIENTS ===
Date d'analyse: {datetime.now().strftime('%d/%m/%Y')}

STATISTIQUES GÉNÉRALES:
• Total clients actifs: 142
• Nouveaux clients ce mois: 28
• Clients fidèles (2+ événements): 45
• Taux de rétention: 68%
• Note de satisfaction moyenne: 4.8/5

TOP 10 CLIENTS (par chiffre d'affaires):
┌─────────────────────┬──────────────┬─────────────┐
│ Client              │ Événements  │ CA total    │
├─────────────────────┼──────────────┼─────────────┤
│ Entreprise XYZ      │ 5           │ 8,500.00 €  │
│ Famille Martin      │ 3           │ 6,200.00 €  │
│ Sophie Dubois       │ 2           │ 4,800.00 €  │
│ Mairie de Ville     │ 4           │ 4,200.00 €  │
│ Association Locale  │ 3           │ 3,900.00 €  │
│ Jean Moreau         │ 2           │ 3,500.00 €  │
│ Claire Bernard      │ 2           │ 3,200.00 €  │
│ Pierre Durand       │ 1           │ 2,800.00 €  │
│ Marie Leroy         │ 1           │ 2,500.00 €  │
│ Paul Petit          │ 1           │ 2,200.00 €  │
└─────────────────────┴──────────────┴─────────────┘

SEGMENTATION CLIENTS:
• Particuliers: 95 clients (67%)
• Entreprises: 28 clients (20%)
• Associations: 19 clients (13%)

ANALYSE GÉOGRAPHIQUE:
• Local (< 20km): 78%
• Régional (20-50km): 15%
• National (> 50km): 7%

CANAUX D'ACQUISITION:
• Bouche à oreille: 45%
• Site internet: 28%
• Réseaux sociaux: 15%
• Publicité locale: 8%
• Autres: 4%

RECOMMANDATIONS:
• Programme de fidélité pour clients réguliers
• Campagne de référencement pour nouveaux clients
• Enquête de satisfaction trimestrielle
        """
        
        self.reports_display.setPlainText(report_content.strip())
    
    def generate_product_report(self):
        """Générer le rapport produits"""
        self.report_title.setText("📦 Rapport produits")
        
        report_content = f"""
=== RAPPORT PRODUITS ET STOCK ===
Date d'analyse: {datetime.now().strftime('%d/%m/%Y')}

ÉTAT DU STOCK:
• Nombre total de produits: 156
• Valeur totale du stock: 15,680.00 €
• Produits en rupture: 3
• Produits en stock faible: 12
• Rotation moyenne: 2.3 fois/mois

PRODUITS LES PLUS VENDUS:
┌─────────────────────┬─────────────┬─────────────┬─────────────┐
│ Produit             │ Qté vendue  │ CA généré   │ Marge       │
├─────────────────────┼─────────────┼─────────────┼─────────────┤
│ Champagne Premium   │ 48         │ 2,160.00 €  │ 35%         │
│ Petits fours        │ 35         │ 420.00 €    │ 60%         │
│ Nappes blanches     │ 25         │ 375.00 €    │ 45%         │
│ Assiettes jetables  │ 60         │ 480.00 €    │ 55%         │
│ Vin rouge Bordeaux  │ 28         │ 700.00 €    │ 40%         │
└─────────────────────┴─────────────┴─────────────┴─────────────┘

ALERTES STOCK:
⚠️ RUPTURE DE STOCK:
• Bouquets de roses (0 unités)
• Bougies parfumées (0 unités)
• Centres de table dorés (0 unités)

⚡ STOCK FAIBLE:
• Petits fours assortis (5/20)
• Serviettes colorées (8/30)
• Verres à champagne (15/50)

MOUVEMENTS DU MOIS:
• Entrées: 245 produits
• Sorties: 312 produits
• Pertes/casse: 8 produits
• Ajustements: +3 produits

ANALYSE DE RENTABILITÉ:
• Marge brute moyenne: 47%
• Produits les plus rentables: Petits fours (60%)
• Produits les moins rentables: Champagne (35%)

RECOMMANDATIONS:
• Réapprovisionner d'urgence les produits en rupture
• Négocier meilleurs prix avec fournisseurs champagne
• Optimiser rotation des produits saisonniers
        """
        
        self.reports_display.setPlainText(report_content.strip())
    
    def generate_service_report(self):
        """Générer le rapport services"""
        self.report_title.setText("🔧 Rapport services")
        
        report_content = f"""
=== RAPPORT SERVICES ===
Date d'analyse: {datetime.now().strftime('%d/%m/%Y')}

SERVICES DISPONIBLES: 24
Services actifs: 22
Services temporairement indisponibles: 2

SERVICES LES PLUS DEMANDÉS:
┌─────────────────────┬─────────────┬─────────────┬─────────────┐
│ Service             │ Utilisation │ CA généré   │ Marge       │
├─────────────────────┼─────────────┼─────────────┼─────────────┤
│ Service traiteur    │ 35 fois     │ 26,250.00 € │ 45%         │
│ Décoration florale  │ 28 fois     │ 12,600.00 € │ 55%         │
│ DJ et sonorisation  │ 22 fois     │ 8,800.00 €  │ 65%         │
│ Animation enfants   │ 15 fois     │ 4,500.00 €  │ 70%         │
│ Photobooth         │ 12 fois     │ 2,400.00 €  │ 80%         │
│ Service nettoyage   │ 48 fois     │ 4,800.00 €  │ 60%         │
└─────────────────────┴─────────────┴─────────────┴─────────────┘

SERVICES PAR CATÉGORIE:
• Restauration: 8 services (58% du CA)
• Décoration: 6 services (22% du CA)
• Animation: 4 services (12% du CA)
• Logistique: 6 services (8% du CA)

SATISFACTION CLIENTS:
• Service traiteur: 4.9/5 ⭐⭐⭐⭐⭐
• DJ et sonorisation: 4.8/5 ⭐⭐⭐⭐⭐
• Décoration florale: 4.7/5 ⭐⭐⭐⭐⭐
• Animation enfants: 4.9/5 ⭐⭐⭐⭐⭐

SERVICES INDISPONIBLES:
• Photographie (équipement en maintenance)
• Château gonflable (réparation en cours)

PARTENAIRES EXTERNES:
• Traiteurs: 3 partenaires actifs
• Fleuristes: 2 partenaires
• DJ/Musiciens: 5 prestataires
• Animateurs: 4 freelances

RECOMMANDATIONS:
• Développer l'offre de services haut de gamme
• Former équipe interne pour réduire coûts externes
• Négocier tarifs préférentiels avec partenaires
        """
        
        self.reports_display.setPlainText(report_content.strip())
    
    def generate_financial_summary(self):
        """Générer le résumé financier"""
        self.report_title.setText("💼 Résumé financier complet")
        
        report_content = f"""
=== RÉSUMÉ FINANCIER COMPLET ===
Période: Août 2025

💰 CHIFFRE D'AFFAIRES:
• CA total: 62,300.00 €
• Objectif mensuel: 60,000.00 €
• Performance: +3.8% vs objectif
• Croissance vs mois précédent: +12.5%

📊 RÉPARTITION DES REVENUS:
• Services: 45,200.00 € (73%)
• Produits: 17,100.00 € (27%)
• Location salle: 0.00 € (inclus dans services)

💳 ENCAISSEMENTS:
• Encaissé ce mois: 58,450.00 €
• En attente: 3,850.00 €
• Taux d'encaissement: 93.8%

💸 CHARGES:
• Coût des marchandises: 23,650.00 €
• Salaires: 12,500.00 €
• Charges sociales: 3,750.00 €
• Fournitures: 2,200.00 €
• Électricité/Eau: 800.00 €
• Assurances: 450.00 €
• Maintenance: 650.00 €
• Marketing: 300.00 €
• Autres: 400.00 €
TOTAL CHARGES: 44,700.00 €

📈 RÉSULTATS:
• Marge brute: 38,650.00 €
• Taux de marge brute: 62.0%
• Résultat d'exploitation: 17,600.00 €
• Taux de résultat: 28.2%

🎯 INDICATEURS CLÉS:
• Panier moyen: 1,297.92 €
• Nombre de clients: 48
• CA par client: 1,297.92 €
• ROI mensuel: 28.2%

📅 PRÉVISIONS SEPTEMBRE:
• CA prévisionnel: 68,000.00 €
• Croissance attendue: +9.1%
• Nouveaux événements prévus: 52
• Investissements prévus: 5,000.00 €

⚠️ POINTS D'ATTENTION:
• 3,850.00 € en attente d'encaissement
• Stock faible sur plusieurs produits
• Besoin de recrutement saisonnier
        """
        
        self.reports_display.setPlainText(report_content.strip())
    
    def generate_custom_report(self):
        """Générer un rapport personnalisé selon les filtres"""
        self.report_title.setText("🔄 Rapport personnalisé")
        
        start_date = self.start_date.date().toString("dd/MM/yyyy")
        end_date = self.end_date.date().toString("dd/MM/yyyy")
        
        report_content = f"""
=== RAPPORT PERSONNALISÉ ===
Période sélectionnée: {start_date} - {end_date}

Ce rapport sera généré selon vos critères personnalisés...

[Ici seront affichées les données filtrées selon la période sélectionnée]

FONCTIONNALITÉS À IMPLÉMENTER:
• Filtrage par date de début/fin
• Intégration avec la base de données
• Calculs dynamiques selon la période
• Export en PDF et Excel
• Graphiques et visualisations

Pour l'instant, ce rapport utilise des données de démonstration.
        """
        
        self.reports_display.setPlainText(report_content.strip())
