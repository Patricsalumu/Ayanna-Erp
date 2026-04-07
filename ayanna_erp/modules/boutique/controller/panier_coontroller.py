from ayanna_erp.modules.boutique.model.models import ShopPanier
from ayanna_erp.database.database_manager import DatabaseManager
from datetime import datetime

class PanierController:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or DatabaseManager()

    def remove_product_from_panier(self, panier_id, product_id):
        """
        Supprime un produit du panier spécifié.
        """
        session = self.db_manager.get_session()
        from ayanna_erp.modules.boutique.model.models import ShopPanierProduct
        panier_product = session.query(ShopPanierProduct).filter_by(panier_id=panier_id, product_id=product_id).first()
        if panier_product:
            session.delete(panier_product)
            session.commit()
            return True
        return False

    def update_product_quantity(self, panier_id, product_id, new_quantity):
        """
        Met à jour la quantité d'un produit dans le panier spécifié.
        """
        session = self.db_manager.get_session()
        from ayanna_erp.modules.boutique.model.models import ShopPanierProduct
        panier_product = session.query(ShopPanierProduct).filter_by(panier_id=panier_id, product_id=product_id).first()
        if panier_product:
            panier_product.quantity = new_quantity
            panier_product.total_price = float(new_quantity) * float(panier_product.price_unit)
            session.commit()
            return panier_product
        return None

    def update_panier_status(self, panier_id, new_status):
        """
        Met à jour le statut du panier (ex: 'valide', 'annule').
        """
        session = self.db_manager.get_session()
        panier = session.query(ShopPanier).get(panier_id)
        if panier:
            panier.status = new_status
            panier.updated_at = datetime.now()
            session.commit()
            return True
        return False
    def add_product_to_panier(self, panier_id, product_id, quantity, price_unit):
        """
        Ajoute un produit au panier spécifié.
        """
        session = self.db_manager.get_session()
        total_price = quantity * price_unit
        from ayanna_erp.modules.boutique.model.models import ShopPanierProduct
        panier_product = ShopPanierProduct(
            panier_id=panier_id,
            product_id=product_id,
            quantity=quantity,
            price_unit=price_unit,
            total_price=total_price
        )
        session.add(panier_product)
        session.commit()
        return panier_product

    def add_service_to_panier(self, panier_id, service_id, quantity, price_unit):
        """
        Ajoute un service au panier spécifié.
        """
        session = self.db_manager.get_session()
        total_price = quantity * price_unit
        from ayanna_erp.modules.boutique.model.models import ShopPanierService
        panier_service = ShopPanierService(
            panier_id=panier_id,
            service_id=service_id,
            quantity=quantity,
            price_unit=price_unit,
            total_price=total_price
        )
        session.add(panier_service)
        session.commit()
        return panier_service
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or DatabaseManager()

    def create_empty_panier(self, pos_id=1, client_id=None):
        """
        Crée un panier vide (statut 'en_cours') et le sauvegarde en base.
        Retourne l'instance du panier créé.
        """
        session = self.db_manager.get_session()
        # Générer un numéro de commande unique (timestamp)
        numero_commande = f"PNR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        panier = ShopPanier(
            pos_id=pos_id,
            client_id=client_id,
            numero_commande=numero_commande,
            status='en_cours',
            subtotal=0.0,
            remise_percent=0.0,
            remise_amount=0.0,
            total_final=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(panier)
        session.commit()
        return panier
