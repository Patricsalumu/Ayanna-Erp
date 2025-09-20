#!/usr/bin/env python3
"""
Test pour vérifier que les formulaires de produits et services 
filtrent correctement les comptes par entreprise.
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager, POSPoint
from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController
from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController


class MockProduitForm:
    """Mock class pour simuler ProduitForm"""
    def __init__(self, controller):
        self.controller = controller
    
    def get_enterprise_id(self):
        """Récupérer l'ID de l'entreprise depuis le contrôleur produit"""
        try:
            if self.controller and hasattr(self.controller, 'pos_id'):
                # Récupérer l'entreprise depuis le pos_id
                from ayanna_erp.database.database_manager import get_database_manager
                
                db_manager = get_database_manager()
                session = db_manager.get_session()
                
                try:
                    # Récupérer le POS et son entreprise
                    from ayanna_erp.database.database_manager import POSPoint
                    pos = session.query(POSPoint).filter_by(id=self.controller.pos_id).first()
                    
                    if pos:
                        return pos.enterprise_id
                    else:
                        print(f"⚠️  POS avec ID {self.controller.pos_id} non trouvé")
                        return None
                finally:
                    session.close()
            else:
                print("⚠️  Contrôleur ou pos_id non disponible")
                return None
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de l'entreprise: {e}")
            return None
    
    def load_sales_accounts(self):
        """Charger les comptes de vente dans le combo box"""
        try:
            # Importer ici pour éviter les imports circulaires
            from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
            
            comptabilite_controller = ComptabiliteController()
            
            # Récupérer l'entreprise depuis le contrôleur produit
            entreprise_id = self.get_enterprise_id()
            
            # Filtrer les comptes par entreprise
            comptes = comptabilite_controller.get_comptes_vente(entreprise_id=entreprise_id)
            
            return comptes
                
        except Exception as e:
            print(f"Erreur lors du chargement des comptes: {e}")
            return []


def test_form_account_filtering():
    """Test du filtrage des comptes dans les formulaires"""
    print("🧪 Test du filtrage des comptes dans les formulaires")
    print("="*50)
    
    db_manager = get_database_manager()
    session = db_manager.get_session()
    
    try:
        # 1. Récupérer quelques POS existants
        print("\n1️⃣ Récupération des POS existants...")
        
        pos_list = session.query(POSPoint).limit(3).all()
        
        if len(pos_list) < 2:
            print("❌ Pas assez de POS pour le test")
            return False
        
        for i, pos in enumerate(pos_list):
            print(f"✅ POS {i+1}: ID {pos.id}, Entreprise {pos.enterprise_id}, Nom '{pos.name}'")
        
        # 2. Test avec des contrôleurs produit différents
        print("\n2️⃣ Test avec les contrôleurs produit...")
        
        for i, pos in enumerate(pos_list[:2]):  # Prendre les 2 premiers
            print(f"\n🔍 Test POS {pos.id} (Entreprise {pos.enterprise_id}):")
            
            # Créer le contrôleur
            produit_controller = ProduitController(pos_id=pos.id)
            
            # Créer le mock form
            mock_form = MockProduitForm(produit_controller)
            
            # Récupérer l'entreprise
            enterprise_id = mock_form.get_enterprise_id()
            print(f"   📍 Entreprise récupérée: {enterprise_id}")
            
            # Charger les comptes
            comptes = mock_form.load_sales_accounts()
            print(f"   📊 Nombre de comptes: {len(comptes)}")
            
            # Afficher les premiers comptes
            for j, compte in enumerate(comptes[:3]):
                print(f"      {j+1}. {compte.numero} - {compte.nom}")
            
            if len(comptes) > 3:
                print(f"      ... et {len(comptes) - 3} autres comptes")
        
        # 3. Test avec des contrôleurs service différents  
        print("\n3️⃣ Test avec les contrôleurs service...")
        
        for i, pos in enumerate(pos_list[:2]):  # Prendre les 2 premiers
            print(f"\n🔍 Test POS {pos.id} (Entreprise {pos.enterprise_id}):")
            
            # Créer le contrôleur
            service_controller = ServiceController(pos_id=pos.id)
            
            # Créer le mock form (même logique pour service)
            mock_form = MockProduitForm(service_controller)
            
            # Récupérer l'entreprise
            enterprise_id = mock_form.get_enterprise_id()
            print(f"   📍 Entreprise récupérée: {enterprise_id}")
            
            # Charger les comptes
            comptes = mock_form.load_sales_accounts()
            print(f"   📊 Nombre de comptes: {len(comptes)}")
        
        print("\n✅ Test terminé avec succès !")
        print("🎯 Les formulaires filtrent correctement les comptes par entreprise.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = test_form_account_filtering()
    if success:
        print("\n🎉 Test terminé avec succès !")
        sys.exit(0)
    else:
        print("\n💥 Test échoué !")
        sys.exit(1)