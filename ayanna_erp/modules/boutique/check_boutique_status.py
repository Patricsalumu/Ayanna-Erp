"""
Script pour vérifier le statut du module Boutique
"""

import sys
import os

# Ajouter le chemin du projet pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ayanna_erp.database.database_manager import DatabaseManager

def check_boutique_status():
    """Vérifie le statut du module Boutique"""
    
    status = {
        'module_registered': False,
        'database_tables_exist': False,
        'default_data_exists': False,
        'errors': []
    }
    
    try:
        # Connexion à la base de données
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # 1. Vérifier l'enregistrement du module
        from sqlalchemy.sql import text
        
        result = session.execute(text("SELECT * FROM modules WHERE nom = 'Boutique'"))
        module = result.fetchone()
        
        if module:
            status['module_registered'] = True
            print("✅ Module Boutique enregistré")
        else:
            print("❌ Module Boutique non enregistré")
            
        # 2. Vérifier l'existence des tables
        try:
            from ayanna_erp.modules.boutique.model.models import (
                ShopCategory, ShopProduct, ShopService, ShopClient
            )
            
            # Tester une requête simple pour voir si les tables existent
            categories_count = session.query(ShopCategory).count()
            status['database_tables_exist'] = True
            print("✅ Tables de la base de données créées")
            
            # 3. Vérifier les données par défaut
            if categories_count > 0:
                status['default_data_exists'] = True
                print("✅ Données par défaut présentes")
            else:
                print("⚠️  Données par défaut manquantes")
                
        except Exception as e:
            status['errors'].append(f"Erreur tables: {str(e)}")
            print(f"❌ Erreur avec les tables: {e}")
            
        session.close()
        
    except Exception as e:
        status['errors'].append(f"Erreur générale: {str(e)}")
        print(f"❌ Erreur générale: {e}")
        
    return status

def print_status_report():
    """Affiche un rapport détaillé du statut"""
    print("="*60)
    print("📊 RAPPORT DE STATUT DU MODULE BOUTIQUE")
    print("="*60)
    
    status = check_boutique_status()
    
    print(f"\n📦 Module enregistré: {'✅ Oui' if status['module_registered'] else '❌ Non'}")
    print(f"🗄️  Tables créées: {'✅ Oui' if status['database_tables_exist'] else '❌ Non'}")
    print(f"📋 Données par défaut: {'✅ Oui' if status['default_data_exists'] else '❌ Non'}")
    
    if status['errors']:
        print(f"\n⚠️  ERREURS DÉTECTÉES:")
        for error in status['errors']:
            print(f"   • {error}")
    else:
        print(f"\n🎉 Aucune erreur détectée")
        
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    if not status['module_registered']:
        print("   1. Exécutez register_boutique_module.py")
    if not status['database_tables_exist']:
        print("   2. Créez les tables avec init_boutique_data.py") 
    if not status['default_data_exists']:
        print("   3. Initialisez les données par défaut")
        
    print("="*60)
    return status

if __name__ == "__main__":
    print_status_report()