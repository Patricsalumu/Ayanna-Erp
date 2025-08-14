#!/usr/bin/env python3
"""
Script de démonstration pour Ayanna ERP
Génère des données de test pour tous les modules
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import (
    DatabaseManager, User, Entreprise, Partner, Module, POSPoint,
    ClasseComptable, CompteComptable, PaymentMethod
)


def create_demo_data():
    """Créer des données de démonstration"""
    print("🎭 Création des données de démonstration...")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # Vérifier si des données existent déjà
        existing_enterprise = session.query(Entreprise).first()
        if not existing_enterprise:
            print("❌ Aucune entreprise trouvée. Exécutez d'abord install.py")
            return False
        
        enterprise = existing_enterprise
        
        # Créer des clients de démonstration
        demo_clients = [
            {
                "name": "Jean Dupont",
                "email": "jean.dupont@email.com",
                "phone": "+243 123 456 789",
                "address": "123 Rue de la Paix, Kinshasa"
            },
            {
                "name": "Marie Kabila", 
                "email": "marie.kabila@email.com",
                "phone": "+243 987 654 321",
                "address": "456 Avenue des Martyrs, Lubumbashi"
            },
            {
                "name": "Entreprise ABC SARL",
                "email": "contact@abc-sarl.cd",
                "phone": "+243 555 123 456",
                "address": "789 Boulevard du 30 Juin, Matadi"
            }
        ]
        
        for client_data in demo_clients:
            existing_client = session.query(Partner).filter_by(
                enterprise_id=enterprise.id,
                email=client_data["email"]
            ).first()
            
            if not existing_client:
                client = Partner(
                    enterprise_id=enterprise.id,
                    **client_data
                )
                session.add(client)
        
        # Créer des POS pour chaque module
        modules = session.query(Module).all()
        for module in modules:
            existing_pos = session.query(POSPoint).filter_by(
                enterprise_id=enterprise.id,
                module_id=module.id
            ).first()
            
            if not existing_pos:
                pos_names = {
                    "SalleFete": "POS Salle de Fête Principale",
                    "Boutique": "POS Boutique Centrale", 
                    "Pharmacie": "POS Pharmacie",
                    "Restaurant": "POS Restaurant Principal",
                    "Hotel": "POS Hôtel",
                    "Achats": "POS Achats",
                    "Stock": "POS Stock Central",
                    "Comptabilite": "POS Comptabilité"
                }
                
                pos = POSPoint(
                    enterprise_id=enterprise.id,
                    module_id=module.id,
                    name=pos_names.get(module.name, f"POS {module.name}")
                )
                session.add(pos)
        
        # Créer des comptes comptables de base
        classe_vente = session.query(ClasseComptable).filter_by(code="7").first()
        if classe_vente:
            comptes_demo = [
                {
                    "code": "701",
                    "nom": "Ventes de marchandises",
                    "libelle": "Ventes de marchandises",
                    "classe_comptable_id": classe_vente.id
                },
                {
                    "code": "7021",
                    "nom": "Ventes de produits finis",
                    "libelle": "Ventes de produits finis",
                    "classe_comptable_id": classe_vente.id
                },
                {
                    "code": "706",
                    "nom": "Services vendus",
                    "libelle": "Services vendus",
                    "classe_comptable_id": classe_vente.id
                }
            ]
            
            for compte_data in comptes_demo:
                existing_compte = session.query(CompteComptable).filter_by(
                    code=compte_data["code"]
                ).first()
                
                if not existing_compte:
                    compte = CompteComptable(**compte_data)
                    session.add(compte)
        
        # Créer des moyens de paiement par défaut pour chaque POS
        pos_points = session.query(POSPoint).all()
        for pos in pos_points:
            # Vérifier si des moyens de paiement existent déjà
            existing_payments = session.query(PaymentMethod).filter_by(pos_id=pos.id).first()
            
            if not existing_payments:
                # Espèces (par défaut)
                cash_payment = PaymentMethod(
                    module_id=pos.module_id,
                    pos_id=pos.id,
                    name="Espèces",
                    is_default=True,
                    is_active=True
                )
                session.add(cash_payment)
                
                # Compte client
                credit_payment = PaymentMethod(
                    module_id=pos.module_id,
                    pos_id=pos.id,
                    name="Compte client",
                    is_default=False,
                    is_active=True
                )
                session.add(credit_payment)
                
                # Carte bancaire
                card_payment = PaymentMethod(
                    module_id=pos.module_id,
                    pos_id=pos.id,
                    name="Carte bancaire",
                    is_default=False,
                    is_active=True
                )
                session.add(card_payment)
        
        session.commit()
        print("✅ Données de démonstration créées avec succès!")
        
        # Afficher un résumé
        print("\n📊 Résumé des données créées:")
        clients_count = session.query(Partner).filter_by(enterprise_id=enterprise.id).count()
        pos_count = session.query(POSPoint).filter_by(enterprise_id=enterprise.id).count()
        payments_count = session.query(PaymentMethod).count()
        
        print(f"   👥 Clients: {clients_count}")
        print(f"   🏪 Points de vente: {pos_count}")
        print(f"   💳 Moyens de paiement: {payments_count}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de la création des données: {e}")
        return False
    
    finally:
        session.close()


def main():
    """Fonction principale"""
    print("🎭 Ayanna ERP - Génération de données de démonstration")
    print("=" * 50)
    
    success = create_demo_data()
    
    print("\n" + "=" * 50)
    
    if success:
        print("🎉 Données de démonstration créées avec succès!")
        print("\nVous pouvez maintenant:")
        print("1. Lancer l'application: python3 main.py")
        print("2. Se connecter avec: admin@ayanna.com / admin123")
        print("3. Explorer les modules avec des données de test")
    else:
        print("❌ Échec de la création des données de démonstration")
        print("Assurez-vous d'avoir exécuté install.py au préalable")


if __name__ == "__main__":
    main()
