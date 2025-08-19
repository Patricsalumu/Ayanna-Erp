#!/usr/bin/env python3
"""
Test simple du module comptabilité pour vérifier les fonctionnalités de base
"""

import sys
import os

# Ajouter les chemins nécessaires
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_basic_accounting_operations():
    """Tester les opérations de base de la comptabilité"""
    try:
        from ayanna_erp.database.database_manager import DatabaseManager
        from ayanna_erp.modules.comptabilite.model.comptabilite import (
            ComptaClasses, ComptaComptes, ComptaJournaux, ComptaEcritures, ComptaConfig
        )
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        print("=== Test des opérations comptables de base ===\n")
        
        # 1. Lister les classes comptables
        print("1. Classes comptables disponibles:")
        classes = session.query(ComptaClasses).filter_by(enterprise_id=1).all()
        for classe in classes:
            print(f"   {classe.code} - {classe.nom}")
        
        # 2. Lister quelques comptes
        print("\n2. Comptes comptables disponibles:")
        comptes = session.query(ComptaComptes).filter_by(enterprise_id=1).limit(5).all()
        for compte in comptes:
            print(f"   {compte.numero} - {compte.nom}")
        
        # 3. Vérifier la configuration
        print("\n3. Configuration comptable:")
        config = session.query(ComptaConfig).filter_by(enterprise_id=1).first()
        if config:
            print(f"   ✅ Configuration trouvée pour l'entreprise {config.enterprise_id}")
            if config.compte_caisse:
                print(f"   📦 Compte caisse: {config.compte_caisse.numero} - {config.compte_caisse.nom}")
            if config.compte_client:
                print(f"   👥 Compte client: {config.compte_client.numero} - {config.compte_client.nom}")
        else:
            print("   ❌ Aucune configuration trouvée")
        
        # 4. Compter les journaux existants
        journaux_count = session.query(ComptaJournaux).filter_by(enterprise_id=1).count()
        print(f"\n4. Nombre de journaux existants: {journaux_count}")
        
        # 5. Compter les écritures existantes
        ecritures_count = session.query(ComptaEcritures).count()
        print(f"5. Nombre d'écritures existantes: {ecritures_count}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def create_sample_transaction():
    """Créer une transaction d'exemple"""
    try:
        from ayanna_erp.database.database_manager import DatabaseManager
        from ayanna_erp.modules.comptabilite.model.comptabilite import (
            ComptaComptes, ComptaJournaux, ComptaEcritures, ComptaConfig
        )
        from datetime import datetime
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        print("\n=== Création d'une transaction d'exemple ===\n")
        
        # Récupérer la configuration
        config = session.query(ComptaConfig).filter_by(enterprise_id=1).first()
        if not config or not config.compte_caisse or not config.compte_vente:
            print("❌ Configuration comptable incomplète")
            return False
        
        # Créer une transaction de vente
        journal = ComptaJournaux(
            date_operation=datetime.now(),
            libelle="Vente de services - Test",
            montant=500.00,
            type_operation="entree",
            reference="VENTE-001",
            description="Transaction de test pour validation du module",
            enterprise_id=1,
            user_id=1
        )
        session.add(journal)
        session.flush()  # Pour obtenir l'ID
        
        # Écriture au débit (caisse)
        ecriture_debit = ComptaEcritures(
            journal_id=journal.id,
            compte_comptable_id=config.compte_caisse.id,
            debit=500.00,
            credit=0.00,
            ordre=1,
            libelle="Encaissement vente de services"
        )
        session.add(ecriture_debit)
        
        # Écriture au crédit (vente)
        ecriture_credit = ComptaEcritures(
            journal_id=journal.id,
            compte_comptable_id=config.compte_vente.id,
            debit=0.00,
            credit=500.00,
            ordre=2,
            libelle="Vente de services"
        )
        session.add(ecriture_credit)
        
        session.commit()
        
        print(f"✅ Transaction créée avec succès:")
        print(f"   📝 Journal ID: {journal.id}")
        print(f"   💰 Montant: {journal.montant} USD")
        print(f"   📅 Date: {journal.date_operation}")
        print(f"   📋 Libellé: {journal.libelle}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la transaction: {e}")
        return False

def main():
    print("🧮 Test du Module Comptabilité - Ayanna ERP\n")
    
    # Test 1: Opérations de base
    if not test_basic_accounting_operations():
        return
    
    # Test 2: Création d'une transaction
    if not create_sample_transaction():
        return
    
    print("\n🎉 Tous les tests comptables sont passés avec succès!")
    print("\n💡 Le module comptabilité est prêt à être utilisé dans Ayanna ERP")

if __name__ == "__main__":
    main()
