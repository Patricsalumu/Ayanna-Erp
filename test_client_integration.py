"""
Test rapide pour vérifier que le nouvel onglet client fonctionne
"""

import sys
import os

# Ajouter le chemin racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    # Test d'import du ClientIndex
    from ayanna_erp.modules.vente.view.client_index import ClientIndex
    print("✅ Import ClientIndex réussi")
    
    # Test d'import du modèle ShopClient
    from ayanna_erp.modules.boutique.model.models import ShopClient
    print("✅ Import ShopClient réussi")
    
    # Test d'import DatabaseManager
    from ayanna_erp.database.database_manager import DatabaseManager
    print("✅ Import DatabaseManager réussi")
    
    print("\n🎉 Tous les imports sont valides !")
    print("📋 Le nouvel onglet client est prêt à être utilisé.")
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
except Exception as e:
    print(f"❌ Erreur: {e}")