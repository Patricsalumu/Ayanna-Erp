"""
Modèles SQLAlchemy pour le module Salle de Fête
Gestion des événements, réservations, services, produits et paiements
"""

import sys
import os
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, inspect
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

# Import du gestionnaire de base de données principal
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.database.database_manager import Base, DatabaseManager


class EventClient(Base):
    """Table des clients pour les événements"""
    __tablename__ = 'event_clients'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence à l'entreprise
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=False)
    email = Column(String(150))
    adresse = Column(Text)
    ville = Column(String(100))
    code_postal = Column(String(10))
    date_naissance = Column(DateTime)
    type_client = Column(String(50), default='Particulier')  # Particulier, Entreprise, Association
    source = Column(String(100))  # Comment nous a connu
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    reservations = relationship("EventReservation", back_populates="client")


class EventService(Base):
    """Table des services pour les événements"""
    __tablename__ = 'event_services'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence à l'entreprise
    name = Column(String(200), nullable=False)
    description = Column(Text)
    cost = Column(Float, default=0.0)  # Coût du service
    price = Column(Float, default=0.0)  # Prix de vente
    account_id = Column(Integer)  # Compte comptable
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    reservation_services = relationship("EventReservationService", back_populates="service")


class EventProduct(Base):
    """Table des produits pour les événements"""
    __tablename__ = 'event_products'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence à l'entreprise
    name = Column(String(200), nullable=False)
    description = Column(Text)
    cost = Column(Float, default=0.0)  # Coût d'achat
    price_unit = Column(Float, default=0.0)  # Prix unitaire de vente
    stock_quantity = Column(Float, default=0.0)  # Quantité en stock
    stock_min = Column(Float, default=0.0)  # Seuil minimum de stock
    unit = Column(String(50), default='pièce')  # Unité de mesure
    category = Column(String(100))  # Catégorie du produit
    account_id = Column(Integer)  # Compte comptable
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    reservation_products = relationship("EventReservationProduct", back_populates="product")
    stock_movements = relationship("EventStockMovement", back_populates="product")


class EventReservation(Base):
    """Table des réservations d'événements"""
    __tablename__ = 'event_reservations'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence à l'entreprise
    partner_id = Column(Integer, ForeignKey('event_clients.id'))  # Client pré-enregistré (optionnel)
    
    # Informations client directes (pour clients non pré-enregistrés)
    client_nom = Column(String(100))  # Nom du client saisi directement
    client_prenom = Column(String(100))  # Prénom du client saisi directement  
    client_telephone = Column(String(20))  # Téléphone du client saisi directement
    
    theme = Column(String(100))  # Thème de l'événement
    event_date = Column(DateTime, nullable=False)  # Date de l'événement
    event_type = Column(String(100))  # Type d'événement (Mariage, Anniversaire, etc.)
    guests_count = Column(Integer, default=1)  # Nombre d'invités
    status = Column(String(50), default='draft')  # draft, confirmed, in_progress, completed, cancelled
    notes = Column(Text)  # Notes sur la réservation
    
    # Totaux financiers
    total_services = Column(Float, default=0.0)
    total_products = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)  # Total TTC
    total_cost = Column(Float, default=0.0)  # Coût total
    discount_percent = Column(Float, default=0.0)  # Remise en pourcentage
    tax_rate = Column(Float, default=20.0)  # Taux de TVA
    tax_amount = Column(Float, default=0.0)  # Montant de la TVA
    
    # Métadonnées
    created_by = Column(Integer)  # Utilisateur qui a créé
    created_at = Column(DateTime, default=func.current_timestamp())
    closed_at = Column(DateTime)  # Date de clôture
    
    # Relations
    client = relationship("EventClient", back_populates="reservations")
    services = relationship("EventReservationService", back_populates="reservation", cascade="all, delete-orphan")
    products = relationship("EventReservationProduct", back_populates="reservation", cascade="all, delete-orphan")
    payments = relationship("EventPayment", back_populates="reservation", cascade="all, delete-orphan")
    
    def get_client_name(self):
        """Récupérer le nom complet du client (pré-enregistré ou saisi directement)"""
        if self.client:
            # Client pré-enregistré
            return f"{self.client.nom} {self.client.prenom}".strip()
        elif self.client_nom or self.client_prenom:
            # Client saisi directement
            return f"{self.client_nom or ''} {self.client_prenom or ''}".strip()
        else:
            return "Client non spécifié"
    
    def get_client_phone(self):
        """Récupérer le téléphone du client"""
        if self.client:
            return self.client.telephone
        else:
            return self.client_telephone or ""


