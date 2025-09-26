"""
Script pour enregistrer le module Boutique dans la base de données
"""

from ayanna_erp.database.database_manager import DatabaseManager, Module


def register_boutique_module():
    """Enregistrer le module Boutique dans la base de données"""
    
    db_manager = DatabaseManager()
    
    try:
        session = db_manager.get_session()
        
        # Vérifier si le module Boutique existe déjà
        existing_module = session.query(Module).filter(Module.name == "Boutique").first()
        
        if existing_module:
            print("✅ Le module Boutique existe déjà dans la base de données.")
            return
        
        # Créer le module Boutique
        boutique_module = Module(
            name="Boutique",
            description="Gestion de la boutique et des ventes - Point de vente avec catalogue produits/services, panier, gestion des stocks et paiements",
            is_active=True
        )
        
        session.add(boutique_module)
        session.commit()
        
        print("✅ Module Boutique enregistré avec succès dans la base de données!")
        print(f"   ID: {boutique_module.id}")
        print(f"   Nom: {boutique_module.name}")
        print(f"   Description: {boutique_module.description}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement du module Boutique: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    register_boutique_module()