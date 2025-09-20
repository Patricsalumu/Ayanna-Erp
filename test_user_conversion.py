"""
Test rapide de la conversion User vers dictionnaire
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_user_conversion():
    """Test de conversion utilisateur"""
    print("=== Test de conversion User -> Dict ===")
    
    # Simuler un objet User comme dans MainWindow
    class SimpleUser:
        def __init__(self, user_data):
            self.id = user_data['id']
            self.username = user_data['username']
            self.name = user_data['name']
            self.role = user_data['role']
            self.email = user_data.get('email', '')
    
    # Créer un utilisateur test
    user_obj = SimpleUser({
        'id': 1,
        'username': 'Super Administrateur',
        'name': 'Super Administrateur',
        'role': 'super_admin',
        'email': 'admin@ayanna.com'
    })
    
    print(f"Objet User original:")
    print(f"  - Type: {type(user_obj)}")
    print(f"  - name: {user_obj.name}")
    print(f"  - role: {user_obj.role}")
    
    # Fonction de conversion (copie de MainWindow)
    def user_to_dict(current_user):
        if hasattr(current_user, '__dict__'):
            user_dict = {}
            if hasattr(current_user, 'id'):
                user_dict['id'] = current_user.id
            if hasattr(current_user, 'username'):
                user_dict['username'] = current_user.username
            if hasattr(current_user, 'name'):
                user_dict['name'] = current_user.name
            if hasattr(current_user, 'role'):
                user_dict['role'] = current_user.role
            if hasattr(current_user, 'email'):
                user_dict['email'] = getattr(current_user, 'email', '')
            return user_dict
        else:
            return current_user
    
    # Conversion
    user_dict = user_to_dict(user_obj)
    
    print(f"\nDictionnaire converti:")
    print(f"  - Type: {type(user_dict)}")
    print(f"  - name: {user_dict.get('name')}")
    print(f"  - role: {user_dict.get('role')}")
    print(f"  - Contenu complet: {user_dict}")
    
    # Test d'utilisation comme dans les vues
    current_role = user_dict.get('role', '') if user_dict else ''
    print(f"\nTest d'accès role avec .get(): '{current_role}'")
    
    print("✓ Conversion réussie!")

if __name__ == "__main__":
    test_user_conversion()