#!/usr/bin/env python3
"""
Test simple pour vérifier les exports PDF
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire du projet au PYTHONPATH
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    print("Test des imports...")
    
    # Test import PDFExporter
    from ayanna_erp.modules.salle_fete.utils.pdf_exporter import PDFExporter
    print("✓ PDFExporter importé avec succès")
    
    # Test import RapportController
    from ayanna_erp.modules.salle_fete.controller.rapport_controller import RapportController
    print("✓ RapportController importé avec succès")
    
    # Test création d'objets
    pdf_exporter = PDFExporter()
    print("✓ PDFExporter instancié avec succès")
    
    rapport_controller = RapportController()
    print("✓ RapportController instancié avec succès")
    
    print("\n🎉 Tous les imports fonctionnent correctement !")
    
except Exception as e:
    print(f"❌ Erreur lors des tests: {e}")
    import traceback
    traceback.print_exc()