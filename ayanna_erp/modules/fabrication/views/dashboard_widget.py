from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QDateEdit, QComboBox, QFileDialog
from PyQt6.QtCore import Qt, QDate
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import Production
from ayanna_erp.modules.achats.views.dashboard_achats_widget import StatCard
from ayanna_erp.core.entreprise_controller import EntrepriseController
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlalchemy import func
import datetime


def _fmt_num(val, decimals: int = 0, suffix: str = '') -> str:
    try:
        if val is None:
            return ''
        if decimals == 0:
            s = f"{int(val):,}".replace(',', ' ')
        else:
            s = f"{float(val):,.{decimals}f}".replace(',', ' ')
        if suffix:
            return f"{s} {suffix}"
        return s
    except Exception:
        try:
            return str(val)
        except Exception:
            return ''


class DashboardWidget(QWidget):
    """Dashboard stylisé pour le module Fabrication (inspiré du dashboard Achats)."""

    def __init__(self, pos_id=None, current_user=None, parent=None):
        super().__init__(parent)
        self.pos_id = pos_id
        self.current_user = current_user
        self.db = DatabaseManager()
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = 'FC'

        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header row with title and refresh
        header = QHBoxLayout()
        title = QLabel("🏭 Tableau de bord - Fabrication")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#2C3E50;")
        header.addWidget(title)
        header.addStretch()
        # Date range controls for sparkline
        self.range_combo = QComboBox()
        self.range_combo.addItem('7 jours', 7)
        self.range_combo.addItem('30 jours', 30)
        self.range_combo.addItem('90 jours', 90)
        header.addWidget(self.range_combo)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        header.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        header.addWidget(self.end_date)

        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.clicked.connect(self.on_refresh_clicked)
        header.addWidget(refresh_btn)

        export_btn = QPushButton("📤 Export PDF")
        export_btn.setToolTip('Exporter le graphique en PDF')
        export_btn.clicked.connect(self.export_sparkline_pdf)
        header.addWidget(export_btn)
        layout.addLayout(header)

        # KPI cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)

        self.total_prod_card = StatCard("Total productions", "0", "📦", "#3498DB")
        self.inprog_card = StatCard("En cours", "0", "⏳", "#F39C12")
        self.completed_card = StatCard("Terminées", "0", "✅", "#27AE60")
        self.failed_card = StatCard("Échecs", "0", "❌", "#E74C3C")
        self.low_stock_card = StatCard("Stocks faibles", "0", "⚠️", "#E67E22")
        self.avg_time_card = StatCard("Temps moyen (min)", "0", "⏱️", "#8E44AD")
        self.avg_yield_card = StatCard("Rendement moyen (%)", "0", "📈", "#2ECC71")

        stats_layout.addWidget(self.total_prod_card)
        stats_layout.addWidget(self.inprog_card)
        stats_layout.addWidget(self.completed_card)
        stats_layout.addWidget(self.failed_card)
        stats_layout.addWidget(self.low_stock_card)
        stats_layout.addWidget(self.avg_time_card)
        stats_layout.addWidget(self.avg_yield_card)

        layout.addLayout(stats_layout)

        # Sparkline area
        spark_layout = QHBoxLayout()
        self.fig = Figure(figsize=(4, 0.8), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        spark_layout.addWidget(self.canvas)
        # final value label to the right of sparkline
        self.final_value_label = QLabel('')
        self.final_value_label.setStyleSheet('font-size:14px; font-weight:bold; padding-left:8px;')
        spark_layout.addWidget(self.final_value_label)
        layout.addLayout(spark_layout)

        # Summary label under sparkline
        self.summary_label = QLabel('')
        self.summary_label.setStyleSheet('font-size:12px; color:#34495E; padding-top:6px;')
        layout.addWidget(self.summary_label)

    def refresh(self):
        try:
            session = self.db.get_session()
            total = session.query(Production).count()
            inprog = session.query(Production).filter(Production.status == 'in_progress').count()
            completed = session.query(Production).filter(Production.status == 'completed').count()
            failed = session.query(Production).filter(Production.status == 'failed').count()

            # Stocks faibles: count product-warehouse where quantity < min_stock_level and min_stock_level > 0
            from ayanna_erp.modules.stock.models import StockProduitEntrepot
            low_stock_q = session.query(StockProduitEntrepot).filter(StockProduitEntrepot.min_stock_level > 0, StockProduitEntrepot.quantity < StockProduitEntrepot.min_stock_level).count()

            # Temps moyen de production (minutes) pour productions terminées
            avg_time = 0
            try:
                avg_time = session.query(func.avg(Production.actual_duration_minutes)).filter(Production.status == 'completed', Production.actual_duration_minutes > 0).scalar() or 0
                avg_time = int(avg_time)
            except Exception:
                avg_time = 0

            # Rendement moyen (%) = avg(produced_quantity / planned_quantity) * 100 for completed productions with planned_quantity>0
            avg_yield = 0
            try:
                prods = session.query(Production).filter(Production.status == 'completed', Production.planned_quantity > 0).all()
                yields = []
                for pr in prods:
                    try:
                        y = float(pr.produced_quantity or 0) / float(pr.planned_quantity or 1) * 100
                        yields.append(y)
                    except Exception:
                        pass
                avg_yield = int(sum(yields) / len(yields)) if yields else 0
            except Exception:
                avg_yield = 0

            self.total_prod_card.update_value(_fmt_num(total))
            self.inprog_card.update_value(_fmt_num(inprog))
            self.completed_card.update_value(_fmt_num(completed))
            self.failed_card.update_value(_fmt_num(failed))
            self.low_stock_card.update_value(_fmt_num(low_stock_q))
            self.avg_time_card.update_value(_fmt_num(avg_time, decimals=0, suffix='min'))
            self.avg_yield_card.update_value(f"{_fmt_num(avg_yield)}%")
            # Update sparkline with default range (from widgets)
            try:
                s_date = self.start_date.date().toPyDate()
                e_date = self.end_date.date().toPyDate()
                self.plot_sparkline(session, s_date, e_date)
            except Exception:
                pass
        except Exception as e:
            print(f"Erreur chargement dashboard fabrication: {e}")
        finally:
            try:
                session.close()
            except Exception:
                pass

    def on_refresh_clicked(self):
        try:
            # adjust start date based on range selection
            days = int(self.range_combo.currentData() or 7)
            self.end_date.setDate(QDate.currentDate())
            self.start_date.setDate(QDate.currentDate().addDays(-days))
        except Exception:
            pass
        self.refresh()

    def plot_sparkline(self, session, start_date: datetime.date, end_date: datetime.date):
        try:
            # build date series
            days = (end_date - start_date).days + 1
            labels = [start_date + datetime.timedelta(days=i) for i in range(days)]
            counts = []
            for d in labels:
                nxt = d + datetime.timedelta(days=1)
                c = session.query(func.count(Production.id)).filter(Production.created_at >= d, Production.created_at < nxt).scalar() or 0
                counts.append(int(c))

            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.plot(labels, counts, color='#2C3E50', linewidth=1.2)
            ax.fill_between(labels, counts, color='#2C3E50', alpha=0.1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            self.canvas.draw()
            # set final value label (last non-null count)
            last_val = counts[-1] if counts else 0
            try:
                self.final_value_label.setText(_fmt_num(last_val))
            except Exception:
                pass
                # update summary (total and average per day)
                try:
                    total = sum(counts)
                    avg = round(total / len(counts), 2) if counts else 0
                    self.summary_label.setText(f"Total: {_fmt_num(total)} — Moyenne/jour: {_fmt_num(avg, decimals=2)}")
                except Exception:
                    try:
                        self.summary_label.setText('')
                    except Exception:
                        pass
        except Exception as e:
            print(f"Erreur plot sparkline: {e}")

    def export_sparkline_pdf(self):
        try:
            out, _ = QFileDialog.getSaveFileName(self, 'Enregistrer le graphique', 'fabrication_sparkline.pdf', 'PDF Files (*.pdf)')
            if not out:
                return

            # get current date range
            s_date = self.start_date.date().toPyDate()
            e_date = self.end_date.date().toPyDate()
            # render a static figure and save to PDF
            fig = Figure(figsize=(8, 3), tight_layout=True)
            ax = fig.add_subplot(111)
            # fetch data from a short-lived session
            db = DatabaseManager()
            session = db.get_session()
            days = (e_date - s_date).days + 1
            labels = [s_date + datetime.timedelta(days=i) for i in range(days)]
            counts = []
            for d in labels:
                nxt = d + datetime.timedelta(days=1)
                c = session.query(func.count(Production.id)).filter(Production.created_at >= d, Production.created_at < nxt).scalar() or 0
                counts.append(int(c))
            session.close()

            ax.plot(labels, counts, color='#2C3E50', linewidth=1.5)
            ax.fill_between(labels, counts, color='#2C3E50', alpha=0.12)
            ax.set_title('Productions par jour')
            ax.set_xlabel('Date')
            ax.set_ylabel('Nombre')
            # add small summary text on the PDF
            total = sum(counts)
            avg = round(total / len(counts), 2) if counts else 0
            fig.text(0.02, 0.95, f"Total: {_fmt_num(total)}")
            fig.text(0.25, 0.95, f"Moyenne/jour: {_fmt_num(avg, decimals=2)}")
            fig.savefig(out)
            QMessageBox.information(self, 'Export', f'Graphique exporté : {out}')
        except Exception as e:
            QMessageBox.warning(self, 'Export', f'Erreur export PDF: {e}')
