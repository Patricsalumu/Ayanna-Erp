"""
Contrôleur pour la gestion des réservations du module Salle de Fête
Gère toutes les opérations CRUD pour les réservations
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, timedelta

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from model.salle_fete import (EventReservation, EventClient, EventService, EventProduct,
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
                discount_percent=reservation_data.get('discount', 0.0),  # Mapper 'discount' -> 'discount_percent'
                tax_rate=reservation_data.get('tax_rate', 20.0),
                created_by=reservation_data.get('created_by', 1)
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
                        
            # Calculer les totaux
            subtotal = total_services + total_products
            discount_amount = subtotal * (reservation.discount_percent / 100)
            subtotal_after_discount = subtotal - discount_amount
            tax_amount = subtotal_after_discount * (reservation.tax_rate / 100)
            total_amount = subtotal_after_discount + tax_amount
            
            # Mettre à jour les totaux de la réservation
            reservation.total_services = total_services
            reservation.total_products = total_products
            reservation.total_cost = total_cost
            reservation.tax_amount = tax_amount
            reservation.total_amount = total_amount
            
            # Créer un paiement automatique si un acompte est fourni
            deposit_amount = reservation_data.get('deposit', 0.0)
            print(f"🔍 Debug - Acompte reçu: {deposit_amount}€")
            
            if deposit_amount > 0:
                from model.salle_fete import EventPayment
                
                payment = EventPayment(
                    reservation_id=reservation.id,
                    amount=deposit_amount,
                    payment_method='Espèces',  # Simplifier en utilisant espèces par défaut
                    payment_date=datetime.now(),
                    status='validated',
                    notes=f"Acompte automatique pour réservation {reservation.client_nom} {reservation.client_prenom}"
                )
                session.add(payment)
                print(f"💰 Paiement d'acompte créé: {deposit_amount}€")
            else:
                print("ℹ️  Aucun acompte fourni, pas de paiement créé")
            
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
            
            # Récupérer les paiements liés
            from model.salle_fete import EventPayment
            payments = session.query(EventPayment).filter(
                EventPayment.reservation_id == reservation_id
            ).all()
            
            # Calculer le total payé
            total_paid = sum(payment.amount for payment in payments if payment.status == 'validated')
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
                'payments': [
                    {
                        'amount': payment.amount,
                        'payment_method': payment.payment_method,
                        'payment_date': payment.payment_date,
                        'status': payment.status,
                        'notes': payment.notes or ''
                    }
                    for payment in payments
                ]
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
