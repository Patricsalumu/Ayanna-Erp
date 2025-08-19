#!/usr/bin/env python3
"""
Script de test pour l'initialisation des tables comptables
"""

import sys
import os

# Ajouter les chemins nécessaires
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_comptabilite_models():
    """Tester l'import des modèles comptables"""
    try:
        from ayanna_erp.modules.comptabilite.model.comptabilite import (
            ComptaClasses, ComptaComptes, ComptaJournaux, ComptaEcritures, ComptaConfig
        )
        print("✅ Import des modèles comptables réussi")
        
        # Afficher les tables
        print("\nTables comptables:")
        print(f"- ComptaClasses: {ComptaClasses.__tablename__}")
        print(f"- ComptaComptes: {ComptaComptes.__tablename__}")
        print(f"- ComptaJournaux: {ComptaJournaux.__tablename__}")
        print(f"- ComptaEcritures: {ComptaEcritures.__tablename__}")
        print(f"- ComptaConfig: {ComptaConfig.__tablename__}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_database_initialization():
    """Tester l'initialisation des tables"""
    try:
        from ayanna_erp.database.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Initialiser la base de données
        print("\n🔄 Initialisation de la base de données...")
        success = db_manager.initialize_database()
        
        if success:
            print("✅ Base de données initialisée avec succès!")
            return True
        else:
            print("❌ Échec de l'initialisation de la base de données")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

def main():
    print("=== Test du module Comptabilité ===\n")
    
    # Test 1: Import des modèles
    print("1. Test d'import des modèles comptables:")
    if not test_comptabilite_models():
        return
    
    # Test 2: Initialisation de la base
    print("\n2. Test d'initialisation de la base de données:")
    if not test_database_initialization():
        return
    
    print("\n🎉 Tous les tests sont passés avec succès!")

if __name__ == "__main__":
    main()
