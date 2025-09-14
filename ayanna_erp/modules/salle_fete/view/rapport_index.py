"""
Onglet Rapports pour le module Salle de Fête
Interface redesignée avec dashboards intuitifs
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView, QDateEdit, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

try:
    from ayanna_erp.modules.salle_fete.controller.rapport_controller import RapportController
except ImportError:
    from ..controller.rapport_controller import RapportController


class RapportIndex(QWidget):
    """Onglet pour la génération et visualisation des rapports avec dashboards intuitifs"""
    
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.rapport_controller = RapportController()
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur avec onglets"""
        layout = QVBoxLayout(self)
        
        # Titre principal
        title_label = QLabel("📊 RAPPORTS SALLE DE FÊTE")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3498DB, stop:1 #2980B9);
                color: white;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Création des onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ECF0F1, stop:1 #BDC3C7);
                border: 1px solid #95A5A6;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498DB, stop:1 #2980B9);
                color: white;
                border-bottom: none;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)
        
        # Onglet 1: Événements du mois
        self.monthly_tab = self.create_monthly_events_tab()
        self.tab_widget.addTab(self.monthly_tab, "📅 Événements du mois")
        
        # Onglet 2: Événements de l'année
        self.yearly_tab = self.create_yearly_events_tab()
        self.tab_widget.addTab(self.yearly_tab, "📊 Événements de l'année")
        
        # Onglet 3: Rapport financier
        self.financial_tab = self.create_financial_report_tab()
        self.tab_widget.addTab(self.financial_tab, "💰 Rapport financier")
        
        layout.addWidget(self.tab_widget)
        
        # Connexions des onglets
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Charger les données par défaut
        self.load_monthly_data()
    
    def create_monthly_events_tab(self):
        """Créer l'onglet des événements du mois"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Zone de filtres
        filter_group = QGroupBox("🔍 Filtres")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Mois:"))
        self.month_combo = QComboBox()
        months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                 "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        self.month_combo.addItems(months)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        
        filter_layout.addWidget(QLabel("Année:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(datetime.now().year)
        
        self.update_monthly_btn = QPushButton("🔄 Actualiser")
        self.update_monthly_btn.setStyleSheet(self.get_button_style("#3498DB"))
        
        filter_layout.addWidget(self.month_combo)
        filter_layout.addWidget(self.year_spin)
        filter_layout.addWidget(self.update_monthly_btn)
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # Zone du graphique et statistiques
        content_layout = QHBoxLayout()
        
        # Graphique (à gauche)
        chart_group = QGroupBox("📊 Événements par jour")
        chart_layout = QVBoxLayout(chart_group)
        
        self.monthly_figure = Figure(figsize=(10, 6))
        self.monthly_canvas = FigureCanvas(self.monthly_figure)
        chart_layout.addWidget(self.monthly_canvas)
        
        content_layout.addWidget(chart_group, 2)
        
        # Statistiques (à droite)
        stats_group = QGroupBox("📈 Statistiques mensuelles")
        stats_layout = QVBoxLayout(stats_group)
        
        self.monthly_stats_text = QTextEdit()
        self.monthly_stats_text.setReadOnly(True)
        self.monthly_stats_text.setMaximumWidth(400)
        self.monthly_stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 5px;
                padding: 15px;
                font-family: 'Segoe UI', Arial;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        stats_layout.addWidget(self.monthly_stats_text)
        
        content_layout.addWidget(stats_group, 1)
        layout.addLayout(content_layout)
        
        # Connexions
        self.update_monthly_btn.clicked.connect(self.load_monthly_data)
        self.month_combo.currentIndexChanged.connect(self.load_monthly_data)
        self.year_spin.valueChanged.connect(self.load_monthly_data)
        
        return tab
    
    def create_yearly_events_tab(self):
        """Créer l'onglet des événements de l'année"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Zone de filtres
        filter_group = QGroupBox("🔍 Filtres")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Année:"))
        self.yearly_year_spin = QSpinBox()
        self.yearly_year_spin.setRange(2020, 2030)
        self.yearly_year_spin.setValue(datetime.now().year)
        
        self.update_yearly_btn = QPushButton("🔄 Actualiser")
        self.update_yearly_btn.setStyleSheet(self.get_button_style("#27AE60"))
        
        filter_layout.addWidget(self.yearly_year_spin)
        filter_layout.addWidget(self.update_yearly_btn)
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # Zone du graphique et statistiques
        content_layout = QHBoxLayout()
        
        # Graphique (à gauche)
        chart_group = QGroupBox("📊 Événements par mois")
        chart_layout = QVBoxLayout(chart_group)
        
        self.yearly_figure = Figure(figsize=(12, 6))
        self.yearly_canvas = FigureCanvas(self.yearly_figure)
        chart_layout.addWidget(self.yearly_canvas)
        
        content_layout.addWidget(chart_group, 2)
        
        # Statistiques (à droite)
        stats_group = QGroupBox("📈 Statistiques annuelles")
        stats_layout = QVBoxLayout(stats_group)
        
        self.yearly_stats_text = QTextEdit()
        self.yearly_stats_text.setReadOnly(True)
        self.yearly_stats_text.setMaximumWidth(400)
        self.yearly_stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 5px;
                padding: 15px;
                font-family: 'Segoe UI', Arial;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        stats_layout.addWidget(self.yearly_stats_text)
        
        content_layout.addWidget(stats_group, 1)
        layout.addLayout(content_layout)
        
        # Connexions
        self.update_yearly_btn.clicked.connect(self.load_yearly_data)
        self.yearly_year_spin.valueChanged.connect(self.load_yearly_data)
        
        return tab
    
    def create_financial_report_tab(self):
        """Créer l'onglet du rapport financier"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Zone de filtres
        filter_group = QGroupBox("🔍 Période d'analyse")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Du:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        
        filter_layout.addWidget(QLabel("Au:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        
        self.update_financial_btn = QPushButton("🔄 Actualiser")
        self.update_financial_btn.setStyleSheet(self.get_button_style("#E67E22"))
        
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addWidget(self.end_date_edit)
        filter_layout.addWidget(self.update_financial_btn)
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # Zone du graphique et analyses
        content_layout = QHBoxLayout()
        
        # Graphique (à gauche)
        chart_group = QGroupBox("📈 Évolution Recettes vs Dépenses")
        chart_layout = QVBoxLayout(chart_group)
        
        self.financial_figure = Figure(figsize=(12, 6))
        self.financial_canvas = FigureCanvas(self.financial_figure)
        chart_layout.addWidget(self.financial_canvas)
        
        content_layout.addWidget(chart_group, 2)
        
        # Analyses financières (à droite)
        analysis_group = QGroupBox("💼 Analyses financières")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.financial_stats_text = QTextEdit()
        self.financial_stats_text.setReadOnly(True)
        self.financial_stats_text.setMaximumWidth(450)
        self.financial_stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 5px;
                padding: 15px;
                font-family: 'Segoe UI', Arial;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        analysis_layout.addWidget(self.financial_stats_text)
        
        content_layout.addWidget(analysis_group, 1)
        layout.addLayout(content_layout)
        
        # Connexions
        self.update_financial_btn.clicked.connect(self.load_financial_data)
        self.start_date_edit.dateChanged.connect(self.load_financial_data)
        self.end_date_edit.dateChanged.connect(self.load_financial_data)
        
        return tab
    
    def load_monthly_data(self):
        """Charger les données mensuelles"""
        try:
            month = self.month_combo.currentIndex() + 1
            year = self.year_spin.value()
            
            # Récupérer les données
            data = self.rapport_controller.get_monthly_events_data(year, month)
            comparison = self.rapport_controller.get_comparison_data(year, month)
            
            # Mettre à jour le graphique
            self.update_monthly_chart(data)
            
            # Mettre à jour les statistiques
            self.update_monthly_stats(data, comparison)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des données: {str(e)}")
    
    def load_yearly_data(self):
        """Charger les données annuelles"""
        try:
            year = self.yearly_year_spin.value()
            
            # Récupérer les données
            data = self.rapport_controller.get_yearly_events_data(year)
            prev_year_data = self.rapport_controller.get_yearly_events_data(year - 1)
            
            # Calculer les comparaisons
            comparison = {
                'revenue_evolution': 0,
                'net_result_evolution': 0
            }
            
            if prev_year_data['total_revenue'] > 0:
                comparison['revenue_evolution'] = ((data['total_revenue'] - prev_year_data['total_revenue']) / prev_year_data['total_revenue']) * 100
            
            if prev_year_data['net_result'] != 0:
                comparison['net_result_evolution'] = ((data['net_result'] - prev_year_data['net_result']) / abs(prev_year_data['net_result'])) * 100
            
            # Mettre à jour le graphique
            self.update_yearly_chart(data)
            
            # Mettre à jour les statistiques
            self.update_yearly_stats(data, comparison)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des données: {str(e)}")
    
    def load_financial_data(self):
        """Charger les données financières"""
        try:
            # Convertir QDate en date Python
            start_qdate = self.start_date_edit.date()
            end_qdate = self.end_date_edit.date()
            
            # Méthode compatible PyQt6
            start_date = date(start_qdate.year(), start_qdate.month(), start_qdate.day())
            end_date = date(end_qdate.year(), end_qdate.month(), end_qdate.day())
            
            # Convertir en datetime
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Récupérer les données
            data = self.rapport_controller.get_financial_report_data(start_datetime, end_datetime)
            
            # Mettre à jour le graphique
            self.update_financial_chart(data)
            
            # Mettre à jour les analyses
            self.update_financial_stats(data)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des données: {str(e)}")
    
    def update_monthly_chart(self, data):
        """Mettre à jour le graphique mensuel"""
        self.monthly_figure.clear()
        ax = self.monthly_figure.add_subplot(111)
        
        # Données pour le graphique
        days = list(data['events_by_day'].keys())
        counts = list(data['events_by_day'].values())
        
        # Création du graphique en barres
        bars = ax.bar(days, counts, color='#3498DB', alpha=0.8, edgecolor='#2980B9', linewidth=1)
        
        # Personnalisation
        ax.set_xlabel('Jour du mois', fontsize=10, fontweight='bold')
        ax.set_ylabel('Nombre d\'événements', fontsize=10, fontweight='bold')
        ax.set_title(f'Répartition des événements - {data["period"]}', fontsize=12, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Ajout des valeurs sur les barres
        for bar, count in zip(bars, counts):
            if count > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{int(count)}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Mise en forme
        ax.set_xlim(0.5, len(days) + 0.5)
        self.monthly_figure.tight_layout()
        self.monthly_canvas.draw()
    
    def update_yearly_chart(self, data):
        """Mettre à jour le graphique annuel"""
        self.yearly_figure.clear()
        ax = self.yearly_figure.add_subplot(111)
        
        # Données pour le graphique
        months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        counts = [data['events_by_month'][i] for i in range(1, 13)]
        
        # Création du graphique en barres
        bars = ax.bar(months, counts, color='#27AE60', alpha=0.8, edgecolor='#229954', linewidth=1)
        
        # Personnalisation
        ax.set_xlabel('Mois', fontsize=10, fontweight='bold')
        ax.set_ylabel('Nombre d\'événements', fontsize=10, fontweight='bold')
        ax.set_title(f'Répartition des événements - {data["period"]}', fontsize=12, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Ajout des valeurs sur les barres
        for bar, count in zip(bars, counts):
            if count > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{int(count)}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Rotation des labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        self.yearly_figure.tight_layout()
        self.yearly_canvas.draw()
    
    def update_financial_chart(self, data):
        """Mettre à jour le graphique financier avec courbes"""
        self.financial_figure.clear()
        ax = self.financial_figure.add_subplot(111)
        
        # Données pour le graphique
        daily_data = data['daily_data']
        dates = [datetime.strptime(d, '%Y-%m-%d') for d in daily_data['dates']]
        revenues = daily_data['revenues']
        expenses = daily_data['expenses']
        
        # Création des courbes
        ax.plot(dates, revenues, color='#27AE60', linewidth=2, marker='o', 
               markersize=4, label='Recettes', alpha=0.8)
        ax.plot(dates, expenses, color='#E74C3C', linewidth=2, marker='s', 
               markersize=4, label='Dépenses', alpha=0.8)
        
        # Remplissage sous les courbes
        ax.fill_between(dates, revenues, alpha=0.2, color='#27AE60')
        ax.fill_between(dates, expenses, alpha=0.2, color='#E74C3C')
        
        # Personnalisation
        ax.set_xlabel('Date', fontsize=10, fontweight='bold')
        ax.set_ylabel('Montant (€)', fontsize=10, fontweight='bold')
        ax.set_title(f'Évolution Recettes vs Dépenses - {data["period"]}', fontsize=12, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
        
        # Format des dates sur l'axe x
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        self.financial_figure.tight_layout()
        self.financial_canvas.draw()
    
    def update_monthly_stats(self, data, comparison):
        """Mettre à jour les statistiques mensuelles"""
        # Préparation du texte
        stats_text = f"""=== RAPPORT DES ÉVÉNEMENTS DU MOIS ===
