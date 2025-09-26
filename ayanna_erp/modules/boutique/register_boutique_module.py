"""
Script pour enregistrer le module Boutique dans la base de données
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin du projet pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ayanna_erp.database.database_manager import DatabaseManager

def register_boutique_module():
    """Enregistre le module Boutique dans la base de données"""
    
    try:
        # Connexion à la base de données
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Vérifier si le module existe déjà
        from sqlalchemy.sql import text
        
        # Vérifier l'existence du module
        result = session.execute(text("SELECT * FROM modules WHERE nom = 'Boutique'"))
        existing_module = result.fetchone()
        
        if existing_module:
            print("✅ Le module Boutique est déjà enregistré")
            session.close()
            return True
            
        # Enregistrer le module
        insert_query = text("""
            INSERT INTO modules (nom, description, version, statut, date_creation) 
            VALUES (:nom, :description, :version, :statut, :date_creation)
        """)
        
        session.execute(insert_query, {
            'nom': 'Boutique',
            'description': 'Module de gestion de boutique et point de vente avec catalogue produits, gestion panier, paiements multiples et rapports détaillés',
            'version': '1.0.0',
            'statut': 'actif',
            'date_creation': datetime.now()
        })
        
        session.commit()
        session.close()
        
        print("✅ Module Boutique enregistré avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement du module: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    success = register_boutique_module()
    if success:
        print("🎉 Enregistrement terminé avec succès")
    else:
        print("💥 Enregistrement échoué")