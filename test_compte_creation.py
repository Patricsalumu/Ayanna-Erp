#!/usr/bin/env python3
"""
Test de création d'un compte après suppression de enterprise_id
"""
import sys
sys.path.insert(0, '.')

from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController

print("🔍 Test de création d'un compte sans enterprise_id...")

try:
    from ayanna_erp.database.database_manager import DatabaseManager
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    # Récupérer une classe comptable existante
    from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaClasses, ComptaComptes
    classe = session.query(ComptaClasses).first()
    
    if not classe:
        print("❌ Aucune classe comptable trouvée")
        exit()
    
    print(f"✅ Classe trouvée: {classe.code} - {classe.nom}")
    
    # Données du nouveau compte
    data = {
        "numero": "5002",
        "nom": "Caisse Point de Vente",
        "libelle": "Caisse pour point de vente principal",
        "classe_comptable_id": classe.id
    }
    
    # Créer le compte directement
    compte = ComptaComptes(
        numero=data["numero"],
        nom=data["nom"],
        libelle=data["libelle"],
        classe_comptable_id=data["classe_comptable_id"]
    )
    session.add(compte)
    session.commit()
    compte_id = compte.id
    print(f"✅ Compte créé avec succès! ID: {compte_id}")
    
    # Vérifier que le compte a été créé
    compte_verifie = session.query(ComptaComptes).filter_by(id=compte_id).first()
    
    if compte_verifie:
        print(f"✅ Vérification: Compte {compte_verifie.numero} - {compte_verifie.nom}")
        print(f"✅ Classe comptable: {compte_verifie.classe_comptable.code} - {compte_verifie.classe_comptable.nom}")
        print(f"✅ Enterprise ID via relation: {compte_verifie.classe_comptable.enterprise_id}")
    else:
        print("❌ Compte non trouvé après création")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
