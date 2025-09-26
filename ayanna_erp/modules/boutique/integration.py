"""
Integration du module Boutique avec Ayanna ERP
"""

from PyQt6.QtWidgets import QMessageBox
from ayanna_erp.modules.boutique.view.boutique_window import BoutiqueWindow
from ayanna_erp.modules.boutique.init_boutique_data import initialize_boutique_data


def open_boutique_module(parent_window=None, current_user=None):
    """
    Ouvrir le module boutique depuis le menu principal
    
    Args:
        parent_window: Fenêtre parent (optionnel)
        current_user: Utilisateur connecté
    """
    
    try:
        # Vérifier que l'utilisateur est connecté
        if not current_user:
            QMessageBox.warning(
                parent_window, 
                "Accès refusé", 
                "Vous devez être connecté pour accéder au module Boutique."
            )
            return None
        
        # Initialiser les données si nécessaire (première utilisation)
        try:
            initialize_boutique_data()
        except Exception:
            # Les données existent déjà, pas de problème
            pass
        
        # Créer et afficher la fenêtre boutique
        boutique_window = BoutiqueWindow(current_user)
        
        # Centrer la fenêtre si un parent existe
        if parent_window:
            # Calculer la position pour centrer
            parent_geometry = parent_window.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - boutique_window.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - boutique_window.height()) // 2
            boutique_window.move(x, y)
        
        boutique_window.show()
        return boutique_window
        
    except Exception as e:
        QMessageBox.critical(
            parent_window,
            "Erreur Boutique",
            f"Impossible d'ouvrir le module Boutique:\n{str(e)}"
        )
        return None


def get_boutique_menu_info():
    """
    Retourner les informations du menu pour intégrer la boutique
    
    Returns:
        dict: Informations du menu (nom, icône, fonction, etc.)
    """
    return {
        "name": "Boutique",
        "icon": "🏪",
        "description": "Point de vente - Gestion des produits, services et ventes",
        "category": "Vente",
        "function": open_boutique_module,
        "shortcut": "Ctrl+B",
        "requires_user": True
    }