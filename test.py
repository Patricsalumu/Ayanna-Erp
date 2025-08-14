#!/usr/bin/env python3
"""
Script de test pour vérifier l'installation d'Ayanna ERP
"""

import sys
import os
import importlib
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_python_version():
    """Tester la version de Python"""
    print("🐍 Test de la version Python...")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requis: Python 3.8+")
        return False


def test_dependencies():
    """Tester les dépendances"""
    print("\n📦 Test des dépendances...")
    
    dependencies = [
        ("PyQt6", "PyQt6.QtWidgets"),
        ("SQLAlchemy", "sqlalchemy"),
        ("bcrypt", "bcrypt"),
        ("reportlab", "reportlab"),
        ("Pillow", "PIL"),
        ("python-dotenv", "dotenv")
    ]
    
    all_ok = True
    
    for name, module in dependencies:
        try:
            importlib.import_module(module)
            print(f"✅ {name} - OK")
        except ImportError:
            print(f"❌ {name} - MANQUANT")
            all_ok = False
    
    return all_ok


def test_project_structure():
    """Tester la structure du projet"""
    print("\n📁 Test de la structure du projet...")
    
    required_files = [
        "main.py",
        "install.py", 
        "requirements.txt",
        ".env",
        "ayanna_erp/__init__.py",
        "ayanna_erp/database/__init__.py",
        "ayanna_erp/database/database_manager.py",
        "ayanna_erp/ui/__init__.py",
        "ayanna_erp/ui/login_window.py",
        "ayanna_erp/ui/main_window.py",
        "ayanna_erp/modules/__init__.py"
    ]
    
    all_ok = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - OK")
        else:
            print(f"❌ {file_path} - MANQUANT")
            all_ok = False
    
    return all_ok


def test_database():
    """Tester la base de données"""
    print("\n🗄️  Test de la base de données...")
    
    try:
        from ayanna_erp.database.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        if session:
            print("✅ Connexion à la base de données - OK")
            session.close()
            return True
        else:
            print("❌ Impossible de se connecter à la base de données")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de base de données: {e}")
        return False


def test_modules():
    """Tester l'importation des modules"""
    print("\n🧩 Test des modules...")
    
    modules = [
        ("ayanna_erp.ui.login_window", "LoginWindow"),
        ("ayanna_erp.ui.main_window", "MainWindow"),
        ("ayanna_erp.modules.boutique.boutique_window", "BoutiqueWindow"),
        ("ayanna_erp.modules.salle_fete.salle_fete_window", "SalleFeteWindow"),
        ("ayanna_erp.modules.hotel.hotel_window", "HotelWindow"),
        ("ayanna_erp.modules.restaurant.restaurant_window", "RestaurantWindow")
    ]
    
    all_ok = True
    
    for module_name, class_name in modules:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name} - OK")
            else:
                print(f"❌ {module_name}.{class_name} - CLASSE MANQUANTE")
                all_ok = False
        except ImportError as e:
            print(f"❌ {module_name} - ERREUR D'IMPORT: {e}")
            all_ok = False
    
    return all_ok


def main():
    """Fonction principale de test"""
    print("🧪 Test d'installation Ayanna ERP")
    print("=" * 50)
    
    tests = [
        ("Version Python", test_python_version),
        ("Dépendances", test_dependencies),
        ("Structure projet", test_project_structure),
        ("Base de données", test_database),
        ("Modules", test_modules)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{test_name:<20} : {status}")
        if result:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont réussis!")
        print("Vous pouvez démarrer Ayanna ERP avec: python3 main.py")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) en échec")
        print("Vérifiez les erreurs ci-dessus et relancez install.py si nécessaire")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
