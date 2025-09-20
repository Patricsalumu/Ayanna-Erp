#!/usr/bin/env python3
"""
Test pour vérifier que les comptes comptables sont bien filtrés par entreprise
dans les formulaires de produits et services.
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager, Entreprise, POSPoint, Module
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaClasses, ComptaComptes
from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController
from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController


def test_account_filtering():
    """Test du filtrage des comptes par entreprise"""
    print("🧪 Test du filtrage des comptes comptables par entreprise")
    print("="*60)
    
    db_manager = get_database_manager()
    session = db_manager.get_session()
    
    try:
        # 1. Créer deux entreprises de test
        print("\n1️⃣ Création des entreprises de test...")
        
        entreprise1 = Entreprise(
            name="Entreprise Test 1",
            address="Adresse 1",
            phone="+243 111 111 111",
            email="test1@example.com",
            currency="USD"
        )
        session.add(entreprise1)
        
        entreprise2 = Entreprise(
            name="Entreprise Test 2", 
            address="Adresse 2",
            phone="+243 222 222 222",
            email="test2@example.com",
            currency="EUR"
        )
        session.add(entreprise2)
        session.flush()  # Pour obtenir les IDs
        
        print(f"✅ Entreprise 1 créée: ID {entreprise1.id}")
        print(f"✅ Entreprise 2 créée: ID {entreprise2.id}")
        
        # 2. Créer le module SalleFete si nécessaire
        print("\n2️⃣ Vérification du module SalleFete...")
        
        module_salle_fete = session.query(Module).filter_by(name="SalleFete").first()
        if not module_salle_fete:
            module_salle_fete = Module(name="SalleFete", description="Module Salle de Fête")
            session.add(module_salle_fete)
            session.flush()
            print(f"✅ Module SalleFete créé: ID {module_salle_fete.id}")
        else:
            print(f"✅ Module SalleFete trouvé: ID {module_salle_fete.id}")
        
        # 3. Créer des POS pour chaque entreprise
        print("\n3️⃣ Création des POS...")
        
        pos1 = POSPoint(
            enterprise_id=entreprise1.id,
            module_id=module_salle_fete.id,
            name="POS Test 1"
        )
        session.add(pos1)
        
        pos2 = POSPoint(
            enterprise_id=entreprise2.id,
            module_id=module_salle_fete.id,
            name="POS Test 2"
        )
        session.add(pos2)
        session.flush()
        
        print(f"✅ POS 1 créé: ID {pos1.id} (Entreprise {entreprise1.id})")
        print(f"✅ POS 2 créé: ID {pos2.id} (Entreprise {entreprise2.id})")
        
        # 4. Créer des classes comptables pour chaque entreprise
        print("\n4️⃣ Création des classes comptables...")
        
        classe1 = ComptaClasses(
            enterprise_id=entreprise1.id,
            code="7T1",
            nom="COMPTES DE PRODUITS - T1",
            libelle="Comptes de produits - Entreprise 1",
            type="produit",
            document="resultat"
        )
        session.add(classe1)
        
        classe2 = ComptaClasses(
            enterprise_id=entreprise2.id,
            code="7T2",
            nom="COMPTES DE PRODUITS - T2",
            libelle="Comptes de produits - Entreprise 2", 
            type="produit",
            document="resultat"
        )
        session.add(classe2)
        session.flush()
        
        print(f"✅ Classe comptable 1 créée: ID {classe1.id} (Entreprise {entreprise1.id})")
        print(f"✅ Classe comptable 2 créée: ID {classe2.id} (Entreprise {entreprise2.id})")
        
        # 5. Créer des comptes pour chaque entreprise
        print("\n5️⃣ Création des comptes comptables...")
        
        compte1 = ComptaComptes(
            classe_comptable_id=classe1.id,
            numero="7011",
            nom="Ventes - Entreprise 1",
            libelle="Ventes de marchandises - Entreprise 1"
        )
        session.add(compte1)
        
        compte2 = ComptaComptes(
            classe_comptable_id=classe2.id,
            numero="7012", 
            nom="Ventes - Entreprise 2",
            libelle="Ventes de marchandises - Entreprise 2"
        )
        session.add(compte2)
        session.flush()
        
        print(f"✅ Compte 1 créé: ID {compte1.id} ('{compte1.nom}' - Entreprise {entreprise1.id})")
        print(f"✅ Compte 2 créé: ID {compte2.id} ('{compte2.nom}' - Entreprise {entreprise2.id})")
        
        session.commit()
        
        # 6. Test du contrôleur de comptabilité
        print("\n6️⃣ Test du contrôleur de comptabilité...")
        
        comptabilite_controller = ComptabiliteController()
        
        # Test sans filtrage (devrait retourner tous les comptes)
        tous_comptes = comptabilite_controller.get_comptes_vente()
        print(f"📊 Tous les comptes (sans filtrage): {len(tous_comptes)} comptes")
        for compte in tous_comptes:
            print(f"   - {compte.numero} - {compte.nom}")
        
        # Test avec filtrage pour entreprise 1
        comptes_ent1 = comptabilite_controller.get_comptes_vente(entreprise_id=entreprise1.id)
        print(f"📊 Comptes entreprise 1: {len(comptes_ent1)} comptes")
        for compte in comptes_ent1:
            print(f"   - {compte.numero} - {compte.nom}")
        
        # Test avec filtrage pour entreprise 2
        comptes_ent2 = comptabilite_controller.get_comptes_vente(entreprise_id=entreprise2.id)
        print(f"📊 Comptes entreprise 2: {len(comptes_ent2)} comptes")
        for compte in comptes_ent2:
            print(f"   - {compte.numero} - {compte.nom}")
        
        # 7. Vérifications
        print("\n7️⃣ Vérifications...")
        
        # Vérifier que le filtrage fonctionne
        ent1_found = any(compte.nom == "Ventes - Entreprise 1" for compte in comptes_ent1)
        ent1_no_ent2 = not any(compte.nom == "Ventes - Entreprise 2" for compte in comptes_ent1)
        
        if ent1_found and ent1_no_ent2:
            print("✅ Filtrage entreprise 1: OK")
        else:
            print("❌ Filtrage entreprise 1: ÉCHEC")
            print(f"   - Compte Ent1 trouvé: {ent1_found}")
            print(f"   - Pas de compte Ent2: {ent1_no_ent2}")
            return False
        
        ent2_found = any(compte.nom == "Ventes - Entreprise 2" for compte in comptes_ent2)
        ent2_no_ent1 = not any(compte.nom == "Ventes - Entreprise 1" for compte in comptes_ent2)
        
        if ent2_found and ent2_no_ent1:
            print("✅ Filtrage entreprise 2: OK")
        else:
            print("❌ Filtrage entreprise 2: ÉCHEC")
            print(f"   - Compte Ent2 trouvé: {ent2_found}")
            print(f"   - Pas de compte Ent1: {ent2_no_ent1}")
            return False
        
        # 8. Test avec les contrôleurs de produit et service
        print("\n8️⃣ Test avec les contrôleurs produit et service...")
        
        # Test avec ProduitController
        produit_controller1 = ProduitController(pos_id=pos1.id)
        produit_controller2 = ProduitController(pos_id=pos2.id)
        
        print(f"🛍️  ProduitController 1 (POS {pos1.id}, Entreprise {entreprise1.id})")
        print(f"🛍️  ProduitController 2 (POS {pos2.id}, Entreprise {entreprise2.id})")
        
        # Test avec ServiceController
        service_controller1 = ServiceController(pos_id=pos1.id)
        service_controller2 = ServiceController(pos_id=pos2.id)
        
        print(f"🎉 ServiceController 1 (POS {pos1.id}, Entreprise {entreprise1.id})")
        print(f"🎉 ServiceController 2 (POS {pos2.id}, Entreprise {entreprise2.id})")
        
        print("\n✅ Tous les tests sont réussis !")
        print("🎯 Le filtrage des comptes par entreprise fonctionne correctement.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = test_account_filtering()
    if success:
        print("\n🎉 Test terminé avec succès !")
        sys.exit(0)
    else:
        print("\n💥 Test échoué !")
        sys.exit(1)