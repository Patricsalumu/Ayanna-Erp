#!/usr/bin/env python3
"""
Script d'installation et de configuration pour Ayanna ERP
"""

import os
import sys
import subprocess
import hashlib
from pathlib import Path


def check_python_version():
    """Vérifie que Python 3.8+ est installé"""
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ requis. Version actuelle: {sys.version}")
        return False
    print(f"ℹ️  Python détecté: {sys.version.split()[0]}")
    return True


def create_virtual_environment():
    """Crée un environnement virtuel si nécessaire"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("ℹ️  Environnement virtuel détecté")
        return True
    
    print("ℹ️  Création de l'environnement virtuel...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Environnement virtuel créé")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la création de l'environnement virtuel: {e}")
        return False


def get_python_executable():
    """Retourne le chemin vers l'exécutable Python (venv ou système)"""
    venv_python = Path("venv/bin/python")
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def install_dependencies():
    """Installer les dépendances Python"""
    print("Installation des dépendances...")
    
    # Créer l'environnement virtuel si nécessaire
    if not create_virtual_environment():
        return False
    
    python_exec = get_python_executable()
    
    dependencies = [
        "PyQt6>=6.5.0",
        "SQLAlchemy>=2.0.0",
        "bcrypt>=4.0.0",
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0"
    ]
    
    for dep in dependencies:
        print(f"Installation de {dep}...")
        try:
            subprocess.check_call([python_exec, "-m", "pip", "install", dep])
            print(f"✅ {dep} installé avec succès")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'installation de {dep}: {e}")
            return False
    
    return True


def create_database():
    """Créer et initialiser la base de données"""
    print("Création de la base de données...")
    
    try:
        # Ajouter le répertoire courant au PYTHONPATH
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Si on utilise un environnement virtuel, s'assurer qu'il est activé
        python_exec = get_python_executable()
        if "venv" in python_exec:
            # Mettre à jour le PATH pour utiliser les modules du venv
            venv_site_packages = Path("venv/lib").glob("python*/site-packages")
            for site_pkg in venv_site_packages:
                sys.path.insert(0, str(site_pkg))
        
        from ayanna_erp.database.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        if db_manager.initialize_database():
            print("✅ Base de données créée et initialisée avec succès")
            return True
        else:
            print("❌ Erreur lors de la création de la base de données")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la base de données: {e}")
        return False


def create_default_admin():
    """Créer un utilisateur administrateur par défaut"""
    print("Création de l'utilisateur administrateur par défaut...")
    
    try:
        from ayanna_erp.database.database_manager import DatabaseManager, User, Entreprise
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Vérifier si une entreprise existe déjà
        existing_enterprise = session.query(Entreprise).first()
        if not existing_enterprise:
            # Créer une entreprise par défaut
            enterprise = Entreprise(
                name="Ayanna Solutions",
                address="123 Rue Exemple",
                phone="+243 123 456 789",
                email="contact@ayanna-solutions.com",
                slogan="Votre partenaire ERP de confiance",
                currency="USD"
            )
            session.add(enterprise)
            session.commit()
            print("✅ Entreprise par défaut créée")
        else:
            enterprise = existing_enterprise
        
        # Vérifier si un utilisateur admin existe déjà
        existing_admin = session.query(User).filter_by(email="admin@ayanna.com").first()
        if not existing_admin:
            # Créer un utilisateur admin par défaut
            admin_user = User(
                enterprise_id=enterprise.id,
                name="Administrateur",
                email="admin@ayanna.com",
                role="admin"
            )
            admin_user.set_password("admin123")  # Mot de passe par défaut
            session.add(admin_user)
            session.commit()
            
            print("✅ Utilisateur administrateur créé")
            print("📧 Email: admin@ayanna.com")
            print("🔑 Mot de passe: admin123")
            print("⚠️  Changez ce mot de passe après la première connexion!")
        else:
            print("✅ Utilisateur administrateur existe déjà")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'administrateur: {e}")
        return False


def create_desktop_shortcut():
    """Créer un raccourci sur le bureau (Linux)"""
    try:
        desktop_path = Path.home() / "Desktop"
        if not desktop_path.exists():
            desktop_path = Path.home() / "Bureau"  # Français
        
        if desktop_path.exists():
            shortcut_path = desktop_path / "Ayanna ERP.desktop"
            current_dir = Path(__file__).parent.absolute()
            main_script = current_dir / "main.py"
            
            desktop_content = f"""[Desktop Entry]
Name=Ayanna ERP
Comment=Système de Gestion Intégré
Exec=python3 "{main_script}"
Icon=application-x-executable
Terminal=false
Type=Application
Categories=Office;
"""
            
            with open(shortcut_path, 'w') as f:
                f.write(desktop_content)
            
            # Rendre le fichier exécutable
            os.chmod(shortcut_path, 0o755)
            
            print(f"✅ Raccourci créé sur le bureau: {shortcut_path}")
            return True
    except Exception as e:
        print(f"⚠️  Impossible de créer le raccourci: {e}")
        return False


def main():
    """Fonction principale d'installation"""
    print("🚀 Installation d'Ayanna ERP")
    print("=" * 40)
    
    success = True
    
    # Étape 0: Vérification de Python
    if not check_python_version():
        success = False
        sys.exit(1)
    
    # Étape 1: Installation des dépendances
    if not install_dependencies():
        success = False
    
    print()
    
    # Étape 2: Création de la base de données
    if success and not create_database():
        success = False
    
    print()
    
    # Étape 3: Création de l'utilisateur admin
    if success and not create_default_admin():
        success = False
    
    print()
    
    # Étape 4: Création du raccourci (optionnel)
    create_desktop_shortcut()
    
    print()
    print("=" * 40)
    
    if success:
        print("🎉 Installation terminée avec succès!")
        print()
        print("Pour démarrer Ayanna ERP:")
        if Path("venv").exists():
            print("1. ./run.sh start")
            print("2. Ou: source venv/bin/activate && python main.py")
        else:
            print("1. ./run.sh start")
            print("2. Ou: python3 main.py")
        print()
        print("Ou utilisez le raccourci sur le bureau si créé.")
        print()
        print("Identifiants par défaut:")
        print("Email: admin@ayanna.com")
        print("Mot de passe: admin123")
    else:
        print("❌ L'installation a échoué. Vérifiez les erreurs ci-dessus.")
        sys.exit(1)


if __name__ == "__main__":
    main()
