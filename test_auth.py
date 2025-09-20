"""
Test de l'authentification
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ayanna_erp.core.controllers.simple_user_controller import SimpleUserController

def test_auth():
    controller = SimpleUserController()
    
    # Récupérer le premier utilisateur
    users = controller.get_all_users()
    if users:
        user = users[0]
        print(f"Premier utilisateur:")
        print(f"  ID: {user.get('id')}")
        print(f"  Username: {user.get('username')}")
        print(f"  Name: {user.get('name')}")
        print(f"  Role: {user.get('role')}")
        
        # Test authentification avec différents mots de passe
        username = user.get('username')
        
        for password in ['admin', 'admin123', 'password']:
            auth = controller.authenticate_user(username, password)
            print(f"Auth {username}/{password}: {'OK' if auth else 'NOK'}")

if __name__ == "__main__":
    test_auth()