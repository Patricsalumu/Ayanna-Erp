"""
Contrôleur pour la gestion des réservations du module Salle de Fête
Gère toutes les opérations CRUD pour les réservations
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from datetime import datetime, date, timedelta

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ayanna_erp.modules.salle_fete.model.salle_fete import (EventReservation, EventClient, EventService, EventProduct,
                              EventReservationService, EventReservationProduct, get_database_manager)


class ReservationController(QObject):
    """Contrôleur pour la gestion des réservations"""
    
    # Signaux pour la communication avec la vue
    reservation_added = pyqtSignal(object)
    reservation_updated = pyqtSignal(object)
    reservation_deleted = pyqtSignal(int)
    reservations_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        
    def set_pos_id(self, pos_id):
        """Définir l'ID de l'entreprise"""
        self.pos_id = pos_id
        
    def create_reservation(self, reservation_data, services_data=None, products_data=None):
        """
        Créer une nouvelle réservation avec services et produits
        
        Args:
            reservation_data (dict): Données de la réservation
            services_data (list): Liste des services [{service_id, quantity, unit_price}, ...]
            products_data (list): Liste des produits [{product_id, quantity, unit_price}, ...]
            
        Returns:
            EventReservation: La réservation créée ou None
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
                
            # Créer la réservation principale
            reservation = EventReservation(
                pos_id=self.pos_id,
                partner_id=reservation_data.get('partner_id'),  # Client pré-enregistré
                client_nom=reservation_data.get('client_nom'),  # Nom saisi directement
                client_prenom=reservation_data.get('client_prenom'),  # Prénom saisi directement
                client_telephone=reservation_data.get('client_telephone'),  # Téléphone
                theme=reservation_data.get('theme', ''),  # Thème de l'événement
                event_date=reservation_data.get('event_date'),
                event_type=reservation_data.get('type', ''),  # Mapper 'type' -> 'event_type'
                guests_count=reservation_data.get('guests', 1),  # Mapper 'guests' -> 'guests_count'
                status=reservation_data.get('status', 'draft'),
                notes=reservation_data.get('notes', ''),
                discount_percent=reservation_data.get('discount_percent', reservation_data.get('discount', 0.0)),  # Support les deux formats
                tax_rate=reservation_data.get('tax_rate', 16.0),
                created_by=reservation_data.get('created_by', 0)
            )
            
            session.add(reservation)
            session.flush()  # Pour obtenir l'ID
            
            total_services = 0.0
            total_products = 0.0
            total_cost = 0.0
            
            # Ajouter les services
            if services_data:
                for service_data in services_data:
                    service = session.query(EventService).get(service_data['service_id'])
                    if service:
                        line_total = service_data['quantity'] * service_data['unit_price']
                        line_cost = service_data['quantity'] * service.cost
                        
                        reservation_service = EventReservationService(
                            reservation_id=reservation.id,
                            service_id=service_data['service_id'],
                            quantity=service_data['quantity'],
                            unit_price=service_data['unit_price'],
                            line_total=line_total,
                            line_cost=line_cost
                        )
                        session.add(reservation_service)
                        total_services += line_total
                        total_cost += line_cost
                        
            # Ajouter les produits
            if products_data:
                for product_data in products_data:
                    product = session.query(EventProduct).get(product_data['product_id'])
                    if product:
                        line_total = product_data['quantity'] * product_data['unit_price']
                        line_cost = product_data['quantity'] * product.cost
                        
                        reservation_product = EventReservationProduct(
                            reservation_id=reservation.id,
                            product_id=product_data['product_id'],
                            quantity=product_data['quantity'],
                            unit_price=product_data['unit_price'],
                            line_total=line_total,
                            line_cost=line_cost
                        )
                        session.add(reservation_product)
                        total_products += line_total
                        total_cost += line_cost
                        
            # Calculer les totaux - NOUVELLE LOGIQUE : total_amount SANS remise
            subtotal_ht = total_services + total_products
            
            # TVA calculée sur le montant BRUT (sans remise)
            tax_amount = subtotal_ht * (reservation.tax_rate / 100)
            
            # IMPORTANT : total_amount est le TTC SANS remise pour les calculs de pourcentage
            total_amount_sans_remise = subtotal_ht + tax_amount
            
            # Mettre à jour les totaux de la réservation
            reservation.total_services = total_services
            reservation.total_products = total_products
            reservation.total_cost = total_cost
            reservation.tax_amount = tax_amount  # TVA sur montant brut
            reservation.total_amount = total_amount_sans_remise  # TTC SANS remise
            
            # Créer un paiement automatique si un acompte est fourni
            deposit_amount = reservation_data.get('deposit', 0.0)
            payment = None

            if deposit_amount > 0:
                from ayanna_erp.modules.salle_fete.model.salle_fete import EventPayment
                payment = EventPayment(
                    reservation_id=reservation.id,
                    amount=deposit_amount,
                    payment_method='Espèces',
                    payment_date=datetime.now(),
                    status='validated',
                    user_id=1,
                    notes=f"Acompte automatique pour réservation {reservation.client_nom} {reservation.client_prenom}"
                )
                session.add(payment)
                session.flush()
                print(f"💰 Paiement d'acompte créé: {deposit_amount}€")
            else:
                print("ℹ️  Aucun acompte fourni, pas de paiement créé")

            # Créer les écritures comptables (journal vente + journal caisse si paiement)
            ecritures = self.creer_ecritures_comptables(session, reservation, payment)
            if ecritures:
                print(f"📊 {len(ecritures)} écritures comptables créées")
                
            session.commit()
            session.refresh(reservation)
            
            print(f"✅ Réservation créée: {reservation.client_nom} {reservation.client_prenom}")
            self.reservation_added.emit(reservation)
            return reservation
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la création de la réservation: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_reservation(self, reservation_id):
        """Récupérer une réservation par ID avec tous ses détails"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            reservation = session.query(EventReservation).filter(
                EventReservation.id == reservation_id,
                EventReservation.pos_id == self.pos_id
            ).first()
            
            if not reservation:
                return None
                
            # Récupérer les services liés
            services = session.query(EventReservationService, EventService).join(
                EventService, EventReservationService.service_id == EventService.id
            ).filter(EventReservationService.reservation_id == reservation_id).all()
            
            # Récupérer les produits liés  
            products = session.query(EventReservationProduct, EventProduct).join(
                EventProduct, EventReservationProduct.product_id == EventProduct.id
            ).filter(EventReservationProduct.reservation_id == reservation_id).all()
            
            # Récupérer les paiements liés avec les noms d'utilisateurs
            payments_query = session.execute(text("""
                SELECT 
                    ep.id, ep.amount, ep.payment_method, ep.payment_date, 
                    ep.status, ep.user_id, ep.notes,
                    COALESCE(cu.name, 'Utilisateur inconnu') as user_name
                FROM event_payments ep
                LEFT JOIN core_users cu ON ep.user_id = cu.id
                WHERE ep.reservation_id = :reservation_id
                ORDER BY ep.payment_date DESC
            """), {'reservation_id': reservation_id})
            
            # Calculer le total payé et construire la liste des paiements
            payments_list = []
            total_paid = 0
            
            for payment_row in payments_query:
                if payment_row.status == 'validated':
                    total_paid += payment_row.amount
                    
                payment_data = {
                    'amount': payment_row.amount,
                    'payment_method': payment_row.payment_method,
                    'payment_date': payment_row.payment_date,
                    'status': payment_row.status,
                    'user_id': payment_row.user_id,
                    'user_name': payment_row.user_name,
                    'notes': payment_row.notes or ''
                }
                payments_list.append(payment_data)
            
            remaining_amount = (reservation.total_amount or 0) - total_paid
            
            # Construire le dictionnaire complet
            reservation_details = {
                'id': reservation.id,
                'client_nom': reservation.get_client_name(),
                'client_telephone': reservation.client_telephone or (reservation.client.telephone if reservation.client else ''),
                'theme': reservation.theme or '',
                'event_date': reservation.event_date,
                'event_type': reservation.event_type or '',
                'guests_count': reservation.guests_count or 0,
                'status': reservation.status or 'draft',
                'notes': reservation.notes or '',
                'total_services': reservation.total_services or 0,
                'total_products': reservation.total_products or 0,
                'total_amount': reservation.total_amount or 0,
                'discount_percent': reservation.discount_percent or 0,
                'tax_rate': reservation.tax_rate or 0,
                'tax_amount': reservation.tax_amount or 0,
                'total_paid': total_paid,
                'remaining_amount': remaining_amount,
                'created_at': reservation.created_at,
                'services': [
                    {
                        'name': service.name,
                        'quantity': res_service.quantity,
                        'unit_price': res_service.unit_price,
                        'line_total': res_service.line_total
                    }
                    for res_service, service in services
                ],
                'products': [
                    {
                        'name': product.name,
                        'quantity': res_product.quantity,
                        'unit_price': res_product.unit_price,
                        'line_total': res_product.line_total
                    }
                    for res_product, product in products
                ],
                'payments': payments_list
            }
            
            return reservation_details
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération de la réservation: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_all_reservations(self, date_from=None, date_to=None, status=None):
        """
        Récupérer toutes les réservations avec filtres optionnels
        Filtre automatiquement par pos_id (entreprise) de l'utilisateur connecté
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            # Filtrage principal par pos_id (entreprise)
            query = session.query(EventReservation).filter(
                EventReservation.pos_id == self.pos_id
            ).join(EventClient, isouter=True)  # LEFT JOIN au cas où client supprimé
            
            # Filtres optionnels
            if date_from:
                query = query.filter(EventReservation.event_date >= date_from)
            if date_to:
                query = query.filter(EventReservation.event_date <= date_to)
            if status:
                query = query.filter(EventReservation.status == status)
                
            reservations = query.order_by(EventReservation.created_at.desc()).all()
            
            self.reservations_loaded.emit(reservations)
            return reservations
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des réservations: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def update_reservation_status(self, reservation_id, new_status):
        """Mettre à jour le statut d'une réservation"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            reservation = session.query(EventReservation).filter(
                EventReservation.id == reservation_id,
                EventReservation.pos_id == self.pos_id
            ).first()
            
            if not reservation:
                error_msg = f"Réservation {reservation_id} non trouvée"
                self.error_occurred.emit(error_msg)
                return False
                
            old_status = reservation.status
            reservation.status = new_status
            
            if new_status == 'completed':
                reservation.closed_at = datetime.now()
                
            session.commit()
            session.refresh(reservation)
            
            print(f"✅ Statut réservation {reservation.reference}: {old_status} → {new_status}")
            self.reservation_updated.emit(reservation)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la mise à jour du statut: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
    
    def add_reservation(self, reservation_data):
        """Ajouter une nouvelle réservation"""
        try:
            # Utiliser la méthode create_reservation existante
            reservation = self.create_reservation(reservation_data)
            if reservation:
                self.reservation_added.emit(reservation)
                return True
            return False
            
        except Exception as e:
            error_msg = f"Erreur lors de l'ajout de la réservation: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def update_reservation(self, reservation_id, reservation_data):
        """Mettre à jour une réservation existante"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            reservation = session.query(EventReservation).filter(
                EventReservation.id == reservation_id,
                EventReservation.pos_id == self.pos_id
            ).first()
            
            if not reservation:
                error_msg = f"Réservation {reservation_id} non trouvée"
                self.error_occurred.emit(error_msg)
                return False

            print(f"🔄 Mise à jour de la réservation {reservation_id}")
            print(f"📝 Données reçues: {reservation_data}")
            
            # Mettre à jour les informations client
            reservation.client_nom = reservation_data.get('client_nom', reservation.client_nom)
            reservation.client_prenom = reservation_data.get('client_prenom', reservation.client_prenom)
            reservation.client_telephone = reservation_data.get('client_telephone', reservation.client_telephone)
            
            # Mettre à jour les informations de l'événement
            reservation.theme = reservation_data.get('theme', reservation.theme)
            reservation.event_date = reservation_data.get('event_date', reservation.event_date)
            reservation.event_type = reservation_data.get('type', reservation.event_type)
            reservation.guests_count = reservation_data.get('guests', reservation.guests_count)
            reservation.status = reservation_data.get('status', reservation.status)
            reservation.notes = reservation_data.get('notes', reservation.notes)
            
            # Mettre à jour les montants financiers
            reservation.discount_percent = reservation_data.get('discount', reservation.discount_percent)
            reservation.tax_rate = reservation_data.get('tax_rate', reservation.tax_rate)
            reservation.tax_amount = reservation_data.get('tax_amount', reservation.tax_amount)
            reservation.total_services = reservation_data.get('total_services', reservation.total_services)
            reservation.total_products = reservation_data.get('total_products', reservation.total_products)
            reservation.total_amount = reservation_data.get('total', reservation.total_amount)
            
            # Supprimer les anciens services et produits
            session.query(EventReservationService).filter(
                EventReservationService.reservation_id == reservation_id
            ).delete()
            
            session.query(EventReservationProduct).filter(
                EventReservationProduct.reservation_id == reservation_id
            ).delete()
            
            # Ajouter les nouveaux services
            services_data = reservation_data.get('services', [])
            total_services = 0
            for service_data in services_data:
                if hasattr(service_data, 'service_data'):
                    # Checkbox avec service_data
                    service = service_data.service_data
                    service_id = service.id if hasattr(service, 'id') else service['id']
                    unit_price = service.price if hasattr(service, 'price') else service['price']
                    quantity = 1
                else:
                    # Données de service normales
                    service_id = service_data.get('service_id') or service_data.get('id')
                    unit_price = service_data.get('unit_price', service_data.get('price', 0))
                    quantity = service_data.get('quantity', 1)
                    print(f"📋 Service: ID={service_id}, Prix={unit_price}, Quantité={quantity}")
                
                if service_id is None:
                    print(f"❌ Service ID manquant pour: {service_data}")
                    continue
                
                line_total = float(unit_price) * quantity
                total_services += line_total
                
                reservation_service = EventReservationService(
                    reservation_id=reservation_id,
                    service_id=service_id,
                    quantity=quantity,
                    unit_price=float(unit_price),
                    line_total=line_total
                )
                session.add(reservation_service)
            
            # Ajouter les nouveaux produits
            products_data = reservation_data.get('products', [])
            total_products = 0
            for product_data in products_data:
                if hasattr(product_data, 'product_data'):
                    # Checkbox avec product_data
                    product = product_data.product_data
                    product_id = product.id if hasattr(product, 'id') else product['id']
                    unit_price = product.price_unit if hasattr(product, 'price_unit') else product['price_unit']
                    quantity = 1
                else:
                    # Données de produit normales
                    product_id = product_data.get('product_id') or product_data.get('id')
                    unit_price = product_data.get('unit_price', product_data.get('price_unit', 0))
                    quantity = product_data.get('quantity', 1)
                    print(f"📋 Produit: ID={product_id}, Prix={unit_price}, Quantité={quantity}")
                
                if product_id is None:
                    print(f"❌ Produit ID manquant pour: {product_data}")
                    continue
                
                line_total = float(unit_price) * quantity
                total_products += line_total
                
                reservation_product = EventReservationProduct(
                    reservation_id=reservation_id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=float(unit_price),
                    line_total=line_total
                )
                session.add(reservation_product)
            
            # Mettre à jour les totaux calculés
            reservation.total_services = total_services
            reservation.total_products = total_products
            
            # Recalculer le total
            subtotal = total_services + total_products
            discount_amount = subtotal * (reservation.discount_percent / 100)
            after_discount = subtotal - discount_amount
            tax_amount = after_discount * (reservation.tax_rate / 100)
            total_amount = after_discount + tax_amount
            
            reservation.tax_amount = tax_amount
            reservation.total_amount = total_amount
            
            session.commit()
            session.refresh(reservation)
            
            print(f"✅ Réservation {reservation_id} mise à jour avec succès")
            print(f"💰 Nouveaux totaux: Services={total_services}€, Produits={total_products}€, Total={total_amount}€")
            
            self.reservation_updated.emit(reservation)
            return reservation
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la mise à jour de la réservation: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"🔍 Traceback: {e}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def delete_reservation(self, reservation_id):
        """Supprimer une réservation (avec ses services et produits)"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            reservation = session.query(EventReservation).filter(
                EventReservation.id == reservation_id,
                EventReservation.pos_id == self.pos_id
            ).first()
            
            if not reservation:
                error_msg = f"Réservation {reservation_id} non trouvée"
                self.error_occurred.emit(error_msg)
                return False
                
            # Supprimer la réservation (cascade supprimera les services/produits liés)
            session.delete(reservation)
            session.commit()
            
            print(f"✅ Réservation supprimée: {reservation.reference}")
            self.reservation_deleted.emit(reservation_id)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la suppression: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def get_reservations_by_date(self, target_date):
        """Récupérer les réservations pour une date donnée"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            if isinstance(target_date, datetime):
                target_date = target_date.date()
                
            reservations = session.query(EventReservation).filter(
                EventReservation.pos_id == self.pos_id,
                EventReservation.event_date >= target_date,
                EventReservation.event_date < target_date + timedelta(days=1)
            ).order_by(EventReservation.event_date).all()
            
            return reservations
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des réservations: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
    
    def load_reservations(self):
        print(f"POS ID: {self.pos_id}")
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            # Récupérer toutes les réservations avec les clients
            reservations_query = session.query(EventReservation).join(EventClient).filter(
                EventReservation.pos_id == self.pos_id
            ).order_by(EventReservation.event_date.desc())
            
            reservations = reservations_query.all()
            
            # Convertir en dictionnaires pour la vue
            reservations_data = []
            for reservation in reservations:
                client = reservation.client
                reservations_data.append({
                    'id': reservation.id,
                    'reference': reservation.reference or '',
                    'client_nom': f"{client.prenom} {client.nom}" if client else 'Client inconnu',
                    'client_id': reservation.partner_id,
                    'event_date': reservation.event_date,
                    'event_type': reservation.event_type or '',
                    'guests_count': reservation.guests_count or 0,
                    'status': reservation.status or 'draft',
                    'total_amount': float(reservation.total_amount or 0),
                    'total_services': float(reservation.total_services or 0),
                    'total_products': float(reservation.total_products or 0),
                    'notes': reservation.notes or '',
                    'created_at': reservation.created_at
                })
            
            print(f"✅ {len(reservations_data)} réservations chargées")
            self.reservations_loaded.emit(reservations_data)
            return reservations_data
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des réservations: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def search_reservations(self, search_term):
        """Rechercher des réservations par référence, client ou type d'événement"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            search_pattern = f"%{search_term}%"
            
            reservations = session.query(EventReservation).join(EventClient).filter(
                EventReservation.pos_id == self.pos_id,
                (EventReservation.reference.ilike(search_pattern) |
                 EventReservation.event_type.ilike(search_pattern) |
                 EventClient.nom.ilike(search_pattern) |
                 EventClient.prenom.ilike(search_pattern))
            ).order_by(EventReservation.event_date.desc()).all()
            
            self.reservations_loaded.emit(reservations)
            return reservations
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()


    def creer_ecritures_comptables(self, session, reservation, payment=None):
        """
        Crée deux journaux et leurs écritures comptables pour une réservation.

        Journal 1 - Vente (Facture) — toujours créé :
          Débit  411 Client         : net à payer (TTC brut - remise)
          Débit  609 Remise         : montant remise (si remise > 0)
          Crédit 7xx Service        : montant HT brut par service (compte_produit_id du service)
          Crédit 7xx Produit        : montant HT brut par produit (compte_produit_id ou compte_vente_id)
          Crédit 44571 TVA          : montant TVA brut (si TVA > 0)

        Journal 2 - Caisse (Paiement) — créé seulement si payment != None :
          Débit  5xx Caisse         : montant payé
          Crédit 411 Client         : montant payé

        Args:
            session   : Session de base de données
            reservation : Instance de EventReservation
            payment   : Instance de EventPayment (optionnel)

        Returns:
            list: Liste de toutes les écritures créées
        """
        try:
            from ayanna_erp.modules.comptabilite.model.comptabilite import (
                ComptaEcritures as EcritureComptable,
                ComptaJournaux as JournalComptable,
                ComptaConfig,
            )
            from ayanna_erp.core.entreprise_controller import EntrepriseController

            entreprise_ctrl = EntrepriseController()
            enterprise_id = entreprise_ctrl.get_connected_enterprise_id()
            user_id = entreprise_ctrl.get_connected_user_id()

            config = session.query(ComptaConfig).filter_by(pos_id=self.pos_id).first()
            if not config:
                print("⚠️ Configuration comptable manquante pour ce point de vente")
                return []

            ecritures = []
            client_name = reservation.get_client_name()

            # Comptes configurés
            compte_client_id      = getattr(config, 'compte_client_id', None)
            compte_caisse_id      = getattr(config, 'compte_caisse_id', None)
            compte_tva_id         = getattr(config, 'compte_tva_id', None)
            compte_remise_id      = getattr(config, 'compte_remise_id', None)
            compte_vente_general_id = getattr(config, 'compte_vente_id', None)

            # Calculs financiers
            tva_total      = round(float(reservation.tax_amount or 0), 2)
            total_ttc_brut = round(float(reservation.total_amount or 0), 2)  # TTC sans remise
            remise_totale  = round(total_ttc_brut * (float(reservation.discount_percent or 0) / 100.0), 2)
            net_a_payer    = round(total_ttc_brut - remise_totale, 2)

            # ============================================================
            # JOURNAL 1 : VENTE (FACTURE)
            # ============================================================
            journal_vente = JournalComptable(
                enterprise_id=enterprise_id,
                libelle=f"Facture Réservation: {client_name}",
                montant=net_a_payer,
                type_operation="vente",
                reference=f"RES-{reservation.id}",
                description=f"Réservation ID: {reservation.id}",
                user_id=user_id,
                date_operation=datetime.now()
            )
            session.add(journal_vente)
            session.flush()
            print(f"📒 Journal vente créé: {net_a_payer:.2f}€")

            ordre = 1

            # Débit compte client (net à payer)
            if compte_client_id and net_a_payer > 0:
                e = EcritureComptable(
                    journal_id=journal_vente.id,
                    compte_comptable_id=compte_client_id,
                    debit=net_a_payer,
                    credit=0,
                    ordre=ordre,
                    libelle=f"Facture {client_name} - Net à payer"
                )
                session.add(e)
                ecritures.append(e)
                print(f"  📥 Débit Client: {net_a_payer:.2f} sur compte {compte_client_id}")
                ordre += 1
            elif not compte_client_id:
                print("⚠️ compte_client_id non configuré, écriture débit client ignorée")

            # Débit compte remise (si remise)
            if remise_totale > 0:
                if compte_remise_id:
                    e = EcritureComptable(
                        journal_id=journal_vente.id,
                        compte_comptable_id=compte_remise_id,
                        debit=remise_totale,
                        credit=0,
                        ordre=ordre,
                        libelle=f"Remise {reservation.discount_percent}% - {client_name}"
                    )
                    session.add(e)
                    ecritures.append(e)
                    print(f"  💳 Débit Remise: {remise_totale:.2f} sur compte {compte_remise_id}")
                    ordre += 1
                else:
                    print(f"⚠️ Remise de {remise_totale:.2f}€ non enregistrée: compte_remise_id non configuré")

            # Crédit services (par compte_produit_id du service, fallback compte_vente_general)
            for service_item in reservation.services:
                service = service_item.service
                if not service:
                    continue
                montant_ht = round(float(service_item.line_total or (service_item.unit_price or 0) * (service_item.quantity or 1)), 2)
                if montant_ht <= 0:
                    continue
                compte_id = getattr(service, 'compte_produit_id', None) or compte_vente_general_id
                if not compte_id:
                    print(f"⚠️ Service '{getattr(service, 'name', '')}' sans compte configuré, ignoré")
                    continue
                e = EcritureComptable(
                    journal_id=journal_vente.id,
                    compte_comptable_id=compte_id,
                    debit=0,
                    credit=montant_ht,
                    ordre=ordre,
                    libelle=f"Vente service: {getattr(service, 'name', '')} - {client_name}"
                )
                session.add(e)
                ecritures.append(e)
                print(f"  📤 Crédit Service '{getattr(service, 'name', '')}': {montant_ht:.2f} sur compte {compte_id}")
                ordre += 1

            # Crédit produits (par compte_produit_id du produit, fallback compte_vente_general)
            for product_item in reservation.products:
                product = product_item.product
                if not product:
                    continue
                montant_ht = round(float(product_item.line_total or (product_item.unit_price or 0) * (product_item.quantity or 1)), 2)
                if montant_ht <= 0:
                    continue
                compte_id = getattr(product, 'compte_produit_id', None) or compte_vente_general_id
                if not compte_id:
                    print(f"⚠️ Produit '{getattr(product, 'name', '')}' sans compte configuré, ignoré")
                    continue
                e = EcritureComptable(
                    journal_id=journal_vente.id,
                    compte_comptable_id=compte_id,
                    debit=0,
                    credit=montant_ht,
                    ordre=ordre,
                    libelle=f"Vente produit: {getattr(product, 'name', '')} - {client_name}"
                )
                session.add(e)
                ecritures.append(e)
                print(f"  📤 Crédit Produit '{getattr(product, 'name', '')}': {montant_ht:.2f} sur compte {compte_id}")
                ordre += 1

            # Crédit TVA (si applicable)
            if tva_total > 0:
                if compte_tva_id:
                    e = EcritureComptable(
                        journal_id=journal_vente.id,
                        compte_comptable_id=compte_tva_id,
                        debit=0,
                        credit=tva_total,
                        ordre=ordre,
                        libelle=f"TVA collectée {reservation.tax_rate}% - {client_name}"
                    )
                    session.add(e)
                    ecritures.append(e)
                    print(f"  📤 Crédit TVA: {tva_total:.2f} sur compte {compte_tva_id}")
                    ordre += 1
                else:
                    print(f"⚠️ TVA de {tva_total:.2f}€ non enregistrée: compte_tva_id non configuré")

            print(f"  ✅ Journal vente: {len(ecritures)} écritures")

            # ============================================================
            # JOURNAL 2 : CAISSE (PAIEMENT) — seulement si paiement fourni
            # ============================================================
            if payment is not None:
                montant_paye = round(float(payment.amount or 0), 2)
                # Utiliser le compte du mode de paiement si disponible,
                # sinon fallback sur le compte caisse de la config comptable
                try:
                    from ayanna_erp.database.database_manager import PaymentMode as _PaymentModeModel
                    _mode = session.query(_PaymentModeModel).filter(
                        _PaymentModeModel.enterprise_id == enterprise_id,
                        _PaymentModeModel.label == getattr(payment, 'payment_method', None),
                        _PaymentModeModel.is_active == 1
                    ).first()
                    if _mode and _mode.compte_id:
                        compte_caisse_id = _mode.compte_id
                        print(f"  💰 Compte caisse du mode '{_mode.label}': {_mode.compte_id} ({_mode.compte_label})")
                    else:
                        print(f"  💰 Mode '{getattr(payment, 'payment_method', '?')}' sans compte associé, compte caisse par défaut: {compte_caisse_id}")
                except Exception as _mode_err:
                    print(f"  ⚠️ Impossible de résoudre le compte du mode de paiement: {_mode_err}")
                if not compte_caisse_id:
                    print("⚠️ compte_caisse_id non configuré, journal caisse non créé")
                elif montant_paye <= 0:
                    print("⚠️ Montant paiement = 0, journal caisse non créé")
                else:
                    journal_caisse = JournalComptable(
                        enterprise_id=enterprise_id,
                        libelle=f"Paiement Réservation: {client_name}",
                        montant=montant_paye,
                        type_operation="entree",
                        reference=f"PAY-{payment.id}",
                        description=f"Acompte réservation ID: {reservation.id}",
                        user_id=user_id,
                        date_operation=datetime.now()
                    )
                    session.add(journal_caisse)
                    session.flush()
                    print(f"📒 Journal caisse créé: {montant_paye:.2f}€")

                    nb_caisse = 0

                    # Débit caisse
                    e = EcritureComptable(
                        journal_id=journal_caisse.id,
                        compte_comptable_id=compte_caisse_id,
                        debit=montant_paye,
                        credit=0,
                        ordre=1,
                        libelle=f"Encaissement acompte - {client_name}"
                    )
                    session.add(e)
                    ecritures.append(e)
                    nb_caisse += 1
                    print(f"  📥 Débit Caisse: {montant_paye:.2f} sur compte {compte_caisse_id}")

                    # Crédit client
                    if compte_client_id:
                        e = EcritureComptable(
                            journal_id=journal_caisse.id,
                            compte_comptable_id=compte_client_id,
                            debit=0,
                            credit=montant_paye,
                            ordre=2,
                            libelle=f"Règlement client - {client_name}"
                        )
                        session.add(e)
                        ecritures.append(e)
                        nb_caisse += 1
                        print(f"  📤 Crédit Client: {montant_paye:.2f} sur compte {compte_client_id}")

                    print(f"  ✅ Journal caisse: {nb_caisse} écritures")

            return ecritures

        except Exception as e:
            print(f"❌ Erreur lors de la création des écritures comptables: {e}")
            import traceback
            traceback.print_exc()
            return []
