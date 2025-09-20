"""
Script pour corriger les données de l'entreprise par défaut
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def fix_enterprise_data():
    """Corriger les données de l'entreprise par défaut"""
    print("=== Correction des données entreprise ===")
    
    controller = EntrepriseController()
    
    # Récupérer l'entreprise actuelle
    enterprise = controller.get_current_enterprise(1)
    
    if enterprise:
        print(f"Entreprise actuelle:")
        print(f"  - ID: {enterprise.get('id')}")
        print(f"  - Nom: {enterprise.get('nom')}")
        print(f"  - Description: {enterprise.get('description')}")
        print(f"  - Email: {enterprise.get('email')}")
        
        # Données à mettre à jour
        updated_data = {
            'nom': enterprise.get('nom') or 'Ayanna Solutions',
            'description': enterprise.get('description') or 'Entreprise de gestion ERP intégrée',
            'secteur_activite': enterprise.get('secteur_activite') or 'Technologies de l\'information',
            'adresse': enterprise.get('adresse') or '123 Avenue de la Technologie',
            'ville': enterprise.get('ville') or 'Kinshasa',
            'code_postal': enterprise.get('code_postal') or '12345',
            'pays': enterprise.get('pays') or 'République Démocratique du Congo',
            'email': enterprise.get('email') or 'contact@ayanna.com',
            'telephone': enterprise.get('telephone') or '+243 123 456 789',
            'site_web': enterprise.get('site_web') or 'www.ayanna.com'
        }
        
        print(f"\nMise à jour des données...")
        
        try:
            # Mettre à jour l'entreprise
            if hasattr(controller, 'update_enterprise'):
                result = controller.update_enterprise(1, updated_data)
                if result:
                    print("✓ Entreprise mise à jour avec succès!")
                else:
                    print("✗ Échec de la mise à jour")
            else:
                # Simulation directe de mise à jour dans la DB
                from ayanna_erp.database.database_manager import DatabaseManager, Entreprise
                
                db_manager = DatabaseManager()
                session = db_manager.get_session()
                
                enterprise_db = session.query(Entreprise).filter(Entreprise.id == 1).first()
                if enterprise_db:
                    for key, value in updated_data.items():
                        setattr(enterprise_db, key, value)
                    
                    session.commit()
                    print("✓ Entreprise mise à jour directement dans la DB!")
                else:
                    print("✗ Entreprise non trouvée dans la DB")
                
        except Exception as e:
            print(f"✗ Erreur lors de la mise à jour: {e}")
        
        # Vérifier la mise à jour
        print(f"\nVérification...")
        updated_enterprise = controller.get_current_enterprise(1)
        if updated_enterprise:
            print(f"✓ Entreprise après mise à jour:")
            print(f"  - Nom: {updated_enterprise.get('nom')}")
            print(f"  - Description: {updated_enterprise.get('description')}")
            print(f"  - Ville: {updated_enterprise.get('ville')}")
        
    else:
        print("✗ Aucune entreprise trouvée")

if __name__ == "__main__":
    fix_enterprise_data()