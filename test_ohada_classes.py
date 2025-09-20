#!/usr/bin/env python3
"""
Test pour vérifier la création automatique des 9 classes comptables OHADA
et la correction de l'erreur 'entreprise_id' invalid keyword argument.
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager, Entreprise
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaClasses


def test_ohada_classes_creation():
    """Test de la création automatique des classes OHADA"""
    print("🧪 Test de la création automatique des classes comptables OHADA")
    print("="*65)
    
    db_manager = get_database_manager()
    session = db_manager.get_session()
    
    try:
        # 1. Créer une nouvelle entreprise de test
        print("\n1️⃣ Création d'une entreprise de test...")
        
        entreprise_test = Entreprise(
            name="Entreprise Test OHADA",
            address="Adresse Test",
            phone="+243 999 999 999",
            email="test.ohada@example.com",
            currency="CDF"
        )
        session.add(entreprise_test)
        session.flush()  # Pour obtenir l'ID
        
        print(f"✅ Entreprise créée: ID {entreprise_test.id} - {entreprise_test.name}")
        
        # 2. Vérifier qu'il n'y a pas de classes pour cette entreprise
        print("\n2️⃣ Vérification des classes existantes...")
        
        classes_existantes = session.query(ComptaClasses).filter_by(
            enterprise_id=entreprise_test.id
        ).all()
        
        print(f"📊 Classes existantes pour l'entreprise {entreprise_test.id}: {len(classes_existantes)}")
        
        # 3. Tester le contrôleur de comptabilité
        print("\n3️⃣ Test du contrôleur de comptabilité...")
        
        comptabilite_controller = ComptabiliteController()
        
        # Cette méthode devrait automatiquement créer les 9 classes si elles n'existent pas
        classes_data = comptabilite_controller.get_classes(entreprise_test.id)
        
        print(f"📊 Classes retournées par get_classes(): {len(classes_data)}")
        
        # 4. Vérifier que les 9 classes OHADA ont été créées
        print("\n4️⃣ Vérification des classes créées...")
        
        expected_classes = [
            {"code": "1", "nom": "COMPTES DE RESSOURCES DURABLES"},
            {"code": "2", "nom": "COMPTES D'ACTIF IMMOBILISE"},
            {"code": "3", "nom": "COMPTES DE STOCKS"},
            {"code": "4", "nom": "COMPTES DE TIERS"},
            {"code": "5", "nom": "COMPTES DE TRESORERIE"},
            {"code": "6", "nom": "COMPTES DE CHARGES"},
            {"code": "7", "nom": "COMPTES DE PRODUITS"},
            {"code": "8", "nom": "COMPTES DES AUTRES CHARGES ET DES AUTRES PRODUITS"},
            {"code": "9", "nom": "COMPTES DES RESSOURCES ET EMPLOIS"}
        ]
        
        # Afficher les classes créées
        for i, classe_data in enumerate(classes_data):
            print(f"   {i+1}. Classe {classe_data['numero']}: {classe_data['nom']}")
        
        # 5. Vérifications
        print("\n5️⃣ Vérifications...")
        
        # Vérifier le nombre total
        if len(classes_data) == 9:
            print("✅ Nombre de classes: 9 (correct)")
        else:
            print(f"❌ Nombre de classes: {len(classes_data)} (attendu: 9)")
            return False
        
        # Vérifier que toutes les classes attendues sont présentes
        codes_crees = [c['numero'] for c in classes_data]
        codes_attendus = [c['code'] for c in expected_classes]
        
        manquants = set(codes_attendus) - set(codes_crees)
        en_trop = set(codes_crees) - set(codes_attendus)
        
        if not manquants and not en_trop:
            print("✅ Toutes les classes OHADA sont présentes")
        else:
            if manquants:
                print(f"❌ Classes manquantes: {manquants}")
            if en_trop:
                print(f"❌ Classes en trop: {en_trop}")
            return False
        
        # Vérifier les classes 8 et 9 spécifiquement (nouvellement ajoutées)
        classe_8 = next((c for c in classes_data if c['numero'] == '8'), None)
        classe_9 = next((c for c in classes_data if c['numero'] == '9'), None)
        
        if classe_8:
            print(f"✅ Classe 8 créée: {classe_8['nom']}")
        else:
            print("❌ Classe 8 manquante")
            return False
        
        if classe_9:
            print(f"✅ Classe 9 créée: {classe_9['nom']}")
        else:
            print("❌ Classe 9 manquante")
            return False
        
        # 6. Test de récupération multiple (ne doit pas recréer)
        print("\n6️⃣ Test de récupération multiple...")
        
        classes_data_2 = comptabilite_controller.get_classes(entreprise_test.id)
        
        if len(classes_data_2) == len(classes_data):
            print("✅ Récupération multiple: pas de duplication")
        else:
            print(f"❌ Récupération multiple: duplication détectée ({len(classes_data)} vs {len(classes_data_2)})")
            return False
        
        session.commit()
        
        print("\n✅ Tous les tests sont réussis !")
        print("🎯 La création automatique des classes OHADA fonctionne correctement.")
        print("🔒 Le système respecte l'intégrité du plan comptable OHADA.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def test_error_fix():
    """Test que l'erreur 'entreprise_id' invalid keyword argument est corrigée"""
    print("\n" + "="*65)
    print("🧪 Test de correction de l'erreur 'entreprise_id' invalid keyword")
    print("="*65)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Récupérer une entreprise existante
        entreprise = session.query(Entreprise).first()
        
        if not entreprise:
            print("❌ Aucune entreprise trouvée pour le test")
            return False
        
        print(f"📍 Test avec entreprise: {entreprise.name} (ID: {entreprise.id})")
        
        # Tenter la récupération des classes
        comptabilite_controller = ComptabiliteController()
        classes_data = comptabilite_controller.get_classes(entreprise.id)
        
        print(f"✅ Récupération réussie: {len(classes_data)} classes")
        print("✅ Plus d'erreur 'entreprise_id' invalid keyword argument")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur persistante: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Test complet du système de classes comptables OHADA\n")
    
    # Test de correction de l'erreur
    success1 = test_error_fix()
    
    # Test de création automatique
    success2 = test_ohada_classes_creation()
    
    if success1 and success2:
        print("\n🎉 Tous les tests sont réussis !")
        print("✅ L'erreur 'entreprise_id' est corrigée")
        print("✅ Les 9 classes OHADA sont créées automatiquement")
        print("✅ Le système comptable respecte les standards OHADA")
        sys.exit(0)
    else:
        print("\n💥 Certains tests ont échoué !")
        sys.exit(1)