Mois: {data['period']}

RÉSUMÉ MENSUEL:
• Nombre total d'événements: {data['events_count']}
• Revenus du mois: {data['total_revenue']:.2f} €
• Total dépenses du mois: {data['total_expenses']:.2f} €
• Résultat net: {data['net_result']:.2f} €
• Revenus moyens par événement: {data['average_revenue']:.2f} €

COMPARAISON AVEC LE MOIS PRÉCÉDENT:
• Évolution des revenus: {comparison['revenue_evolution']:+.1f}%
• Évolution du résultat net: {comparison['net_result_evolution']:+.1f}%

TOP 5 DES SERVICES:"""
        
        for i, service in enumerate(data['top_services'], 1):
            stats_text += f"\n{i}. {service.name}: {service.count} utilisations - {service.total:.2f} €"
        
        if not data['top_services']:
            stats_text += "\nAucun service utilisé ce mois"
        
        self.monthly_stats_text.setPlainText(stats_text)
    
    def update_yearly_stats(self, data, comparison):
        """Mettre à jour les statistiques annuelles"""
        stats_text = f"""=== RAPPORT DES ÉVÉNEMENTS DE L'ANNÉE ===
Année: {data['period']}

RÉSUMÉ ANNUEL:
• Nombre total d'événements: {data['events_count']}
• Revenus de l'année: {data['total_revenue']:.2f} €
• Total dépenses de l'année: {data['total_expenses']:.2f} €
• Résultat net: {data['net_result']:.2f} €
• Revenus moyens par événement: {data['average_revenue']:.2f} €

