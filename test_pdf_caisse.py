import sys
import os
sys.path.append('.')

try:
    from ayanna_erp.modules.salle_fete.view.entreSortie_index import EntreeSortieIndex
    from PyQt6.QtWidgets import QApplication
    import tempfile

    # Créer une application Qt temporaire
    app = QApplication([])

    # Créer un widget temporaire pour tester
    # On simule un main_controller basique
    class MockController:
        def __init__(self):
            self.pos_id = 1

    mock_controller = MockController()
    widget = EntreeSortieIndex(mock_controller, None)

    # Simuler quelques données de test
    from datetime import datetime
    widget.journal_data = [
        {
            'id': 'TEST_1',
            'datetime': datetime.now(),
            'type': 'Entrée',
            'libelle': 'Paiement client - Test',
            'categorie': 'Paiement client',
            'montant_entree': 1500.00,
            'montant_sortie': 0.0,
            'utilisateur': 'Test User',
            'description': ''
        },
        {
            'id': 'TEST_2',
            'datetime': datetime.now(),
            'type': 'Sortie',
            'libelle': 'Achat matériel - Test',
            'categorie': 'Achat matériel',
            'montant_entree': 0.0,
            'montant_sortie': 750.00,
            'utilisateur': 'Test User',
            'description': ''
        }
    ]

    print(f"✅ {len(widget.journal_data)} opérations de test créées")

    # Tester l'export PDF
    # On doit mocker les filtres de date
    from PyQt6.QtCore import QDate
    class MockDateEdit:
        def date(self):
            return QDate.currentDate()

    widget.date_debut_filter = MockDateEdit()
    widget.date_fin_filter = MockDateEdit()

    pdf_filename = widget.export_to_pdf()

    print("✅ Export PDF de caisse terminé")

except Exception as e:
    print(f"❌ Erreur test PDF caisse: {e}")
    import traceback
    traceback.print_exc()