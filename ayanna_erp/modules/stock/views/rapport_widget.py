"""
Widget pour la génération et visualisation des rapports de stock
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy import text
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QProgressBar, QFrame, QDateEdit,
    QFileDialog, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

# Import PyQt6-Charts si disponible, sinon utiliser des graphiques simples
try:
    from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis, QPieSeries, QLineSeries
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.controllers.rapport_controller import RapportController


class ReportGenerationThread(QThread):
    """Thread pour la génération de rapports en arrière-plan"""
    
    report_generated = pyqtSignal(dict)  # Rapport généré
    progress_updated = pyqtSignal(int)   # Progression
    error_occurred = pyqtSignal(str)     # Erreur
    
    def __init__(self, controller, report_type, parameters):
        super().__init__()
        self.controller = controller
        self.report_type = report_type
        self.parameters = parameters
    
    def run(self):
        """Générer le rapport"""
        try:
            self.progress_updated.emit(10)
            
            with self.controller.db_manager.get_session() as session:
                self.progress_updated.emit(30)
                
                if self.report_type == "stock_valuation":
                    report_data = self.controller.generate_stock_valuation_report(session, self.parameters)
                elif self.report_type == "movement_analysis":
                    report_data = self.controller.generate_movement_analysis_report(session, self.parameters)
                elif self.report_type == "warehouse_comparison":
                    report_data = self.controller.generate_warehouse_comparison_report(session, self.parameters)
                elif self.report_type == "abc_analysis":
                    report_data = self.controller.generate_abc_analysis_report(session, self.parameters)
                elif self.report_type == "turnover_analysis":
                    report_data = self.controller.generate_turnover_analysis_report(session, self.parameters)
                else:
                    raise ValueError(f"Type de rapport non supporté: {self.report_type}")
                
                self.progress_updated.emit(90)
                
                self.report_generated.emit(report_data)
                self.progress_updated.emit(100)
                
        except Exception as e:
            self.error_occurred.emit(str(e))


class ReportConfigDialog(QDialog):
    """Dialog pour configurer les paramètres d'un rapport"""
    
    def __init__(self, parent=None, report_type=None, pos_id=None):
        super().__init__(parent)
        self.report_type = report_type
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
        
        self.setWindowTitle(f"Configuration du Rapport - {self.get_report_title()}")
        self.setFixedSize(500, 600)
        self.setup_ui()
        self.load_warehouses()
    
    def get_report_title(self):
        """Obtenir le titre du rapport"""
        titles = {
            "stock_valuation": "Valorisation du Stock",
            "movement_analysis": "Analyse des Mouvements",
            "warehouse_comparison": "Comparaison des Entrepôts",
            "abc_analysis": "Analyse ABC",
            "turnover_analysis": "Analyse de Rotation"
        }
        return titles.get(self.report_type, "Rapport")
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel(f"📊 {self.get_report_title()}")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Période
        period_group = QGroupBox("Période d'Analyse")
        period_layout = QFormLayout(period_group)
        
        self.period_type = QComboBox()
        self.period_type.addItems([
            "Période personnalisée",
            "7 derniers jours",
            "30 derniers jours", 
            "3 derniers mois",
            "6 derniers mois",
            "Cette année",
            "Année dernière"
        ])
        self.period_type.currentTextChanged.connect(self.on_period_changed)
        period_layout.addRow("Type de période:", self.period_type)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        period_layout.addRow("Date de début:", self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        period_layout.addRow("Date de fin:", self.end_date)
        
        layout.addWidget(period_group)
        
        # Filtres
        filters_group = QGroupBox("Filtres")
        filters_layout = QFormLayout(filters_group)
        
        # Entrepôts
        self.warehouses_combo = QComboBox()
        filters_layout.addRow("Entrepôts:", self.warehouses_combo)
        
        # Catégories (si applicable)
        if self.report_type in ["abc_analysis", "turnover_analysis"]:
            self.categories_combo = QComboBox()
            self.categories_combo.addItem("Toutes les catégories", None)
            filters_layout.addRow("Catégories:", self.categories_combo)
        
        # Options spécifiques au rapport
        if self.report_type == "stock_valuation":
            self.valuation_method = QComboBox()
            self.valuation_method.addItems(["FIFO", "LIFO", "Coût moyen", "Coût standard"])
            filters_layout.addRow("Méthode de valorisation:", self.valuation_method)
            
            self.include_zero_stock = QCheckBox("Inclure les produits à stock zéro")
            filters_layout.addRow(self.include_zero_stock)
        
        elif self.report_type == "abc_analysis":
            self.abc_criteria = QComboBox()
            self.abc_criteria.addItems(["Valeur du stock", "Quantité vendue", "Chiffre d'affaires", "Marge"])
            filters_layout.addRow("Critère d'analyse:", self.abc_criteria)
            
            self.abc_percentages = QHBoxLayout()
            self.abc_a_percent = QSpinBox()
            self.abc_a_percent.setRange(1, 100)
            self.abc_a_percent.setValue(80)
            self.abc_a_percent.setSuffix("%")
            self.abc_percentages.addWidget(QLabel("A:"))
            self.abc_percentages.addWidget(self.abc_a_percent)
            
            self.abc_b_percent = QSpinBox()
            self.abc_b_percent.setRange(1, 100)
            self.abc_b_percent.setValue(15)
            self.abc_b_percent.setSuffix("%")
            self.abc_percentages.addWidget(QLabel("B:"))
            self.abc_percentages.addWidget(self.abc_b_percent)
            
            self.abc_percentages.addWidget(QLabel("C: Reste"))
            
            filters_layout.addRow("Répartition ABC:", self.abc_percentages)
        
        elif self.report_type == "turnover_analysis":
            self.turnover_period = QComboBox()
            self.turnover_period.addItems(["Mensuel", "Trimestriel", "Annuel"])
            filters_layout.addRow("Période de rotation:", self.turnover_period)
            
            self.min_turnover = QDoubleSpinBox()
            self.min_turnover.setDecimals(2)
            self.min_turnover.setMinimum(0.0)
            self.min_turnover.setMaximum(1000.0)
            self.min_turnover.setValue(0.0)
            filters_layout.addRow("Rotation minimale:", self.min_turnover)
        
        layout.addWidget(filters_group)
        
        # Format de sortie
        output_group = QGroupBox("Format de Sortie")
        output_layout = QFormLayout(output_group)
        
        self.output_format = QComboBox()
        self.output_format.addItems(["Affichage à l'écran", "Export Excel", "Export PDF", "Export CSV"])
        output_layout.addRow("Format:", self.output_format)
        
        self.include_charts = QCheckBox("Inclure les graphiques")
        self.include_charts.setChecked(True)
        output_layout.addRow(self.include_charts)
        
        self.detailed_view = QCheckBox("Vue détaillée")
        self.detailed_view.setChecked(True)
        output_layout.addRow(self.detailed_view)
        
        layout.addWidget(output_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        generate_btn = QPushButton("📊 Générer le Rapport")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        generate_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(generate_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_warehouses(self):
        """Charger la liste des entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                from ayanna_erp.modules.boutique.model.models import ShopWarehouse
                warehouses = session.query(ShopWarehouse).filter(
                    ShopWarehouse.pos_id == self.pos_id,
                    ShopWarehouse.is_active == True
                ).order_by(ShopWarehouse.name).all()
                
                self.warehouses_combo.clear()
                self.warehouses_combo.addItem("Tous les entrepôts", None)
                for warehouse in warehouses:
                    self.warehouses_combo.addItem(f"{warehouse.name} ({warehouse.code})", warehouse.id)
                    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des entrepôts:\n{str(e)}")
    
    def on_period_changed(self):
        """Quand le type de période change"""
        period_type = self.period_type.currentText()
        
        if period_type == "7 derniers jours":
            self.start_date.setDate(QDate.currentDate().addDays(-7))
            self.end_date.setDate(QDate.currentDate())
        elif period_type == "30 derniers jours":
            self.start_date.setDate(QDate.currentDate().addDays(-30))
            self.end_date.setDate(QDate.currentDate())
        elif period_type == "3 derniers mois":
            self.start_date.setDate(QDate.currentDate().addMonths(-3))
            self.end_date.setDate(QDate.currentDate())
        elif period_type == "6 derniers mois":
            self.start_date.setDate(QDate.currentDate().addMonths(-6))
            self.end_date.setDate(QDate.currentDate())
        elif period_type == "Cette année":
            current_year = QDate.currentDate().year()
            self.start_date.setDate(QDate(current_year, 1, 1))
            self.end_date.setDate(QDate.currentDate())
        elif period_type == "Année dernière":
            last_year = QDate.currentDate().year() - 1
            self.start_date.setDate(QDate(last_year, 1, 1))
            self.end_date.setDate(QDate(last_year, 12, 31))
    
    def get_parameters(self):
        """Obtenir les paramètres configurés"""
        parameters = {
            'start_date': self.start_date.date().toPython(),
            'end_date': self.end_date.date().toPython(),
            'warehouse_id': self.warehouses_combo.currentData(),
            'output_format': self.output_format.currentText(),
            'include_charts': self.include_charts.isChecked(),
            'detailed_view': self.detailed_view.isChecked()
        }
        
        # Paramètres spécifiques au rapport
        if self.report_type == "stock_valuation":
            parameters.update({
                'valuation_method': self.valuation_method.currentText(),
                'include_zero_stock': self.include_zero_stock.isChecked()
            })
        elif self.report_type == "abc_analysis":
            parameters.update({
                'abc_criteria': self.abc_criteria.currentText(),
                'abc_a_percent': self.abc_a_percent.value(),
                'abc_b_percent': self.abc_b_percent.value()
            })
        elif self.report_type == "turnover_analysis":
            parameters.update({
                'turnover_period': self.turnover_period.currentText(),
                'min_turnover': self.min_turnover.value()
            })
        
        return parameters


class ReportViewDialog(QDialog):
    """Dialog pour afficher un rapport généré"""
    
    def __init__(self, parent=None, report_data=None, report_type=None):
        super().__init__(parent)
        self.report_data = report_data
        self.report_type = report_type
        
        self.setWindowTitle(f"📊 {report_data.get('title', 'Rapport')}")
        self.setGeometry(100, 100, 1000, 700)
        self.setup_ui()
        self.populate_report()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # En-tête
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.report_data.get('title', 'Rapport'))
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Actions
        export_btn = QPushButton("📤 Exporter")
        export_btn.clicked.connect(self.export_report)
        header_layout.addWidget(export_btn)
        
        print_btn = QPushButton("🖨️ Imprimer")
        print_btn.clicked.connect(self.print_report)
        header_layout.addWidget(print_btn)
        
        close_btn = QPushButton("❌ Fermer")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Onglets pour différentes vues
        tabs = QTabWidget()
        
        # Onglet Résumé
        summary_tab = self.create_summary_tab()
        tabs.addTab(summary_tab, "📋 Résumé")
        
        # Onglet Données détaillées
        details_tab = self.create_details_tab()
        tabs.addTab(details_tab, "📊 Données Détaillées")
        
        # Onglet Graphiques
        if self.report_data.get('include_charts', True):
            charts_tab = self.create_charts_tab()
            tabs.addTab(charts_tab, "📈 Graphiques")
        
        layout.addWidget(tabs)
    
    def create_summary_tab(self) -> QWidget:
        """Créer l'onglet résumé"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Informations du rapport
        info_group = QGroupBox("Informations du Rapport")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("Titre:", QLabel(self.report_data.get('title', 'N/A')))
        info_layout.addRow("Période:", QLabel(self.report_data.get('period_description', 'N/A')))
        info_layout.addRow("Généré le:", QLabel(self.report_data.get('generated_at', datetime.now()).strftime('%d/%m/%Y %H:%M')))
        info_layout.addRow("Nombre d'éléments:", QLabel(str(self.report_data.get('total_items', 0))))
        
        layout.addWidget(info_group)
        
        # Métriques clés
        metrics_group = QGroupBox("Métriques Clés")
        metrics_layout = QGridLayout(metrics_group)
        
        metrics = self.report_data.get('key_metrics', {})
        row = 0
        col = 0
        
        for metric_name, metric_value in metrics.items():
            metric_frame = QFrame()
            metric_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 5px;
                }
            """)
            
            metric_layout = QVBoxLayout(metric_frame)
            
            metric_label = QLabel(metric_name)
            metric_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            metric_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            metric_layout.addWidget(metric_label)
            
            metric_value_label = QLabel(str(metric_value))
            metric_value_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            metric_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            metric_value_label.setStyleSheet("color: #3498db;")
            metric_layout.addWidget(metric_value_label)
            
            metrics_layout.addWidget(metric_frame, row, col)
            
            col += 1
            if col >= 3:  # 3 colonnes maximum
                col = 0
                row += 1
        
        layout.addWidget(metrics_group)
        
        # Résumé textuel
        if 'summary_text' in self.report_data:
            summary_group = QGroupBox("Résumé Exécutif")
            summary_layout = QVBoxLayout(summary_group)
            
            summary_text = QTextEdit()
            summary_text.setPlainText(self.report_data['summary_text'])
            summary_text.setReadOnly(True)
            summary_text.setMaximumHeight(150)
            summary_layout.addWidget(summary_text)
            
            layout.addWidget(summary_group)
        
        layout.addStretch()
        return widget
    
    def create_details_tab(self) -> QWidget:
        """Créer l'onglet des données détaillées"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtres de recherche
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Recherche:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtrer les données...")
        self.search_input.textChanged.connect(self.filter_details_table)
        search_layout.addWidget(self.search_input)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # Tableau des données
        self.details_table = QTableWidget()
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.details_table)
        
        return widget
    
    def create_charts_tab(self) -> QWidget:
        """Créer l'onglet des graphiques"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Sélecteur de graphique
        chart_selector_layout = QHBoxLayout()
        chart_selector_layout.addWidget(QLabel("Graphique:"))
        
        self.chart_selector = QComboBox()
        self.chart_selector.currentTextChanged.connect(self.display_selected_chart)
        chart_selector_layout.addWidget(self.chart_selector)
        
        chart_selector_layout.addStretch()
        layout.addLayout(chart_selector_layout)
        
        # Zone d'affichage des graphiques
        if CHARTS_AVAILABLE:
            self.chart_view = QChartView()
        else:
            # Fallback simple si pas de charts
            self.chart_view = QLabel("Graphiques non disponibles")
            self.chart_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.chart_view)
        
        return widget
    
    def populate_report(self):
        """Peupler le rapport avec les données"""
        # Peupler le tableau des détails
        self.populate_details_table()
        
        # Configurer les graphiques
        if self.report_data.get('include_charts', True):
            self.setup_charts()
    
    def populate_details_table(self):
        """Peupler le tableau des données détaillées"""
        data = self.report_data.get('detailed_data', [])
        if not data:
            return
        
        # Configuration des colonnes
        columns = self.report_data.get('table_columns', [])
        self.details_table.setColumnCount(len(columns))
        self.details_table.setHorizontalHeaderLabels(columns)
        
        # Remplissage des données
        self.details_table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            for col, column_key in enumerate(self.report_data.get('table_column_keys', [])):
                value = item.get(column_key, '')
                
                # Formatage selon le type de donnée
                if isinstance(value, (int, float, Decimal)):
                    if 'price' in column_key.lower() or 'value' in column_key.lower():
                        value_str = f"{float(value):.2f} €"
                    elif 'quantity' in column_key.lower():
                        value_str = f"{float(value):.2f}"
                    else:
                        value_str = str(value)
                elif isinstance(value, datetime):
                    value_str = value.strftime('%d/%m/%Y %H:%M')
                elif isinstance(value, date):
                    value_str = value.strftime('%d/%m/%Y')
                else:
                    value_str = str(value)
                
                table_item = QTableWidgetItem(value_str)
                
                # Alignement pour les nombres
                if isinstance(value, (int, float, Decimal)):
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                self.details_table.setItem(row, col, table_item)
        
        self.details_table.resizeColumnsToContents()
    
    def setup_charts(self):
        """Configurer les graphiques"""
        charts = self.report_data.get('charts', {})
        
        self.chart_selector.clear()
        for chart_name in charts.keys():
            self.chart_selector.addItem(chart_name)
        
        if charts:
            self.display_selected_chart()
    
    def display_selected_chart(self):
        """Afficher le graphique sélectionné"""
        chart_name = self.chart_selector.currentText()
        if not chart_name:
            return
        
        charts = self.report_data.get('charts', {})
        chart_data = charts.get(chart_name, {})
        
        if chart_data.get('type') == 'bar':
            chart = self.create_bar_chart(chart_data)
        elif chart_data.get('type') == 'pie':
            chart = self.create_pie_chart(chart_data)
        elif chart_data.get('type') == 'line':
            chart = self.create_line_chart(chart_data)
        else:
            return
        
        if hasattr(self, 'chart_view') and hasattr(self.chart_view, 'setChart'):
            self.chart_view.setChart(chart)
        else:
            # Fallback si pas de charts
            pass
    
    def create_bar_chart(self, chart_data):
        """Créer un graphique en barres"""
        if not CHARTS_AVAILABLE:
            return None
            
        series = QBarSeries()
        
        for dataset in chart_data.get('datasets', []):
            bar_set = QBarSet(dataset['label'])
            bar_set.append(dataset['data'])
            series.append(bar_set)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(chart_data.get('title', ''))
        
        # Configuration des axes
        categories = chart_data.get('categories', [])
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        return chart
    
    def create_pie_chart(self, chart_data):
        """Créer un graphique circulaire"""
        if not CHARTS_AVAILABLE:
            return None
            
        series = QPieSeries()
        
        for item in chart_data.get('data', []):
            series.append(item['label'], item['value'])
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(chart_data.get('title', ''))
        
        return chart
    
    def create_line_chart(self, chart_data):
        """Créer un graphique linéaire"""
        if not CHARTS_AVAILABLE:
            return None
            
        series = QLineSeries()
        series.setName(chart_data.get('title', ''))
        
        for point in chart_data.get('data', []):
            series.append(point['x'], point['y'])
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(chart_data.get('title', ''))
        
        return chart
    
    def filter_details_table(self):
        """Filtrer le tableau des détails"""
        search_term = self.search_input.text().lower()
        
        for row in range(self.details_table.rowCount()):
            row_visible = False
            
            for col in range(self.details_table.columnCount()):
                item = self.details_table.item(row, col)
                if item and search_term in item.text().lower():
                    row_visible = True
                    break
            
            self.details_table.setRowHidden(row, not row_visible)
    
    def export_report(self):
        """Exporter le rapport"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le Rapport",
            f"rapport_{self.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx);;PDF Files (*.pdf);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # TODO: Implémenter l'export selon le format
                QMessageBox.information(self, "Export", f"Rapport exporté vers:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export:\n{str(e)}")
    
    def print_report(self):
        """Imprimer le rapport"""
        QMessageBox.information(self, "Impression", "Fonctionnalité d'impression à implémenter.")


class RapportWidget(QWidget):
    """Widget principal pour la génération et visualisation des rapports"""
    
    # Signaux
    report_generated = pyqtSignal(dict)  # Quand un rapport est généré
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        # Récupérer entreprise_id depuis pos_id
        self.entreprise_id = self.get_entreprise_id_from_pos(pos_id)
        self.controller = RapportController(self.entreprise_id)
        self.db_manager = DatabaseManager()
        self.recent_reports = []
        
        self.setup_ui()
        self.load_recent_reports()

    def get_entreprise_id_from_pos(self, pos_id):
        """Récupérer l'entreprise_id depuis le pos_id"""
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("SELECT enterprise_id FROM core_pos_points WHERE id = :pos_id"), {"pos_id": pos_id})
                row = result.fetchone()
                return row[0] if row else 1  # Par défaut entreprise 1
        except:
            return 1  # Par défaut entreprise 1
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # En-tête
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 Rapports et Analyses")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_recent_reports)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Zone principale avec splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche : Types de rapports
        reports_panel = self.create_reports_panel()
        main_splitter.addWidget(reports_panel)
        
        # Panneau droit : Rapports récents et historique
        history_panel = self.create_history_panel()
        main_splitter.addWidget(history_panel)
        
        main_splitter.setSizes([400, 600])
        layout.addWidget(main_splitter)
    
    def create_reports_panel(self) -> QWidget:
        """Créer le panneau des types de rapports"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Titre
        title = QLabel("📋 Types de Rapports")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Rapports de stock
        stock_group = QGroupBox("📦 Rapports de Stock")
        stock_layout = QVBoxLayout(stock_group)
        
        # Valorisation du stock
        valuation_btn = QPushButton("💰 Valorisation du Stock")
        valuation_btn.setToolTip("Rapport détaillé de la valeur du stock par entrepôt")
        valuation_btn.clicked.connect(lambda: self.configure_report("stock_valuation"))
        stock_layout.addWidget(valuation_btn)
        
        # Analyse des mouvements
        movements_btn = QPushButton("📈 Analyse des Mouvements")
        movements_btn.setToolTip("Analyse des entrées, sorties et transferts")
        movements_btn.clicked.connect(lambda: self.configure_report("movement_analysis"))
        stock_layout.addWidget(movements_btn)
        
        # Comparaison des entrepôts
        warehouse_comp_btn = QPushButton("🏪 Comparaison des Entrepôts")
        warehouse_comp_btn.setToolTip("Comparaison des performances entre entrepôts")
        warehouse_comp_btn.clicked.connect(lambda: self.configure_report("warehouse_comparison"))
        stock_layout.addWidget(warehouse_comp_btn)
        
        layout.addWidget(stock_group)
        
        # Rapports d'analyse
        analysis_group = QGroupBox("🎯 Analyses Avancées")
        analysis_layout = QVBoxLayout(analysis_group)
        
        # Analyse ABC
        abc_btn = QPushButton("🔤 Analyse ABC")
        abc_btn.setToolTip("Classification ABC des produits selon différents critères")
        abc_btn.clicked.connect(lambda: self.configure_report("abc_analysis"))
        analysis_layout.addWidget(abc_btn)
        
        # Analyse de rotation
        turnover_btn = QPushButton("🔄 Analyse de Rotation")
        turnover_btn.setToolTip("Analyse du taux de rotation des stocks")
        turnover_btn.clicked.connect(lambda: self.configure_report("turnover_analysis"))
        analysis_layout.addWidget(turnover_btn)
        
        # Prévisions
        forecast_btn = QPushButton("🔮 Prévisions de Stock")
        forecast_btn.setToolTip("Prévisions basées sur l'historique de consommation")
        forecast_btn.clicked.connect(lambda: self.configure_report("stock_forecast"))
        analysis_layout.addWidget(forecast_btn)
        
        layout.addWidget(analysis_group)
        
        # Rapports opérationnels
        operational_group = QGroupBox("⚙️ Rapports Opérationnels")
        operational_layout = QVBoxLayout(operational_group)
        
        # Alertes et seuils
        alerts_btn = QPushButton("🚨 Rapport d'Alertes")
        alerts_btn.setToolTip("Synthèse des alertes de stock et actions recommandées")
        alerts_btn.clicked.connect(lambda: self.configure_report("alerts_report"))
        operational_layout.addWidget(alerts_btn)
        
        # Inventaires
        inventory_btn = QPushButton("📋 Rapport d'Inventaires")
        inventory_btn.setToolTip("Résultats et écarts des derniers inventaires")
        inventory_btn.clicked.connect(lambda: self.configure_report("inventory_report"))
        operational_layout.addWidget(inventory_btn)
        
        # Performance des transferts
        transfers_btn = QPushButton("🔄 Performance des Transferts")
        transfers_btn.setToolTip("Analyse des délais et efficacité des transferts")
        transfers_btn.clicked.connect(lambda: self.configure_report("transfers_performance"))
        operational_layout.addWidget(transfers_btn)
        
        layout.addWidget(operational_group)
        
        layout.addStretch()
        return widget
    
    def create_history_panel(self) -> QWidget:
        """Créer le panneau de l'historique"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Titre
        title = QLabel("📚 Rapports Récents")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Tableau des rapports récents
        self.recent_reports_table = QTableWidget()
        self.recent_reports_table.setColumnCount(5)
        self.recent_reports_table.setHorizontalHeaderLabels([
            "Type", "Période", "Généré le", "Statut", "Actions"
        ])
        self.recent_reports_table.setAlternatingRowColors(True)
        self.recent_reports_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.recent_reports_table)
        
        # Barre de progression pour la génération
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Progression:"))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        
        layout.addLayout(progress_layout)
        
        return widget
    
    def configure_report(self, report_type):
        """Configurer et générer un rapport"""
        dialog = ReportConfigDialog(self, report_type=report_type, pos_id=self.pos_id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            parameters = dialog.get_parameters()
            self.generate_report(report_type, parameters)
    
    def generate_report(self, report_type, parameters):
        """Générer un rapport"""
        # Afficher la barre de progression
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Génération en cours...")
        self.progress_bar.setValue(0)
        
        # Créer et démarrer le thread de génération
        self.generation_thread = ReportGenerationThread(self.controller, report_type, parameters)
        self.generation_thread.report_generated.connect(self.on_report_generated)
        self.generation_thread.progress_updated.connect(self.on_progress_updated)
        self.generation_thread.error_occurred.connect(self.on_generation_error)
        self.generation_thread.start()
    
    @pyqtSlot(dict)
    def on_report_generated(self, report_data):
        """Quand un rapport est généré"""
        # Masquer la barre de progression
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Afficher le rapport
        if report_data.get('output_format') == "Affichage à l'écran":
            dialog = ReportViewDialog(self, report_data=report_data, report_type=report_data.get('type'))
            dialog.exec()
        else:
            # Export direct
            self.export_report_directly(report_data)
        
        # Recharger les rapports récents
        self.load_recent_reports()
        
        # Émettre le signal
        self.report_generated.emit(report_data)
    
    @pyqtSlot(int)
    def on_progress_updated(self, progress):
        """Mettre à jour la progression"""
        self.progress_bar.setValue(progress)
    
    @pyqtSlot(str)
    def on_generation_error(self, error_message):
        """Quand une erreur survient pendant la génération"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du rapport:\n{error_message}")
    
    def export_report_directly(self, report_data):
        """Exporter un rapport directement"""
        output_format = report_data.get('output_format', 'Excel')
        
        if 'Excel' in output_format:
            extension = 'xlsx'
        elif 'PDF' in output_format:
            extension = 'pdf'
        elif 'CSV' in output_format:
            extension = 'csv'
        else:
            extension = 'txt'
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder le Rapport",
            f"rapport_{report_data.get('type', 'report')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}",
            f"{output_format} Files (*.{extension})"
        )
        
        if file_path:
            try:
                # TODO: Implémenter l'export selon le format
                QMessageBox.information(self, "Export", f"Rapport exporté vers:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export:\n{str(e)}")
    
    def load_recent_reports(self):
        """Charger les rapports récents"""
        try:
            with self.db_manager.get_session() as session:
                self.recent_reports = self.controller.get_recent_reports(session, limit=20)
                self.populate_recent_reports_table()
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des rapports récents:\n{str(e)}")
    
    def populate_recent_reports_table(self):
        """Peupler le tableau des rapports récents"""
        self.recent_reports_table.setRowCount(len(self.recent_reports))
        
        for row, report in enumerate(self.recent_reports):
            # Type
            report_types = {
                'stock_valuation': '💰 Valorisation',
                'movement_analysis': '📈 Mouvements',
                'warehouse_comparison': '🏪 Comparaison',
                'abc_analysis': '🔤 Analyse ABC',
                'turnover_analysis': '🔄 Rotation',
                'alerts_report': '🚨 Alertes',
                'inventory_report': '📋 Inventaires'
            }
            type_text = report_types.get(report.get('type'), report.get('type', 'N/A'))
            self.recent_reports_table.setItem(row, 0, QTableWidgetItem(type_text))
            
            # Période
            period = f"{report.get('start_date', 'N/A')} - {report.get('end_date', 'N/A')}"
            self.recent_reports_table.setItem(row, 1, QTableWidgetItem(period))
            
            # Généré le
            generated_at = report.get('generated_at', datetime.now())
            if isinstance(generated_at, datetime):
                date_str = generated_at.strftime('%d/%m/%Y %H:%M')
            else:
                date_str = "N/A"
            self.recent_reports_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Statut
            status_icons = {
                'COMPLETED': '✅ Terminé',
                'IN_PROGRESS': '🔄 En cours',
                'ERROR': '❌ Erreur'
            }
            status = status_icons.get(report.get('status'), report.get('status', 'N/A'))
            self.recent_reports_table.setItem(row, 3, QTableWidgetItem(status))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            if report.get('status') == 'COMPLETED':
                view_btn = QPushButton("👁️")
                view_btn.setToolTip("Voir le rapport")
                view_btn.setMaximumWidth(30)
                view_btn.clicked.connect(lambda checked, r=report: self.view_saved_report(r))
                actions_layout.addWidget(view_btn)
                
                download_btn = QPushButton("📥")
                download_btn.setToolTip("Télécharger")
                download_btn.setMaximumWidth(30)
                download_btn.clicked.connect(lambda checked, r=report: self.download_report(r))
                actions_layout.addWidget(download_btn)
            
            self.recent_reports_table.setCellWidget(row, 4, actions_widget)
        
        self.recent_reports_table.resizeColumnsToContents()
    
    def view_saved_report(self, report):
        """Voir un rapport sauvegardé"""
        # TODO: Charger et afficher le rapport sauvegardé
        QMessageBox.information(self, "Rapport", f"Affichage du rapport {report.get('type', 'N/A')}")
    
    def download_report(self, report):
        """Télécharger un rapport"""
        # TODO: Télécharger le rapport depuis le stockage
        QMessageBox.information(self, "Téléchargement", f"Téléchargement du rapport {report.get('type', 'N/A')}")