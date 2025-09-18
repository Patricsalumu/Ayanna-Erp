#!/usr/bin/env python3
"""
Test pour vérifier si les modèles s'importent correctement
"""
import sys
sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')

try:
    print("Test d'import des modèles...")
    
    # Test du modèle boutique qui avait le problème
    print("1. Import du modèle boutique...")
    from ayanna_erp.modules.boutique.models import ShopProduct, ShopService
    print("   ✅ Modèle boutique importé avec succès")
    
    # Test du modèle comptabilité
    print("2. Import du modèle comptabilité...")
    from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes, ComptaConfig
    print("   ✅ Modèle comptabilité importé avec succès")
    
    # Test du modèle salle de fête
    print("3. Import du modèle salle de fête...")
    from ayanna_erp.modules.salle_fete.model.salle_fete import EventService, EventProduct
    print("   ✅ Modèle salle de fête importé avec succès")
    
    # Test d'initialisation des mappers SQLAlchemy
    print("4. Test d'initialisation de la base de données...")
    from ayanna_erp.database.database_manager import DatabaseManager
    
    db = DatabaseManager()
    print("   ✅ DatabaseManager initialisé")
    
    # Test de création d'une instance
    print("5. Test de création d'instance...")
    product = ShopProduct()
    service = ShopService()
    print("   ✅ Instances créées sans erreur")
    
    print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
    print("   Le problème de référence CompteComptable est résolu.")
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()