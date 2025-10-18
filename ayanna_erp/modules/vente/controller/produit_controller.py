from ayanna_erp.modules.core.controllers.product_controller import CoreProductController

class ProduitController(CoreProductController):
    """
    Contrôleur pour la gestion des produits de la boutique
    Hérite du contrôleur centralisé CoreProductController
    """
    def __init__(self, pos_id: int):
        super().__init__(pos_id)  # Utilise l'entrepôt POS_2 pour la boutique

    def get_product_stock_total(self, session, product_id: int) -> float:
        """Méthode spécifique à la boutique pour la compatibilité"""
        stock_info = self.get_product_stock_info(product_id)
        return stock_info['total_stock']