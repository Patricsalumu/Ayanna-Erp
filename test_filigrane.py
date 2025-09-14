#!/usr/bin/env python3
"""
Test du filigrane PDF
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire du projet au PYTHONPATH
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from ayanna_erp.modules.salle_fete.utils.pdf_exporter import PDFExporter
    
    # Créer l'exporteur PDF
    pdf_exporter = PDFExporter()
    
    # Données de test simples
    test_data = {
        'period': 'Septembre 2025',
        'events_count': 5,
        'total_revenue': 1500.00,
        'total_expenses': 300.00,
        'net_result': 1200.00,
        'average_revenue': 300.00,
        'top_services': []
    }
    
    test_comparison = {
        'revenue_evolution': 15.5,
        'net_result_evolution': 20.0
    }
    
    # Créer le dossier de test
    os.makedirs("data/reports", exist_ok=True)
    
    # Test d'export simple
    filename = "data/reports/test_filigrane.pdf"
    result = pdf_exporter.export_monthly_report(test_data, test_comparison, None, filename)
    
    print(f"✅ PDF de test créé : {result}")
    print("Vérifiez le filigrane en haut du PDF !")
    
except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()