"""
Vérification finale de l'intégration du module Boutique
"""

def check_integration():
    """Vérifie que tous les fichiers nécessaires sont en place"""
    
    import os
    
    print("🔍 VÉRIFICATION DE L'INTÉGRATION DU MODULE BOUTIQUE")
    print("=" * 60)
    
    base_path = r"c:\Ayanna ERP\Ayanna-Erp\ayanna_erp\modules\boutique"
    
    # Fichiers à vérifier
    files_to_check = {
        "Modèles": [
            f"{base_path}\\model\\__init__.py",
            f"{base_path}\\model\\models.py"
        ],
        "Vues": [
            f"{base_path}\\view\\__init__.py",
            f"{base_path}\\view\\boutique_window.py",
            f"{base_path}\\view\\panier_index.py",
            f"{base_path}\\view\\produit_index.py",
            f"{base_path}\\view\\categorie_index.py",
            f"{base_path}\\view\\client_index.py",
            f"{base_path}\\view\\stock_index.py",
            f"{base_path}\\view\\rapport_index.py"
        ],
        "Contrôleurs": [
            f"{base_path}\\controller\\__init__.py",
            f"{base_path}\\controller\\boutique_controller.py"
        ],
        "Utilitaires": [
            f"{base_path}\\init_boutique_data.py",
            f"{base_path}\\register_boutique_module.py",
            f"{base_path}\\check_boutique_status.py"
        ]
    }
    
    all_ok = True
    
    for category, files in files_to_check.items():
        print(f"\n📁 {category}:")
        for file_path in files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"   ✅ {os.path.basename(file_path)} ({size} bytes)")
            else:
                print(f"   ❌ {os.path.basename(file_path)} MANQUANT")
                all_ok = False
    
    # Vérification de main_window.py
    main_window_path = r"c:\Ayanna ERP\Ayanna-Erp\ayanna_erp\ui\main_window.py"
    print(f"\n🏠 Fenêtre principale:")
    if os.path.exists(main_window_path):
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = {
            "Import BoutiqueWindow": "from ayanna_erp.modules.boutique.view.boutique_window import BoutiqueWindow" in content,
            "Méthode ensure_boutique_module_registered": "def ensure_boutique_module_registered" in content,
            "Import QProgressDialog": "QProgressDialog" in content,
            "Logique open_module": 'elif module_name == "Boutique":' in content
        }
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if not passed:
                all_ok = False
    else:
        print(f"   ❌ main_window.py MANQUANT")
        all_ok = False
    
    print(f"\n{'=' * 60}")
    if all_ok:
        print("🎉 INTÉGRATION COMPLÈTE ET CORRECTE !")
        print("\n🚀 ÉTAPES SUIVANTES :")
        print("1. Lancez Ayanna ERP : python main.py")
        print("2. Connectez-vous avec vos identifiants")
        print("3. Cliquez sur le module 'Boutique'")
        print("4. Le module s'initialisera automatiquement au premier clic")
    else:
        print("⚠️  IL Y A DES FICHIERS MANQUANTS OU DES ERREURS")
    
    print("=" * 60)

if __name__ == "__main__":
    check_integration()