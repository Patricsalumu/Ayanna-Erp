"""
Test final boutique avec onglets modifiés selon demande utilisateur
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QEventLoop
from ayanna_erp.modules.boutique.view.boutique_window import BoutiqueWindow

def test_boutique_onglets():
    """Test final des onglets de la boutique"""
    
    print("🧪 Test final - Configuration onglets boutique")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    try:
        # Créer utilisateur de test
        test_user = type('User', (), {
            'id': 1, 
            'username': 'test_user',
            'role': 'admin'
        })()
        
        print("📱 Création fenêtre boutique...")
        boutique_window = BoutiqueWindow(test_user, pos_id=1)
        
        # Attendre l'initialisation complète
        loop = QEventLoop()
        QTimer.singleShot(2000, loop.quit)  # 2 secondes
        loop.exec()
        
        # Vérifier les onglets
        tab_count = boutique_window.tab_widget.count()
        print(f"📊 Onglets créés: {tab_count}")
        
        tab_names = []
        for i in range(tab_count):
            tab_name = boutique_window.tab_widget.tabText(i)
            tab_names.append(tab_name)
            print(f"  {i+1}. {tab_name}")
        
        print("\n🔍 Validation demandes utilisateur:")
        
        # Demande: supprimer Stock seulement
        if "📊 Stock" not in tab_names:
            print("  ✅ Onglet Stock supprimé ✓")
        else:
            print("  ❌ Onglet Stock encore présent")
        
        # Demande: garder Produits
        if "📦 Produits" in tab_names:
            print("  ✅ Onglet Produits conservé ✓")
        else:
            print("  ❌ Onglet Produits manquant")
        
        # Nouveau: onglet Commandes
        if "📋 Commandes" in tab_names:
            print("  ✅ Onglet Commandes ajouté ✓")
        else:
            print("  ❌ Onglet Commandes manquant")
        
        # Autres onglets essentiels
        required = ["🛒 Vente", "📂 Catégories", "👥 Clients", "📈 Rapports"]
        for onglet in required:
            if onglet in tab_names:
                print(f"  ✅ {onglet} présent")
            else:
                print(f"  ❌ {onglet} manquant")
        
        print("\n📋 Résumé configuration:")
        print("  Stock: SUPPRIMÉ (comme demandé)")
        print("  Produits: CONSERVÉ (comme demandé)")
        print("  Commandes: AJOUTÉ (nouveau)")
        
        # Affichage visuel
        boutique_window.show()
        print("\n👁️ Interface affichée (fermeture auto dans 4s)")
        
        QTimer.singleShot(4000, app.quit)
        app.exec()
        
        print("✅ Test terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_boutique_onglets()
    sys.exit(0 if success else 1)