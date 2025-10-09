# Test intégration achats-comptabilité
import sys
import os
from datetime import datetime
from decimal import Decimal

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== TEST INTÉGRATION ACHATS-COMPTABILITÉ ===\n")

try:
    from ayanna_erp.database.database_manager import DatabaseManager
    from ayanna_erp.modules.achats.controllers.achat_controller import AchatController
    from sqlalchemy import text
    
    db_manager = DatabaseManager()
    
    # Test de la fonction create_ecriture_comptable_achat
    print("1. Test de la création d'écriture comptable...")
    
    # Créer une instance du controller
    controller = AchatController(entreprise_id=1)
    
    with db_manager.get_session() as session:
        
        # Créer des objets mock pour tester
        class MockFournisseur:
            def __init__(self):
                self.nom = "Fournisseur Test"
        
        class MockCommande:
            def __init__(self):
                self.numero = "CMD-TEST-001"
                self.montant_total = Decimal('150.00')
                self.utilisateur_id = 1
                self.fournisseur = MockFournisseur()
        
        class MockDepense:
            def __init__(self):
                self.compte_id = 3  # Utiliser le compte caisse (ID 3)
                
        # Créer les objets de test
        commande_test = MockCommande()
        depense_test = MockDepense()
        
        print(f"   Commande test: {commande_test.numero} - {commande_test.montant_total}€")
        print(f"   Compte dépense: {depense_test.compte_id}")
        
        # Vérifier que le compte existe
        result = session.execute(text("SELECT numero, nom FROM compta_comptes WHERE id = :id"), 
                                {"id": depense_test.compte_id})
        compte_info = result.fetchone()
        if compte_info:
            print(f"   Compte trouvé: {compte_info[0]} - {compte_info[1]}")
        else:
            print(f"   ❌ Compte {depense_test.compte_id} introuvable!")
        
        # Appeler la fonction
        print("\n2. Appel de create_ecriture_comptable_achat...")
        
        try:
            controller.create_ecriture_comptable_achat(session, commande_test, depense_test)
            
            # Vérifier si des journaux ont été créés
            result = session.execute(text("SELECT COUNT(*) FROM compta_journaux"))
            count_journaux = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM compta_ecritures"))  
            count_ecritures = result.fetchone()[0]
            
            print(f"   Journaux après test: {count_journaux}")
            print(f"   Écritures après test: {count_ecritures}")
            
            if count_journaux > 0:
                print("✅ Écriture comptable créée avec succès!")
                
                # Afficher le détail
                result = session.execute(text("""
                    SELECT j.libelle, j.montant, e.debit, e.credit, c.numero, c.nom
                    FROM compta_journaux j
                    LEFT JOIN compta_ecritures e ON j.id = e.journal_id
                    LEFT JOIN compta_comptes c ON e.compte_comptable_id = c.id
                    WHERE j.reference = 'CMD-TEST-001'
                    ORDER BY e.ordre
                """))
                details = result.fetchall()
                
                print("   Détail des écritures:")
                for detail in details:
                    print(f"     {detail[4]} {detail[5]}: D={detail[2]} C={detail[3]}")
            else:
                print("❌ Aucune écriture créée")
            
            # Rollback pour ne pas polluer la base
            session.rollback()
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()
    
    print("\n" + "="*60)
    print("TEST TERMINÉ")
    print("="*60)
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()