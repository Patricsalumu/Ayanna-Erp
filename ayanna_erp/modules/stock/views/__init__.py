"""
Module views pour la gestion du stock - Architecture modulaire
"""

# Import des widgets principaux
from .entrepot_widget import EntrepotWidget
from .stock_widget import StockWidget  
from .transfert_widget import TransfertWidget
from .inventaire_widget import InventaireWidget

# Widget principal orchestrateur
from .modular_stock_widget import ModularStockManagementWidget, StockManagementWidget

__all__ = [
    'EntrepotWidget',
    'StockWidget',
    'TransfertWidget', 
    'InventaireWidget',
    'ModularStockManagementWidget',
    'StockManagementWidget'  # Alias pour compatibilité
]