class EventReservationService(Base):
    """Table de liaison entre réservations et services"""
    __tablename__ = 'event_reservation_services'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey('event_reservations.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('event_services.id'), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)  # Prix unitaire au moment de la réservation
    line_total = Column(Float, default=0.0)  # Total de la ligne
    line_cost = Column(Float, default=0.0)  # Coût de la ligne
    
    # Relations
    reservation = relationship("EventReservation", back_populates="services")
    service = relationship("EventService", back_populates="reservation_services")


class EventReservationProduct(Base):
    """Table de liaison entre réservations et produits"""
    __tablename__ = 'event_reservation_products'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey('event_reservations.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('event_products.id'), nullable=False)
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0.0)  # Prix unitaire au moment de la réservation
    line_total = Column(Float, default=0.0)  # Total de la ligne
    line_cost = Column(Float, default=0.0)  # Coût de la ligne
    
    # Relations
    reservation = relationship("EventReservation", back_populates="products")
    product = relationship("EventProduct", back_populates="reservation_products")


class EventPayment(Base):
    """Table des paiements pour les réservations"""
    __tablename__ = 'event_payments'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey('event_reservations.id'), nullable=False)
    payment_method = Column(String(50), nullable=False)  # Espèces, Carte, Chèque, Virement, etc.
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=func.current_timestamp())
    status = Column(String(50), default='validated')  # validated, pending, cancelled
    notes = Column(Text)
    journal_id = Column(Integer)  # Journal comptable
    
    # Relations
    reservation = relationship("EventReservation", back_populates="payments")


class EventStockMovement(Base):
    """Table des mouvements de stock pour les produits"""
    __tablename__ = 'event_stock_movements'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('event_products.id'), nullable=False)
    movement_type = Column(String(50), nullable=False)  # entry, exit, adjustment, loss
    quantity = Column(Float, nullable=False)  # Quantité (positive pour entrée, négative pour sortie)
    unit_cost = Column(Float, default=0.0)  # Coût unitaire
    reference = Column(String(100))  # Référence du mouvement (facture, réservation, etc.)
    reason = Column(String(200))  # Raison du mouvement
    movement_date = Column(DateTime, default=func.current_timestamp())
    created_by = Column(Integer)  # Utilisateur qui a créé le mouvement
    
    # Relations
    product = relationship("EventProduct", back_populates="stock_movements")


class EventExpense(Base):
    """Table des dépenses liées aux événements"""
    __tablename__ = 'event_expenses'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence à l'entreprise
    reservation_id = Column(Integer, ForeignKey('event_reservations.id'))  # Optionnel, si lié à une réservation
    expense_type = Column(String(100), nullable=False)  # Type de dépense
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    expense_date = Column(DateTime, nullable=False)
    supplier = Column(String(200))  # Fournisseur
    invoice_number = Column(String(100))  # Numéro de facture
    payment_method = Column(String(50))  # Méthode de paiement
    account_id = Column(Integer)  # Compte comptable
    created_by = Column(Integer)
    created_at = Column(DateTime, default=func.current_timestamp())


# Instance globale du gestionnaire de base de données principal
from ayanna_erp.database.database_manager import DatabaseManager

# Variable globale pour le gestionnaire
salle_fete_db = None

def get_database_manager():
    """Obtenir l'instance du gestionnaire de base de données principal"""
    global salle_fete_db
    if salle_fete_db is None:
        # Utiliser le même chemin que l'application principale
        import ayanna_erp
        main_db_path = os.path.join(os.path.dirname(ayanna_erp.__file__), '..', 'ayanna_erp.db')
        main_db_path = os.path.abspath(main_db_path)
        database_url = f'sqlite:///{main_db_path}'
        salle_fete_db = DatabaseManager(database_url)
        
        # Créer les tables du module si nécessaire
        try:
            Base.metadata.create_all(bind=salle_fete_db.engine, checkfirst=True)
            print(f"✅ Tables créées dans: {main_db_path}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la création des tables: {e}")
        
    return salle_fete_db


def initialize_salle_fete_tables():
    """
    Initialiser seulement les tables du module Salle de Fête dans la BDD principale
    """
    try:
        db_manager = get_database_manager()
        
        # Créer seulement les tables de ce module
        tables_to_create = [
            EventClient.__table__,
            EventService.__table__,
            EventProduct.__table__,
            EventReservation.__table__,
            EventReservationService.__table__,
            EventReservationProduct.__table__,
            EventPayment.__table__,
            EventStockMovement.__table__,
            EventExpense.__table__
        ]
        
        for table in tables_to_create:
            table.create(bind=db_manager.engine, checkfirst=True)
        
        print("✅ Tables du module Salle de Fête initialisées dans la BDD principale")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation des tables Salle de Fête: {e}")
        return False


