#!/usr/bin/env python3
"""
Script pour configurer les comptes comptables des services et produits
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import EventService, EventProduct
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes

def configurer_comptes_services_produits():
    """Configure les comptes comptables pour les services et produits"""
    print("=== Configuration des comptes comptables ===")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # 1. Récupérer des comptes de vente (classe 7) pour assigner aux services/produits
        print("\n1. Récupération des comptes de vente disponibles...")
        comptes_vente = session.query(ComptaComptes).join(ComptaComptes.classe_comptable).filter(
            ComptaComptes.classe_comptable.has(code='7')
        ).all()
        
        if not comptes_vente:
            print("   ❌ Aucun compte de vente (classe 7) trouvé")
            print("   Vous devez d'abord créer des comptes de vente dans la comptabilité")
            return
        
        print(f"   ✅ {len(comptes_vente)} comptes de vente trouvés:")
        for compte in comptes_vente:
            print(f"      - {compte.numero}: {compte.nom} (ID: {compte.id})")
        
        # Choisir un compte par défaut (le premier)
        compte_par_defaut = comptes_vente[0]
        print(f"\n   Utilisation du compte par défaut: {compte_par_defaut.numero} - {compte_par_defaut.nom}")
        
        # 2. Configurer les services sans compte
        print(f"\n2. Configuration des services...")
        services_sans_compte = session.query(EventService).filter(
            (EventService.account_id.is_(None)) | (EventService.account_id == 0)
        ).all()
        
        if services_sans_compte:
            print(f"   {len(services_sans_compte)} services sans compte trouvés:")
            for service in services_sans_compte:
                print(f"      - Service: {service.name}")
                service.account_id = compte_par_defaut.id
                print(f"        ✅ Assigné au compte {compte_par_defaut.numero}")
        else:
            print("   ✅ Tous les services ont déjà un compte assigné")
        
        # 3. Configurer les produits sans compte
        print(f"\n3. Configuration des produits...")
        produits_sans_compte = session.query(EventProduct).filter(
            (EventProduct.account_id.is_(None)) | (EventProduct.account_id == 0)
        ).all()
        
        if produits_sans_compte:
            print(f"   {len(produits_sans_compte)} produits sans compte trouvés:")
            for produit in produits_sans_compte:
                print(f"      - Produit: {produit.name}")
                produit.account_id = compte_par_defaut.id
                print(f"        ✅ Assigné au compte {compte_par_defaut.numero}")
        else:
            print("   ✅ Tous les produits ont déjà un compte assigné")
        
        # 4. Sauvegarder les modifications
        session.commit()
        print(f"\n✅ Configuration sauvegardée avec succès!")
        
        # 5. Vérification finale
        print(f"\n4. Vérification finale...")
        services_total = session.query(EventService).count()
        services_avec_compte = session.query(EventService).filter(EventService.account_id.isnot(None)).count()
        
        produits_total = session.query(EventProduct).count()
        produits_avec_compte = session.query(EventProduct).filter(EventProduct.account_id.isnot(None)).count()
        
        print(f"   Services: {services_avec_compte}/{services_total} avec compte configuré")
        print(f"   Produits: {produits_avec_compte}/{produits_total} avec compte configuré")
        
        if services_avec_compte == services_total and produits_avec_compte == produits_total:
            print(f"   ✅ Tous les services et produits ont un compte configuré!")
            print(f"\n🎉 La répartition des paiements devrait maintenant fonctionner correctement!")
        else:
            print(f"   ⚠️  Certains services/produits n'ont toujours pas de compte")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    configurer_comptes_services_produits()