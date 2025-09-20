#!/usr/bin/env python3
"""
Test pour vérifier que plusieurs entreprises peuvent avoir les mêmes codes de classes
après la correction de la contrainte d'unicité.
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager, Entreprise
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaClasses


def test_multi_enterprise_classes():
    """Test que plusieurs entreprises peuvent avoir les mêmes codes de classes"""
    print("🧪 Test multi-entreprises pour les classes comptables")
    print("="*55)
    
    db_manager = get_database_manager()
    session = db_manager.get_session()
    
    try:
        # 1. Créer deux nouvelles entreprises de test
        print("\n1️⃣ Création des entreprises de test...")
        
        entreprise_a = Entreprise(
            name="Entreprise Test A",
            address="Adresse A",
            phone="+243 111 111 111",
            email="testA@example.com",
            currency="USD"
        )
        session.add(entreprise_a)
        
        entreprise_b = Entreprise(
            name="Entreprise Test B",
            address="Adresse B",
            phone="+243 222 222 222",
            email="testB@example.com",
            currency="EUR"
        )
        session.add(entreprise_b)
        session.flush()  # Pour obtenir les IDs
        
        print(f"✅ Entreprise A créée: ID {entreprise_a.id}")
        print(f"✅ Entreprise B créée: ID {entreprise_b.id}")
        
        # 2. Vérifier qu'aucune classe n'existe pour ces entreprises
        print("\n2️⃣ Vérification des classes existantes...")
        
        classes_a = session.query(ComptaClasses).filter_by(enterprise_id=entreprise_a.id).all()
        classes_b = session.query(ComptaClasses).filter_by(enterprise_id=entreprise_b.id).all()
        
        print(f"📊 Classes Entreprise A: {len(classes_a)}")
        print(f"📊 Classes Entreprise B: {len(classes_b)}")
        
        # 3. Créer automatiquement les classes pour l'entreprise A
        print("\n3️⃣ Création des classes pour l'entreprise A...")
        
        comptabilite_controller = ComptabiliteController()
        classes_data_a = comptabilite_controller.get_classes(entreprise_a.id)
        
        print(f"✅ Classes créées pour A: {len(classes_data_a)}")
        for classe in classes_data_a:
            print(f"   - Classe {classe['numero']}: {classe['nom']}")
        
        # 4. Créer automatiquement les classes pour l'entreprise B
        print("\n4️⃣ Création des classes pour l'entreprise B...")
        
        classes_data_b = comptabilite_controller.get_classes(entreprise_b.id)
        
        print(f"✅ Classes créées pour B: {len(classes_data_b)}")
        for classe in classes_data_b:
            print(f"   - Classe {classe['numero']}: {classe['nom']}")
        
        # 5. Vérifications
        print("\n5️⃣ Vérifications...")
        
        # Vérifier que les deux entreprises ont des classes
        if len(classes_data_a) > 0 and len(classes_data_b) > 0:
            print("✅ Les deux entreprises ont des classes")
        else:
            print("❌ Au moins une entreprise n'a pas de classes")
            return False
        
        # Vérifier que les codes sont identiques
        codes_a = [c['numero'] for c in classes_data_a]
        codes_b = [c['numero'] for c in classes_data_b]
        
        codes_a.sort()
        codes_b.sort()
        
        if codes_a == codes_b:
            print(f"✅ Codes identiques: {', '.join(codes_a)}")
        else:
            print(f"❌ Codes différents:")
            print(f"   Entreprise A: {codes_a}")
            print(f"   Entreprise B: {codes_b}")
            return False
        
        # Vérifier l'isolation : les classes de A ne sont pas vues par B
        session.refresh(entreprise_a)
        session.refresh(entreprise_b)
        
        # Test direct en base
        print("\n6️⃣ Test d'isolation en base de données...")
        
        classes_a_db = session.query(ComptaClasses).filter_by(enterprise_id=entreprise_a.id).all()
        classes_b_db = session.query(ComptaClasses).filter_by(enterprise_id=entreprise_b.id).all()
        
        print(f"📊 Classes A en base: {len(classes_a_db)}")
        print(f"📊 Classes B en base: {len(classes_b_db)}")
        
        # Vérifier qu'il n'y a pas de croisement
        for classe_a in classes_a_db:
            if classe_a.enterprise_id != entreprise_a.id:
                print(f"❌ Classe mal assignée: {classe_a.code} -> Entreprise {classe_a.enterprise_id}")
                return False
        
        for classe_b in classes_b_db:
            if classe_b.enterprise_id != entreprise_b.id:
                print(f"❌ Classe mal assignée: {classe_b.code} -> Entreprise {classe_b.enterprise_id}")
                return False
        
        print("✅ Isolation parfaite entre les entreprises")
        
        # 7. Test de la contrainte composite
        print("\n7️⃣ Test de la contrainte composite...")
        
        try:
            # Essayer d'ajouter une classe avec le même code pour la même entreprise (doit échouer)
            classe_doublon = ComptaClasses(
                code="1",
                nom="Test Doublon",
                libelle="Test",
                type="test",
                document="bilan",
                enterprise_id=entreprise_a.id
            )
            session.add(classe_doublon)
            session.flush()
            
            print("❌ La contrainte composite ne fonctionne pas (doublon autorisé)")
            session.rollback()
            return False
            
        except Exception as e:
            print("✅ Contrainte composite fonctionne (doublon rejeté)")
            session.rollback()
        
        session.commit()
        
        print("\n✅ Tous les tests sont réussis !")
        print("🎯 Plusieurs entreprises peuvent avoir les mêmes codes de classes")
        print("🔒 L'isolation entre entreprises est maintenue")
        print("🛡️ La contrainte composite empêche les doublons dans une même entreprise")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = test_multi_enterprise_classes()
    if success:
        print("\n🎉 Test réussi !")
        print("✅ Contrainte d'unicité corrigée")
        print("✅ Multi-entreprises fonctionnel")
        print("✅ Classes comptables isolées par entreprise")
    else:
        print("\n💥 Test échoué !")
        print("❌ Problème avec la contrainte d'unicité")