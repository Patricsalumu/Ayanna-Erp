"""
Utilitaires pour la gestion du module Boutique
"""

from ayanna_erp.database.database_manager import DatabaseManager, Module


def check_boutique_module_status():
    """Vérifier le statut du module Boutique dans la base de données"""
    
    db_manager = DatabaseManager()
    
    try:
        session = db_manager.get_session()
        
        # Vérifier si le module Boutique existe
        boutique_module = session.query(Module).filter(Module.name == "Boutique").first()
        
        if boutique_module:
            print("✅ Module Boutique trouvé dans la base de données:")
            print(f"   ID: {boutique_module.id}")
            print(f"   Nom: {boutique_module.name}")
            print(f"   Description: {boutique_module.description}")
            print(f"   Actif: {'Oui' if boutique_module.is_active else 'Non'}")
            return True
        else:
            print("❌ Module Boutique non trouvé dans la base de données")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    finally:
        session.close()


def list_all_modules():
    """Lister tous les modules dans la base de données"""
    
    db_manager = DatabaseManager()
    
    try:
        session = db_manager.get_session()
        
        modules = session.query(Module).all()
        
        print(f"\n📋 Modules enregistrés ({len(modules)}):")
        print("-" * 50)
        
        for module in modules:
            status = "✅ Actif" if module.is_active else "❌ Inactif"
            print(f"  {module.id:2d}. {module.name:15s} - {status}")
            if module.description:
                print(f"      Description: {module.description[:60]}...")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des modules: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("🔍 Vérification du statut du module Boutique...\n")
    
    # Vérifier le module Boutique
    check_boutique_module_status()
    
    # Lister tous les modules
    list_all_modules()