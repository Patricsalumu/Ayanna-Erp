"""
Mise à jour directe de l'entreprise dans la base de données
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager, Entreprise

def update_enterprise_direct():
    """Mise à jour directe de l'entreprise"""
    print("=== Mise à jour directe de l'entreprise ===")
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Récupérer l'entreprise
        enterprise = session.query(Entreprise).filter(Entreprise.id == 1).first()
        
        if enterprise:
            print(f"Entreprise avant mise à jour:")
            print(f"  - ID: {enterprise.id}")
            print(f"  - Nom: {enterprise.nom}")
            print(f"  - Email: {enterprise.email}")
            
            # Mettre à jour les champs
            enterprise.nom = 'Ayanna Solutions'
            enterprise.description = 'Entreprise de gestion ERP intégrée'
            enterprise.secteur_activite = 'Technologies de l\'information'
            enterprise.adresse = '123 Avenue de la Technologie'
            enterprise.ville = 'Kinshasa'
            enterprise.code_postal = '12345'
            enterprise.pays = 'République Démocratique du Congo'
            enterprise.telephone = '+243 123 456 789'
            enterprise.site_web = 'www.ayanna.com'
            
            # Sauvegarder
            session.commit()
            print("✓ Entreprise mise à jour avec succès!")
            
            # Vérifier
            session.refresh(enterprise)
            print(f"\nEntreprise après mise à jour:")
            print(f"  - Nom: {enterprise.nom}")
            print(f"  - Description: {enterprise.description}")
            print(f"  - Ville: {enterprise.ville}")
            print(f"  - Téléphone: {enterprise.telephone}")
            
        else:
            print("✗ Entreprise non trouvée")
            
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_enterprise_direct()