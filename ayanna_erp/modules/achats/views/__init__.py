"""
Vues du module Achats
"""

from .achats_main_window import AchatsMainWindow, AchatsWindow
from .fournisseurs_widget import FournisseursWidget
from .commandes_widget import CommandesWidget
from .nouvelle_commande_widget import NouvelleCommandeWidget
from .dashboard_achats_widget import DashboardAchatsWidget

__all__ = [
    'AchatsMainWindow',
    'AchatsWindow',
    'FournisseursWidget',
    'CommandesWidget',
    'NouvelleCommandeWidget',
    'DashboardAchatsWidget'
]