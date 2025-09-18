#!/usr/bin/env python3
"""
Script pour créer des comptes TVA de test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaClasses, ComptaComptes

def create_tva_accounts():
    """Créer des comptes TVA de test"""
    print("=== Création de comptes TVA de test ===")
    
    controller = ComptabiliteController()
    enterprise_id = 1
    
    try:
        # 1. Vérifier si la classe 44 existe
        classe_44 = controller.session.query(ComptaClasses).filter_by(
            enterprise_id=enterprise_id, 
            code="44"
        ).first()
        
        if not classe_44:
            print("Création de la classe 44 (État et autres collectivités publiques)...")
            classe_44 = ComptaClasses(
                enterprise_id=enterprise_id,
                code="44",
                nom="État et autres collectivités publiques",
                libelle="Comptes de TVA et autres taxes",
                type="passif",
                document="bilan"
            )
            controller.session.add(classe_44)
            controller.session.commit()
            print("✅ Classe 44 créée")
        else:
            print("✅ Classe 44 déjà existante")
        
        # 2. Créer quelques comptes TVA
        comptes_tva = [
            ("445", "TVA à décaisser", "TVA collectée sur ventes"),
            ("4456", "TVA déductible", "TVA déductible sur achats"),
            ("4457", "TVA à régulariser", "Compte de régularisation TVA")
        ]
        
        for numero, nom, description in comptes_tva:
            # Vérifier si le compte existe déjà
            compte_existant = controller.session.query(ComptaComptes).filter_by(
                numero=numero
            ).first()
            
            if not compte_existant:
                print(f"Création du compte {numero} - {nom}...")
                compte = ComptaComptes(
                    classe_comptable_id=classe_44.id,
                    numero=numero,
                    nom=nom,
                    libelle=description,
                    actif=True
                )
                controller.session.add(compte)
            else:
                print(f"✅ Compte {numero} déjà existant")
        
        controller.session.commit()
        print("\n✅ Comptes TVA créés avec succès!")
        
        # 3. Vérifier les comptes créés
        print("\n=== Vérification des comptes TVA ===")
        comptes_tva = controller.get_comptes_par_classe(enterprise_id, '44')
        for compte in comptes_tva:
            print(f"   - {compte.numero}: {compte.nom}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tva_accounts()