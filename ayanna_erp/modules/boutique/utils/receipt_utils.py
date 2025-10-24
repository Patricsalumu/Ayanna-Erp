import os
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout, QPushButton, QMessageBox, QFileDialog
from PyQt6.QtGui import QPixmap, QFont, QTextDocument
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter

def show_sale_receipt(parent, sale_data, payment_data, enterprise_controller, current_user=None, pos_id=1):
    """Affiche un reçu de vente dans un dialogue (utilitaire partagé).

    Args:
        parent: QWidget parent
        sale_data: dict contenant subtotal, discount_amount, total_amount, sale_date, notes (optionnel)
        payment_data: dict contenant method, amount_received, change
        enterprise_controller: instance of EntrepriseController
        current_user: objet utilisateur (optionnel)
        pos_id: identifiant du POS (optionnel)
    """
    ent = enterprise_controller.get_current_enterprise()

    order_dt = sale_data.get('sale_date') or datetime.now()
    order_number = f"CMD-{pos_id}-{order_dt.strftime('%Y%m%d%H%M%S')}"

    # Construire le texte du reçu
    receipt_lines = []
    receipt_lines.append("===============================")
    receipt_lines.append(ent.get('name', ''))
    receipt_lines.append("===============================\n")
    receipt_lines.append(f"Adresse: {ent.get('address','')}")
    receipt_lines.append(f"Téléphone: {ent.get('phone','')}")
    receipt_lines.append(f"Email: {ent.get('email','')}")
    receipt_lines.append("")
    receipt_lines.append("===== REÇU DE VENTE =====")
    receipt_lines.append(f"N° Commande: {order_number}")
    receipt_lines.append(f"Date: {order_dt.strftime('%d/%m/%Y %H:%M')}")
    receipt_lines.append(f"POS: #{pos_id}")
    receipt_lines.append(f"Vendeur: {getattr(current_user, 'name', 'Utilisateur') if current_user else 'Utilisateur'}")
    receipt_lines.append("")
    receipt_lines.append("--- DÉTAIL DES ARTICLES ---")

    for item in sale_data.get('cart_items', []):
        name = item.get('name', '')
        qty = item.get('quantity', 0)
        unit = item.get('unit_price', 0)
        line_total = unit * qty
        receipt_lines.append(f"{name[:28]:<28} {qty:>3} x {unit:>6.0f} = {line_total:>8.0f}")

    # RÉCAPITULATIF (format 53 mm thermique)
    receipt_lines.append("")
    receipt_lines.append("===== RÉCAPITULATIF =====")
    receipt_lines.append(f"Sous-total: {sale_data.get('subtotal',0):.2f} FC")
    receipt_lines.append(f"Remise: -{sale_data.get('discount_amount',0):.2f} FC")
    receipt_lines.append(f"NET À PAYER: {sale_data.get('total_amount',0):.2f} FC")
    # Paiement details
    receipt_lines.append(f"PAYÉ: {payment_data.get('amount_received',0):.2f} FC")
    # Change/remaining
    received = float(payment_data.get('amount_received', 0) or 0)
    total = float(sale_data.get('total_amount', 0) or 0)
    reste = max(0.0, total - received)
    receipt_lines.append(f"RESTE: {reste:.2f} FC")

    # Notes should appear AFTER the recapitulatif
    if sale_data.get('notes'):
        receipt_lines.append("")
        receipt_lines.append("--- NOTES ---")
        receipt_lines.append(sale_data.get('notes'))

    receipt_lines.append("\nMerci pour votre achat !")
    receipt_lines.append("===============================")

    # Préparer le dialogue
    dialog = QDialog(parent)
    dialog.setWindowTitle("🧾 Reçu de vente")
    dialog.setMinimumSize(480, 600)

    layout = QVBoxLayout(dialog)

    # Afficher logo si présent (et informations entreprise)
    logo_path = None
    try:
        blob = ent.get('logo')
        if blob:
            fd, tmp_path = tempfile.mkstemp(suffix='.png')
            with os.fdopen(fd, 'wb') as f:
                f.write(blob)
            logo_path = tmp_path
            if os.path.exists(logo_path):
                logo_label = QLabel()
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaledToWidth(160)
                    logo_label.setPixmap(scaled)
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(logo_label)
    except Exception:
        logo_path = None

    # Entête entreprise (nom déjà dans lines) - conserver mais ensure spacing
    text = "\n".join(receipt_lines)
    display = QTextEdit()
    display.setPlainText(text)
    display.setReadOnly(True)
    # Utiliser une police monospace pour alignement thermique
    mono = QFont("Courier New")
    mono.setPointSize(10)
    display.setFont(mono)
    layout.addWidget(display)

    # Boutons: Imprimer (délégué), Enregistrer en PDF, Fermer
    btn_layout = QHBoxLayout()

    print_btn = QPushButton("🖨️ Imprimer")
    def _print():
        # Utiliser la méthode d'impression parent si disponible
        if hasattr(parent, '_print_receipt'):
            try:
                parent._print_receipt(text)
                return
            except Exception:
                pass
        QMessageBox.information(parent, "Impression", "Fonction d'impression à implémenter")
    print_btn.clicked.connect(_print)
    btn_layout.addWidget(print_btn)

    pdf_btn = QPushButton("📄 Enregistrer en PDF")
    def _save_pdf():
        filename, _ = QFileDialog.getSaveFileName(parent, "Enregistrer le reçu en PDF", f"recu-{order_number}.pdf", "PDF Files (*.pdf)")
        if not filename:
            return
        try:
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filename)
            doc = QTextDocument()
            # Conserver la mise en forme monospaced
            doc.setDefaultFont(mono)
            doc.setPlainText(text)
            doc.print(printer)
            QMessageBox.information(parent, "PDF", f"Reçu enregistré: {filename}")
        except Exception as e:
            QMessageBox.warning(parent, "PDF", f"Erreur génération PDF: {e}")
    pdf_btn.clicked.connect(_save_pdf)
    btn_layout.addWidget(pdf_btn)

    close_btn = QPushButton("✅ Fermer")
    close_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(close_btn)

    layout.addLayout(btn_layout)

    dialog.exec()

    # Nettoyer le logo temporaire
    try:
        if logo_path and os.path.exists(logo_path):
            os.remove(logo_path)
    except Exception:
        pass
