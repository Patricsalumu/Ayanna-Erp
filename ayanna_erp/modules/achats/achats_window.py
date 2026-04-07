"""
Fenêtre du module Achats pour Ayanna ERP
Point d'entrée principal pour le module de gestion des achats
"""

from ayanna_erp.modules.achats.views import AchatsMainWindow

# Alias pour la compatibilité avec le système principal
AchatsWindow = AchatsMainWindow

__all__ = ['AchatsWindow']
