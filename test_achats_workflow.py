#!/usr/bin/env python3
"""
Test du workflow complet du module d'achats
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# Configuration du path
sys.path.insert(0, os.path.abspath('.'))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.achats.models.achats_models import AchatCommande, CoreFournisseur, AchatCommandeLigne, AchatDepense, EtatCommande
from ayanna_erp.modules.achats.controllers.achat_controller import AchatController
from ayanna_erp.modules.boutique.model.models import Produit, Categorie
from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot, StockMovement

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️ {message}")

def test_achats_workflow():
    """Test complet du workflow d'achats"""
    print("=== TEST DU WORKFLOW D'ACHATS ===\n")
    
    # Initialiser la base de données
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    controller = AchatController()
    
    try:
        # 1. Créer un fournisseur
        print("1. Test de création de fournisseur...")
        fournisseur = CoreFournisseur(
            nom="Fournisseur Test",
            telephone="+243 123 456 789",
            email="test@fournisseur.com",
            adresse="123 Rue du Test"
        )
        session.add(fournisseur)
        session.commit()
        print_success(f"Fournisseur créé: {fournisseur.nom} (ID: {fournisseur.id})")
        
        # 2. Créer un entrepôt si nécessaire
        print("\n2. Vérification de l'entrepôt...")
        entrepot = session.query(StockWarehouse).filter_by(code='POS_1').first()
        if not entrepot:
            entrepot = StockWarehouse(
                code='POS_1',
                nom='Entrepôt Principal',
                description='Entrepôt principal pour les tests',
                active=True
            )
            session.add(entrepot)
            session.commit()
            print_success(f"Entrepôt créé: {entrepot.nom}")
        else:
            print_success(f"Entrepôt existant: {entrepot.nom}")
        
        # 3. Créer une catégorie et un produit
        print("\n3. Création de produit...")
        categorie = session.query(Categorie).first()
        if not categorie:
            categorie = Categorie(
                nom="Catégorie Test",
                description="Catégorie pour les tests"
            )
            session.add(categorie)
            session.commit()
        
        produit = Produit(
            nom="Produit Test",
            code="PROD_TEST_001",
            description="Produit pour test d'achat",
            prix_vente=Decimal('150.00'),
            prix_achat=Decimal('100.00'),
            categorie_id=categorie.id,
            active=True
        )
        session.add(produit)
        session.commit()
        print_success(f"Produit créé: {produit.nom} (Code: {produit.code})")
        
        # 4. Créer une commande d'achat
        print("\n4. Création de commande d'achat...")
        commande_data = {
            'fournisseur_id': fournisseur.id,
            'entrepot_id': entrepot.id,
            'date_commande': datetime.now(),
            'numero_commande': 'CMD_TEST_001',
            'notes': 'Commande de test automatique'
        }
        
        lignes_data = [{
            'produit_id': produit.id,
            'quantite': Decimal('5'),
            'prix_unitaire': Decimal('100.00'),
            'remise': Decimal('0')
        }]
        
        result = controller.create_commande(commande_data, lignes_data)
        if result['success']:
            commande = result['commande']
            print_success(f"Commande créée: {commande.numero_commande} (Total: {commande.total_ht} FC)")
        else:
            print_error(f"Erreur création commande: {result['error']}")
            return False
        
        # 5. Effectuer un paiement
        print("\n5. Test de paiement...")
        paiement_data = {
            'montant': Decimal('500.00'),  # Paiement complet
            'mode_paiement': 'ESPECES',
            'reference': 'PAI_TEST_001',
            'notes': 'Paiement test complet'
        }
        
        result = controller.process_paiement_commande(commande.id, paiement_data)
        if result['success']:
            print_success(f"Paiement traité: {paiement_data['montant']} FC")
            print_success(f"Commande validée automatiquement: {result['commande_validated']}")
        else:
            print_error(f"Erreur paiement: {result['error']}")
            return False
        
        # 6. Vérifier l'état final
        print("\n6. Vérification de l'état final...")
        session.refresh(commande)
        print_info(f"État commande: {commande.etat}")
        print_info(f"Total payé: {commande.total_paye} FC")
        
        # 7. Vérifier le stock
        print("\n7. Vérification du stock...")
        stock_entry = session.query(StockProduitEntrepot).filter_by(
            product_id=produit.id,
            warehouse_id=entrepot.id
        ).first()
        
        if stock_entry:
            print_success(f"Stock mis à jour: {stock_entry.quantity} unités")
            print_info(f"Prix unitaire moyen: {stock_entry.unit_cost} FC")
        else:
            print_error("Aucune entrée de stock trouvée")
        
        # 8. Vérifier les mouvements de stock
        print("\n8. Vérification des mouvements...")
        mouvements = session.query(StockMovement).filter_by(
            product_id=produit.id,
            warehouse_id=entrepot.id
        ).all()
        
        print_info(f"Nombre de mouvements: {len(mouvements)}")
        for mouvement in mouvements:
            print_info(f"  - {mouvement.movement_type}: {mouvement.quantity} unités")
        
        print("\n" + "="*50)
        print_success("WORKFLOW D'ACHATS TESTÉ AVEC SUCCÈS!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print_error(f"Erreur pendant le test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        session.close()

if __name__ == "__main__":
    success = test_achats_workflow()
    if success:
        print("\n🎉 Tous les tests ont réussi!")
    else:
        print("\n💥 Des erreurs ont été détectées!")
        sys.exit(1)