COMPARAISON AVEC L'ANNÉE PRÉCÉDENTE:
• Évolution des revenus: {comparison['revenue_evolution']:+.1f}%
• Évolution du résultat net: {comparison['net_result_evolution']:+.1f}%

TOP 5 DES SERVICES:"""
        
        for i, service in enumerate(data['top_services'], 1):
            stats_text += f"\n{i}. {service.name}: {service.count} utilisations - {service.total:.2f} €"
        
        if not data['top_services']:
            stats_text += "\nAucun service utilisé cette année"
        
        self.yearly_stats_text.setPlainText(stats_text)
    
    def update_financial_stats(self, data):
        """Mettre à jour les analyses financières"""
        # Calculs pour les analyses
        total_revenue = data['total_revenue']
        total_expenses = data['total_expenses']
        net_result = data['net_result']
        service_revenue = data['service_revenue']
        product_revenue = data['product_revenue']
        
        # Pourcentages
        service_percent = (service_revenue / total_revenue * 100) if total_revenue > 0 else 0
        product_percent = (product_revenue / total_revenue * 100) if total_revenue > 0 else 0
        margin_percent = (net_result / total_revenue * 100) if total_revenue > 0 else 0
        
        # Nombre d'événements pour le panier moyen
        total_events = len([pm for pm in data['payment_methods']])
        average_basket = total_revenue / total_events if total_events > 0 else 0
        
        stats_text = f"""=== RAPPORT DE REVENUS DÉTAILLÉ ===
