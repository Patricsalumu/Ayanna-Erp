"""
Test d'intégration de l'onglet Commandes dans le module Boutique
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.modules.boutique.view.boutique_window import BoutiqueWindow
from ayanna_erp.core.session_manager import SessionManager

def test_commandes_tab():
    """Test de l'onglet Commandes"""
    
    print("🧪 Test d'intégration de l'onglet Commandes")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    try:
        # Créer une session utilisateur de test
        session_manager = SessionManager()
        test_user = type('User', (), {
            'id': 1, 
            'username': 'test_user',
            'role': 'admin'
        })()
        
        # Créer la fenêtre boutique
        print("📱 Création de la fenêtre boutique...")
        boutique_window = BoutiqueWindow(test_user, pos_id=1)
        
        # Vérifier que les onglets sont correctement créés
        tab_count = boutique_window.tab_widget.count()
        print(f"📊 Nombre d'onglets créés: {tab_count}")
        
        # Lister les onglets
        tab_names = []
        for i in range(tab_count):
            tab_name = boutique_window.tab_widget.tabText(i)
            tab_names.append(tab_name)
            print(f"  - Onglet {i+1}: {tab_name}")
        
        # Vérifications
        assert "🛒 Vente" in tab_names, "Onglet Vente manquant"
        assert "📋 Commandes" in tab_names, "Onglet Commandes manquant"
        assert "📂 Catégories" in tab_names, "Onglet Catégories manquant"
        assert "👥 Clients" in tab_names, "Onglet Clients manquant"
        assert "📈 Rapports" in tab_names, "Onglet Rapports manquant"
        
        # Vérifier que les anciens onglets ont été supprimés
        assert "📦 Produits" not in tab_names, "Onglet Produits devrait être supprimé"
        assert "📊 Stock" not in tab_names, "Onglet Stock devrait être supprimé"
        
        print("✅ Vérifications réussies:")
        print("  ✓ Onglet Commandes présent")
        print("  ✓ Onglets Stock et Produits supprimés")
        print("  ✓ Autres onglets préservés")
        
        # Test du widget Commandes
        if hasattr(boutique_window, 'commandes_widget'):
            commandes_widget = boutique_window.commandes_widget
            print("✅ Widget Commandes accessible")
            
            # Test de la méthode refresh_data
            if hasattr(commandes_widget, 'refresh_data'):
                print("✅ Méthode refresh_data disponible")
            else:
                print("⚠️ Méthode refresh_data manquante")
        else:
            print("❌ Widget Commandes non accessible")
        
        # Afficher la fenêtre pour validation visuelle
        boutique_window.show()
        print("👁️ Fenêtre affichée pour validation visuelle")
        print("📋 L'onglet Commandes devrait être visible avec l'interface de gestion")
        
        # Fermer après 3 secondes
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, app.quit)
        
        app.exec()
        
        print("✅ Test d'intégration terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_commandes_tab()
    sys.exit(0 if success else 1)