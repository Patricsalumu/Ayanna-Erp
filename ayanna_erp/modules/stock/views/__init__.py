"""
Module views pour la gestion du stock - Architecture modulaire
"""

# Import des widgets principaux
from .entrepot_widget import EntrepotWidget
from .stock_widget import StockWidget  
from .transfert_widget import TransfertWidget
from .alerte_widget import AlerteWidget
from .inventaire_widget import InventaireWidget
from .rapport_widget import RapportWidget

# Widget principal orchestrateur
from .modular_stock_widget import ModularStockManagementWidget, StockManagementWidget

__all__ = [
    'EntrepotWidget',
    'StockWidget',
    'TransfertWidget', 
    'AlerteWidget',
    'InventaireWidget',
    'RapportWidget',
    'ModularStockManagementWidget',
    'StockManagementWidget'  # Alias pour compatibilité
]