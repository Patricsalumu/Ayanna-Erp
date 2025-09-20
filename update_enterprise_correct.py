"""
Mise à jour de l'entreprise avec les bonnes colonnes de la base de données
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager, Entreprise

def update_enterprise_correct():
    """Mise à jour avec les bonnes colonnes"""
    print("=== Mise à jour entreprise avec bonnes colonnes ===")
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Récupérer l'entreprise
        enterprise = session.query(Entreprise).filter(Entreprise.id == 1).first()
        
        if enterprise:
            print(f"Entreprise avant mise à jour:")
            print(f"  - ID: {enterprise.id}")
            print(f"  - Name: {enterprise.name}")
            print(f"  - Email: {enterprise.email}")
            print(f"  - Phone: {enterprise.phone}")
            
            # Mettre à jour avec les vraies colonnes
            enterprise.name = 'Ayanna Solutions'
            enterprise.address = '123 Avenue de la Technologie, Kinshasa'
            enterprise.phone = '+243 123 456 789'
            enterprise.email = 'contact@ayanna.com'
            enterprise.rccm = 'CD/KIN/RCCM/23-B-5678'
            enterprise.id_nat = 'A123456789'
            enterprise.slogan = 'Solutions ERP intégrées pour votre entreprise'
            enterprise.currency = 'USD'
            
            # Sauvegarder
            session.commit()
            print("✓ Entreprise mise à jour avec succès!")
            
            # Vérifier
            session.refresh(enterprise)
            print(f"\nEntreprise après mise à jour:")
            print(f"  - Name: {enterprise.name}")
            print(f"  - Address: {enterprise.address}")
            print(f"  - Phone: {enterprise.phone}")
            print(f"  - Email: {enterprise.email}")
            print(f"  - RCCM: {enterprise.rccm}")
            print(f"  - Slogan: {enterprise.slogan}")
            
        else:
            print("✗ Entreprise non trouvée")
            
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_enterprise_correct()