def create_sample_data(pos_id=1):
    """Créer des données d'exemple pour tester le module"""
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Vérifier si des données existent déjà
        if session.query(EventService).first():
            print("ℹ️ Données d'exemple déjà présentes")
            return
        
        # Créer des services d'exemple
        services = [
            EventService(pos_id=pos_id, name="Décoration florale premium", description="Décoration complète avec fleurs fraîches", cost=150.0, price=250.0),
            EventService(pos_id=pos_id, name="DJ avec équipement son", description="DJ professionnel avec système son complet", cost=200.0, price=400.0),
            EventService(pos_id=pos_id, name="Service traiteur", description="Service complet de restauration", cost=15.0, price=25.0),
            EventService(pos_id=pos_id, name="Animation enfants", description="Animateur professionnel pour enfants", cost=80.0, price=150.0),
            EventService(pos_id=pos_id, name="Photobooth", description="Borne photo avec accessoires", cost=100.0, price=200.0),
            EventService(pos_id=pos_id, name="Service de nettoyage", description="Nettoyage complet après événement", cost=50.0, price=100.0),
        ]
        
        # Créer des produits d'exemple
        products = [
            EventProduct(pos_id=pos_id, name="Champagne Moët & Chandon", cost=30.0, price_unit=45.0, stock_quantity=25, stock_min=10, unit="bouteille", category="Boissons"),
            EventProduct(pos_id=pos_id, name="Petits fours assortis", cost=8.0, price_unit=12.0, stock_quantity=20, stock_min=20, unit="plateau", category="Alimentaire"),
            EventProduct(pos_id=pos_id, name="Nappe blanche 3m", cost=10.0, price_unit=15.0, stock_quantity=30, stock_min=5, unit="pièce", category="Matériel"),
            EventProduct(pos_id=pos_id, name="Bouquet de roses", cost=20.0, price_unit=35.0, stock_quantity=5, stock_min=5, unit="bouquet", category="Décoration"),
            EventProduct(pos_id=pos_id, name="Assiettes jetables", cost=5.0, price_unit=8.0, stock_quantity=100, stock_min=50, unit="lot de 20", category="Matériel"),
            EventProduct(pos_id=pos_id, name="Vin rouge Bordeaux", cost=15.0, price_unit=25.0, stock_quantity=15, stock_min=10, unit="bouteille", category="Boissons"),
        ]
        
        # Créer des clients d'exemple
        clients = [
            EventClient(pos_id=pos_id, nom="Dupont", prenom="Martin", telephone="06.12.34.56.78", email="martin.dupont@email.com", type_client="Particulier", source="Bouche à oreille"),
            EventClient(pos_id=pos_id, nom="Bernard", prenom="Sophie", telephone="06.98.76.54.32", email="sophie.bernard@email.com", type_client="Particulier", source="Site internet"),
            EventClient(pos_id=pos_id, nom="Moreau", prenom="Jean", telephone="06.11.22.33.44", email="jean.moreau@email.com", type_client="Particulier", source="Réseaux sociaux"),
            EventClient(pos_id=pos_id, nom="Dubois", prenom="Claire", telephone="06.55.66.77.88", email="claire.dubois@email.com", type_client="Entreprise", source="Publicité locale"),
            EventClient(pos_id=pos_id, nom="Martin", prenom="Pierre", telephone="06.99.88.77.66", email="pierre.martin@email.com", type_client="Association", source="Ancien client"),
        ]
        
        # Ajouter tout à la session
        session.add_all(services + products + clients)
        session.commit()
        
        print("✅ Données d'exemple créées avec succès")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de la création des données d'exemple: {e}")
        return False
    finally:
        db_manager.close_session()


def ensure_pos_exists(session, default_pos_id=1):
    """
    S'assurer qu'un point de vente existe pour le module Salle de Fête
    Récupérer le POS existant ou utiliser l'ID par défaut
    """
    try:
        from ayanna_erp.database.database_manager import POSPoint, Module
        
        # Vérifier si le POS existe déjà
        pos = session.query(POSPoint).filter_by(id=default_pos_id).first()
        if pos:
            print(f"✅ POS existant trouvé: {pos.name} (ID: {pos.id})")
            return pos.id
        
        # Chercher un POS pour le module SalleFete
        module = session.query(Module).filter_by(name="SalleFete").first()
        if module:
            pos = session.query(POSPoint).filter_by(module_id=module.id).first()
            if pos:
                print(f"✅ POS trouvé pour le module SalleFete: {pos.name} (ID: {pos.id})")
                return pos.id
        
        print(f"⚠️ Aucun POS trouvé, utilisation de l'ID par défaut: {default_pos_id}")
        return default_pos_id
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche du POS: {e}")
        return default_pos_id


def initialize_salle_fete_module(pos_id=1):
    """
    Initialiser le module Salle de Fête
    À appeler la première fois que l'utilisateur accède au module
    """
    try:
        # Vérifier si le module est déjà initialisé en vérifiant la présence de données
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Vérifier s'il y a déjà des services pour cette entreprise
        existing_services = session.query(EventService).filter(EventService.pos_id == pos_id).first()
        
        if existing_services:
            # Le module est déjà initialisé, retourner silencieusement
            db_manager.close_session()
            return True
            
        # Première initialisation
        print("🎪 Initialisation du module Salle de Fête...")
        
        # Vérifier si le POS existe, sinon le créer
        pos_id = ensure_pos_exists(session, pos_id)
        db_manager.close_session()
        
        # Initialiser les tables dans la BDD principale
        if initialize_salle_fete_tables():
            # Créer des données d'exemple
            create_sample_data(pos_id)
            print("🎉 Module Salle de Fête initialisé avec succès !")
            return True
        else:
            print("❌ Échec de l'initialisation du module Salle de Fête")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False


if __name__ == "__main__":
    # Test de l'initialisation
    initialize_salle_fete_module()
