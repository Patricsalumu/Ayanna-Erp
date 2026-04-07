"""
Module model pour salle de fête
"""

from .salle_fete import (
    EventClient,
    EventService,
    EventReservation,
    EventReservationService,
    EventReservationProduct,
    EventPayment,
    EventStockMovement,
    EventExpense
)

# Import direct des modèles centralisés pour éviter les conflits SQLAlchemy
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory

__all__ = [
    'EventClient',
    'EventService',
    'EventReservation',
    'EventReservationService',
    'EventReservationProduct',
    'EventPayment',
    'EventStockMovement',
    'EventExpense',
    # Modèles centralisés
    'CoreProduct',
    'CoreProductCategory'
]