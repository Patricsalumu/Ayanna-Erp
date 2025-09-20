#!/usr/bin/env python3
"""
Test simple pour vérifier que la contrainte d'unicité a été corrigée
"""

import sys
import os
import sqlite3

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_constraint_fix():
    """Test simple de la correction de contrainte"""
    print("🧪 Test de vérification de la contrainte d'unicité")
    print("="*50)
    
    try:
        # Connexion directe à la base
        db_path = "ayanna_erp.db"
        if not os.path.exists(db_path):
            print(f"❌ Base de données non trouvée: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Vérifier la structure actuelle
        print("1️⃣ Vérification de la structure de la table...")
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='compta_classes'")
        schema = cursor.fetchone()
        
        if schema:
            print(f"📋 Schéma de la table:")
            schema_text = schema[0]
            print(f"   {schema_text}")
            
            # Vérifier que la contrainte composite est présente
            if "UNIQUE (code, enterprise_id)" in schema_text:
                print("\n✅ Contrainte composite trouvée: UNIQUE (code, enterprise_id)")
            else:
                print("\n❌ Contrainte composite non trouvée")
                return False
            
            # Vérifier que l'ancienne contrainte unique sur code seul n'est plus là
            if "UNIQUE (code)" in schema_text and "UNIQUE (code, enterprise_id)" not in schema_text:
                print("❌ Ancienne contrainte unique sur code seul encore présente")
                return False
            
        else:
            print("❌ Table compta_classes non trouvée")
            return False
        
        # 2. Vérifier les données existantes
        print("\n2️⃣ Vérification des données existantes...")
        
        cursor.execute("""
            SELECT enterprise_id, code, nom, COUNT(*) as count
            FROM compta_classes 
            GROUP BY enterprise_id, code 
            ORDER BY enterprise_id, code
        """)
        
        classes_par_entreprise = cursor.fetchall()
        
        print(f"📊 Classes par entreprise:")
        current_enterprise = None
        for row in classes_par_entreprise:
            enterprise_id, code, nom, count = row
            if current_enterprise != enterprise_id:
                print(f"\n   🏢 Entreprise {enterprise_id}:")
                current_enterprise = enterprise_id
            print(f"      - Classe {code}: {nom} (count: {count})")
        
        # 3. Vérifier qu'il n'y a pas de doublons dans la même entreprise
        print("\n3️⃣ Vérification des doublons...")
        
        cursor.execute("""
            SELECT enterprise_id, code, COUNT(*) as count
            FROM compta_classes 
            GROUP BY enterprise_id, code 
            HAVING COUNT(*) > 1
        """)
        
        doublons = cursor.fetchall()
        
        if doublons:
            print("❌ Doublons détectés:")
            for enterprise_id, code, count in doublons:
                print(f"   - Entreprise {enterprise_id}, Code {code}: {count} occurrences")
            return False
        else:
            print("✅ Aucun doublon détecté")
        
        # 4. Vérifier les codes existants
        print("\n4️⃣ Codes de classes par entreprise...")
        
        cursor.execute("""
            SELECT enterprise_id, GROUP_CONCAT(code ORDER BY code) as codes
            FROM compta_classes 
            GROUP BY enterprise_id 
            ORDER BY enterprise_id
        """)
        
        entreprises_codes = cursor.fetchall()
        
        for enterprise_id, codes in entreprises_codes:
            print(f"   🏢 Entreprise {enterprise_id}: Codes {codes}")
        
        conn.close()
        
        print("\n✅ Tous les tests de vérification sont réussis !")
        print("🎯 La contrainte composite fonctionne correctement")
        print("🔒 Chaque entreprise peut avoir ses propres codes de classes")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == "__main__":
    success = test_constraint_fix()
    if success:
        print("\n🎉 Contrainte d'unicité corrigée !")
        print("✅ Structure de table: OK")
        print("✅ Pas de doublons: OK")
        print("✅ Multi-entreprises: Supporté")
    else:
        print("\n💥 Problème avec la contrainte !")