Période d'analyse: {data['period']}

RÉSUMÉ FINANCIER:
• Total recettes: {total_revenue:.2f} €
• Total dépenses: {total_expenses:.2f} €
• Chiffre d'affaires total: {total_revenue:.2f} €
• Revenus services: {service_revenue:.2f} € ({service_percent:.0f}%)
• Revenus produits: {product_revenue:.2f} € ({product_percent:.0f}%)
• Résultat net: {net_result:.2f} €
• Marge nette: {margin_percent:.1f}%

RÉPARTITION PAR MÉTHODE DE PAIEMENT:
┌─────────────────┬─────────────┬─────────────┐
│ Méthode         │ Montant     │ %           │
├─────────────────┼─────────────┼─────────────┤"""
        
        for payment_method in data['payment_methods']:
            percent = (payment_method.total / total_revenue * 100) if total_revenue > 0 else 0
            method_name = payment_method.payment_method[:15]
            stats_text += f"\n│ {method_name:<15} │ {payment_method.total:>9.2f} € │ {percent:>9.0f}% │"
        
        stats_text += "\n└─────────────────┴─────────────┴─────────────┘"
        
        stats_text += "\n\nREVENUS PAR TYPE D'ÉVÉNEMENT:"
        for event_type in data['revenue_by_type']:
            percent = (event_type.total / total_revenue * 100) if total_revenue > 0 else 0
            stats_text += f"\n• {event_type.event_type}: {event_type.total:.2f} € ({percent:.0f}%)"
        
        stats_text += f"""

INDICATEURS CLÉS:
• Panier moyen: {average_basket:.2f} €
• Marge nette: {margin_percent:.1f}%"""
        
        self.financial_stats_text.setPlainText(stats_text)
    
    def on_tab_changed(self, index):
        """Gérer les changements d'onglets"""
        if index == 0:  # Événements du mois
            self.load_monthly_data()
        elif index == 1:  # Événements de l'année
            self.load_yearly_data()
        elif index == 2:  # Rapport financier
            self.load_financial_data()
    
    def get_button_style(self, color):
        """Style pour les boutons"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {color}DD;
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {color}AA;
            }}
        """