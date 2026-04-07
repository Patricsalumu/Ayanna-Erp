
"""
Module model pour la boutique
"""

from .models import (
    ShopClient,
    ShopService,
    ShopPanier,
    ShopPanierProduct,
    ShopPanierService,
    ShopPayment,
    ShopExpense,
    ShopComptesConfig
)

# Import direct des modèles centralisés pour éviter les conflits SQLAlchemy
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory

__all__ = [
    'ShopClient',
    'ShopService',
    'ShopPanier',
    'ShopPanierProduct', 
    'ShopPanierService',
    'ShopPayment',
    'ShopExpense',
    'ShopComptesConfig',
    # Modèles centralisés
    'CoreProduct',
    'CoreProductCategory'
]