#!/usr/bin/env python3
"""
Test simple pour valider la correction de l'erreur QDate
"""

import sys
import os
from datetime import datetime, date

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def test_qdate_conversion():
    """Tester la conversion QDate vers date Python"""
    print("=== Test de la correction QDate ===")
    
    try:
        from PyQt6.QtCore import QDate
        from PyQt6.QtWidgets import QApplication
        
        # Créer une application Qt minimale
        app = QApplication([])
        
        # Créer un QDate
        qdate = QDate.currentDate()
        print(f"QDate original: {qdate.toString('yyyy-MM-dd')}")
        
        # Méthode corrigée pour convertir QDate en date Python
        python_date = date(qdate.year(), qdate.month(), qdate.day())
        print(f"Date Python convertie: {python_date}")
        
        # Convertir en datetime
        datetime_obj = datetime.combine(python_date, datetime.min.time())
        print(f"DateTime pour la BDD: {datetime_obj}")
        
        print("✅ Conversion QDate vers date Python réussie!")
        
        # Test avec le controller
        from ayanna_erp.modules.salle_fete.controller.rapport_controller import RapportController
        
        controller = RapportController()
        print("✅ RapportController instancié avec succès!")
        
        # Test d'une requête simple
        today = datetime.now()
        yesterday = today.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        data = controller.get_financial_report_data(yesterday, tomorrow)
        print(f"✅ Données financières récupérées pour aujourd'hui")
        print(f"   - Total recettes: {data['total_revenue']:.2f} €")
        print(f"   - Total dépenses: {data['total_expenses']:.2f} €")
        print(f"   - Résultat net: {data['net_result']:.2f} €")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qdate_conversion()