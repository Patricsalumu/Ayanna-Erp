"""
Contrôleur pour la gestion des paiements du module Salle de Fête
Gestion des réservations, paiements et interactions avec la base de données
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import desc, and_, or_, func
from PyQt6.QtCore import QObject, pyqtSignal

# Import des modèles et du gestionnaire de base de données
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import (
    EventReservation, EventClient, EventService, EventProduct,
    EventReservationService, EventReservationProduct, EventPayment
)


class PaiementController(QObject):
    """Contrôleur pour la gestion des paiements et réservations"""
    
    # Signaux pour la communication avec l'interface
    payment_added = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
        
    def get_session(self):
        """Créer une nouvelle session de base de données"""
        return self.db_manager.get_session()
    
    def get_latest_reservations(self, limit=10):
        """
        Récupérer les dernières réservations
        
        Args:
            limit (int): Nombre maximum de réservations à retourner
            
        Returns:
            list: Liste des réservations avec leurs détails
        """
        try:
            session = self.get_session()
            
            # Récupérer les réservations avec les clients
            reservations = session.query(EventReservation)\
                .options(joinedload(EventReservation.client))\
                .filter(EventReservation.pos_id == self.pos_id)\
                .order_by(desc(EventReservation.created_at))\
                .limit(limit)\
                .all()
            
            result = []
            for reservation in reservations:
                # Calculer le solde
                total_paid = session.query(func.sum(EventPayment.amount))\
                    .filter(EventPayment.reservation_id == reservation.id,
                           EventPayment.status == 'validated')\
                    .scalar() or 0
                
                balance = (reservation.total_amount or 0) - total_paid
                
                reservation_data = {
                    'id': reservation.id,
                    'reference': str(reservation.id),  # Utiliser l'ID comme référence
                    'client_nom': reservation.get_client_name(),
                    'client_telephone': reservation.get_client_phone(),
                    'event_date': reservation.event_date,
                    'event_type': reservation.event_type or 'Non spécifié',
                    'theme': reservation.theme,
                    'guests_count': reservation.guests_count,
                    'status': reservation.status,
                    'total_amount': reservation.total_amount or 0,
                    'total_services': reservation.total_services or 0,
                    'total_products': reservation.total_products or 0,
                    'tax_amount': reservation.tax_amount or 0,
                    'discount_percent': reservation.discount_percent or 0,
                    'notes': reservation.notes,
                    'created_at': reservation.created_at,
                    'total_paid': total_paid,
                    'balance': balance
                }
                result.append(reservation_data)
            
            session.close()
            return result
            
        except Exception as e:
            print(f"Erreur lors de la récupération des réservations: {str(e)}")
            self.error_occurred.emit(f"Erreur lors de la récupération des réservations: {str(e)}")
            return []
    
    def search_reservations(self, search_term, search_type='all'):
        """
        Rechercher des réservations par différents critères
        
        Args:
            search_term (str): Terme de recherche
            search_type (str): Type de recherche ('all', 'phone', 'client', 'id', 'reference')
            
        Returns:
            list: Liste des réservations correspondantes
        """
        try:
            session = self.get_session()
            
            query = session.query(EventReservation)\
                .options(joinedload(EventReservation.client))\
                .filter(EventReservation.pos_id == self.pos_id)
            
            if search_type == 'all':
                # Recherche globale sur tous les champs
                conditions = []
                
                # Recherche par téléphone
                conditions.append(EventReservation.client_telephone.ilike(f'%{search_term}%'))
                conditions.append(EventReservation.client.has(EventClient.telephone.ilike(f'%{search_term}%')))
                
                # Recherche par nom/prénom
                conditions.append(EventReservation.client_nom.ilike(f'%{search_term}%'))
                conditions.append(EventReservation.client_prenom.ilike(f'%{search_term}%'))
                conditions.append(EventReservation.client.has(EventClient.nom.ilike(f'%{search_term}%')))
                conditions.append(EventReservation.client.has(EventClient.prenom.ilike(f'%{search_term}%')))
                
                # Recherche par ID/référence (si c'est un nombre)
                try:
                    reservation_id = int(search_term)
                    conditions.append(EventReservation.id == reservation_id)
                except ValueError:
                    pass
                
                # Recherche par type d'événement et thème
                conditions.append(EventReservation.event_type.ilike(f'%{search_term}%'))
                conditions.append(EventReservation.theme.ilike(f'%{search_term}%'))
                
                query = query.filter(or_(*conditions))
                
            elif search_type == 'phone':
                # Recherche par téléphone uniquement
                query = query.filter(
                    or_(
                        EventReservation.client_telephone.ilike(f'%{search_term}%'),
                        EventReservation.client.has(EventClient.telephone.ilike(f'%{search_term}%'))
                    )
                )
            elif search_type == 'client':
                # Recherche par nom de client uniquement
                query = query.filter(
                    or_(
                        EventReservation.client_nom.ilike(f'%{search_term}%'),
                        EventReservation.client_prenom.ilike(f'%{search_term}%'),
                        EventReservation.client.has(EventClient.nom.ilike(f'%{search_term}%')),
                        EventReservation.client.has(EventClient.prenom.ilike(f'%{search_term}%'))
                    )
                )
            elif search_type == 'id' or search_type == 'reference':
                # Recherche par ID/référence uniquement
                try:
                    reservation_id = int(search_term)
                    query = query.filter(EventReservation.id == reservation_id)
                except ValueError:
                    session.close()
                    return []
            
            reservations = query.order_by(desc(EventReservation.created_at)).all()
            
            result = []
            for reservation in reservations:
                # Calculer le solde
                total_paid = session.query(func.sum(EventPayment.amount))\
                    .filter(EventPayment.reservation_id == reservation.id,
                           EventPayment.status == 'validated')\
                    .scalar() or 0
                
                balance = (reservation.total_amount or 0) - total_paid
                
                reservation_data = {
                    'id': reservation.id,
                    'reference': str(reservation.id),
                    'client_nom': reservation.get_client_name(),
                    'client_telephone': reservation.get_client_phone(),
                    'event_date': reservation.event_date,
                    'event_type': reservation.event_type or 'Non spécifié',
                    'theme': reservation.theme,
                    'guests_count': reservation.guests_count,
                    'status': reservation.status,
                    'total_amount': reservation.total_amount or 0,
                    'total_services': reservation.total_services or 0,
                    'total_products': reservation.total_products or 0,
                    'tax_amount': reservation.tax_amount or 0,
                    'discount_percent': reservation.discount_percent or 0,
                    'notes': reservation.notes,
                    'created_at': reservation.created_at,
                    'total_paid': total_paid,
                    'balance': balance
                }
                result.append(reservation_data)
            
            session.close()
            return result
            
        except Exception as e:
            print(f"Erreur lors de la recherche de réservations: {str(e)}")
            self.error_occurred.emit(f"Erreur lors de la recherche: {str(e)}")
            return []
    
    def filter_reservations_by_date(self, start_date=None, end_date=None):
        """
        Filtrer les réservations par date d'événement
        
        Args:
            start_date (datetime): Date de début (optionnelle)
            end_date (datetime): Date de fin (optionnelle)
            
        Returns:
            list: Liste des réservations dans la plage de dates
        """
        try:
            session = self.get_session()
            
            query = session.query(EventReservation)\
                .options(joinedload(EventReservation.client))\
                .filter(EventReservation.pos_id == self.pos_id)
            
            if start_date:
                query = query.filter(EventReservation.event_date >= start_date)
            
            if end_date:
                # Ajouter 1 jour pour inclure toute la journée de fin
                end_date_inclusive = end_date + timedelta(days=1)
                query = query.filter(EventReservation.event_date < end_date_inclusive)
            
            reservations = query.order_by(EventReservation.event_date).all()
            
            result = []
            for reservation in reservations:
                # Calculer le solde
                total_paid = session.query(func.sum(EventPayment.amount))\
                    .filter(EventPayment.reservation_id == reservation.id,
                           EventPayment.status == 'validated')\
                    .scalar() or 0
                
                balance = (reservation.total_amount or 0) - total_paid
                
                reservation_data = {
                    'id': reservation.id,
                    'reference': str(reservation.id),
                    'client_nom': reservation.get_client_name(),
                    'client_telephone': reservation.get_client_phone(),
                    'event_date': reservation.event_date,
                    'event_type': reservation.event_type or 'Non spécifié',
                    'theme': reservation.theme,
                    'guests_count': reservation.guests_count,
                    'status': reservation.status,
                    'total_amount': reservation.total_amount or 0,
                    'total_services': reservation.total_services or 0,
                    'total_products': reservation.total_products or 0,
                    'tax_amount': reservation.tax_amount or 0,
                    'discount_percent': reservation.discount_percent or 0,
                    'notes': reservation.notes,
                    'created_at': reservation.created_at,
                    'total_paid': total_paid,
                    'balance': balance
                }
                result.append(reservation_data)
            
            session.close()
            return result
            
        except Exception as e:
            print(f"Erreur lors du filtrage par date: {str(e)}")
            self.error_occurred.emit(f"Erreur lors du filtrage par date: {str(e)}")
            return []
    
    def get_reservation_details(self, reservation_id):
        """
        Récupérer les détails complets d'une réservation avec services, produits et paiements
        
        Args:
            reservation_id (int): ID de la réservation
            
        Returns:
            dict: Détails complets de la réservation
        """
        try:
            session = self.get_session()
            
            # Récupérer la réservation avec toutes ses relations
            reservation = session.query(EventReservation)\
                .options(
                    joinedload(EventReservation.client),
                    joinedload(EventReservation.services).joinedload(EventReservationService.service),
                    joinedload(EventReservation.products).joinedload(EventReservationProduct.product),
                    joinedload(EventReservation.payments)
                )\
                .filter(EventReservation.id == reservation_id)\
                .first()
            
            if not reservation:
                return None
            
            # Préparer les services
            services = []
            for reservation_service in reservation.services:
                service_data = {
                    'id': reservation_service.service.id,
                    'name': reservation_service.service.name,
                    'description': reservation_service.service.description,
                    'quantity': reservation_service.quantity,
                    'unit_price': reservation_service.unit_price,
                    'line_total': reservation_service.line_total,
                    'line_cost': reservation_service.line_cost
                }
                services.append(service_data)
            
            # Préparer les produits
            products = []
            for reservation_product in reservation.products:
                product_data = {
                    'id': reservation_product.product.id,
                    'name': reservation_product.product.name,
                    'description': reservation_product.product.description,
                    'quantity': reservation_product.quantity,
                    'unit_price': reservation_product.unit_price,
                    'line_total': reservation_product.line_total,
                    'line_cost': reservation_product.line_cost,
                    'unit': reservation_product.product.unit
                }
                products.append(product_data)
            
            # Préparer les paiements
            payments = []
            total_paid = 0
            for payment in reservation.payments:
                if payment.status == 'validated':
                    total_paid += payment.amount
                    
                payment_data = {
                    'id': payment.id,
                    'amount': payment.amount,
                    'payment_method': payment.payment_method,
                    'payment_date': payment.payment_date,
                    'status': payment.status,
                    'notes': payment.notes
                }
                payments.append(payment_data)
            
            # Calculer le solde
            balance = (reservation.total_amount or 0) - total_paid
            
            reservation_details = {
                'id': reservation.id,
                'reference': str(reservation.id),
                'client_nom': reservation.get_client_name(),
                'client_telephone': reservation.get_client_phone(),
                'event_date': reservation.event_date,
                'event_type': reservation.event_type or 'Non spécifié',
                'theme': reservation.theme,
                'guests_count': reservation.guests_count,
                'status': reservation.status,
                'notes': reservation.notes,
                'total_amount': reservation.total_amount or 0,
                'total_services': reservation.total_services or 0,
                'total_products': reservation.total_products or 0,
                'tax_amount': reservation.tax_amount or 0,
                'discount_percent': reservation.discount_percent or 0,
                'total_cost': reservation.total_cost or 0,
                'created_at': reservation.created_at,
                'services': services,
                'products': products,
                'payments': payments,
                'total_paid': total_paid,
                'balance': balance
            }
            
            session.close()
            return reservation_details
            
        except Exception as e:
            print(f"Erreur lors de la récupération des détails: {str(e)}")
            self.error_occurred.emit(f"Erreur lors de la récupération des détails: {str(e)}")
            return None
    
    def create_payment(self, payment_data):
        """
        Créer un nouveau paiement pour une réservation
        
        Args:
            payment_data (dict): Données du paiement
                - reservation_id: ID de la réservation
                - amount: Montant du paiement
                - payment_method: Méthode de paiement
                - payment_date: Date du paiement (optionnel)
                - notes: Notes (optionnel)
                - status: Statut (optionnel, défaut: 'validated')
                
        Returns:
            bool: True si le paiement a été créé avec succès
        """
        try:
            session = self.get_session()
            
            # Vérifier que la réservation existe
            reservation = session.query(EventReservation)\
                .filter(EventReservation.id == payment_data['reservation_id'])\
                .first()
            
            if not reservation:
                self.error_occurred.emit("Réservation introuvable")
                session.close()
                return False
            
            # Calculer le solde actuel
            total_paid = session.query(func.sum(EventPayment.amount))\
                .filter(EventPayment.reservation_id == reservation.id,
                       EventPayment.status == 'validated')\
                .scalar() or 0
            
            balance = (reservation.total_amount or 0) - total_paid
            
            # Vérifier que le montant du paiement ne dépasse pas le solde
            if payment_data['amount'] > balance:
                self.error_occurred.emit(f"Le montant du paiement ({payment_data['amount']:.2f} €) dépasse le solde restant ({balance:.2f} €)")
                session.close()
                return False
            
            # Créer le paiement
            payment = EventPayment(
                reservation_id=payment_data['reservation_id'],
                amount=payment_data['amount'],
                payment_method=payment_data['payment_method'],
                payment_date=payment_data.get('payment_date', datetime.now()),
                status=payment_data.get('status', 'validated'),
                notes=payment_data.get('notes', '')
            )
            
            session.add(payment)
            session.commit()
            
            # Émettre le signal de succès
            self.payment_added.emit(payment)
            
            session.close()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création du paiement: {str(e)}")
            self.error_occurred.emit(f"Erreur lors de la création du paiement: {str(e)}")
            return False
    
    def get_payments_by_reservation(self, reservation_id):
        """
        Récupérer tous les paiements d'une réservation
        
        Args:
            reservation_id (int): ID de la réservation
            
        Returns:
            list: Liste des paiements
        """
        try:
            session = self.get_session()
            
            payments = session.query(EventPayment)\
                .filter(EventPayment.reservation_id == reservation_id)\
                .order_by(desc(EventPayment.payment_date))\
                .all()
            
            session.close()
            return payments
            
        except Exception as e:
            print(f"Erreur lors de la récupération des paiements: {str(e)}")
            self.error_occurred.emit(f"Erreur lors de la récupération des paiements: {str(e)}")
            return []
    
    def get_payment_balance(self, reservation_id):
        """
        Calculer le solde de paiement d'une réservation
        
        Args:
            reservation_id (int): ID de la réservation
            
        Returns:
            dict: Informations sur le solde
        """
        try:
            session = self.get_session()
            
            # Récupérer la réservation
            reservation = session.query(EventReservation)\
                .filter(EventReservation.id == reservation_id)\
                .first()
            
            if not reservation:
                session.close()
                return {'total_amount': 0, 'total_paid': 0, 'balance': 0}
            
            # Calculer le total payé
            total_paid = session.query(func.sum(EventPayment.amount))\
                .filter(EventPayment.reservation_id == reservation_id,
                       EventPayment.status == 'validated')\
                .scalar() or 0
            
            total_amount = reservation.total_amount or 0
            balance = total_amount - total_paid
            
            session.close()
            
            return {
                'total_amount': total_amount,
                'total_paid': total_paid,
                'balance': balance
            }
            
        except Exception as e:
            print(f"Erreur lors du calcul du solde: {str(e)}")
            self.error_occurred.emit(f"Erreur lors du calcul du solde: {str(e)}")
            return {'total_amount': 0, 'total_paid': 0, 'balance': 0}
    
    def get_payment_statistics(self, start_date=None, end_date=None):
        """
        Récupérer les statistiques de paiement
        
        Args:
            start_date (datetime): Date de début (optionnelle)
            end_date (datetime): Date de fin (optionnelle)
            
        Returns:
            dict: Statistiques de paiement
        """
        try:
            session = self.get_session()
            
            # Query de base pour les paiements validés
            payments_query = session.query(EventPayment)\
                .join(EventReservation)\
                .filter(EventReservation.pos_id == self.pos_id,
                       EventPayment.status == 'validated')
            
            if start_date:
                payments_query = payments_query.filter(EventPayment.payment_date >= start_date)
            
            if end_date:
                end_date_inclusive = end_date + timedelta(days=1)
                payments_query = payments_query.filter(EventPayment.payment_date < end_date_inclusive)
            
            # Calculer les statistiques
            total_payments = payments_query.with_entities(func.sum(EventPayment.amount)).scalar() or 0
            payment_count = payments_query.count()
            
            # Grouper par méthode de paiement
            payment_methods = payments_query.with_entities(
                EventPayment.payment_method,
                func.sum(EventPayment.amount),
                func.count(EventPayment.id)
            ).group_by(EventPayment.payment_method).all()
            
            methods_stats = []
            for method, amount, count in payment_methods:
                methods_stats.append({
                    'method': method,
                    'total_amount': amount or 0,
                    'count': count or 0
                })
            
            session.close()
            
            return {
                'total_payments': total_payments,
                'payment_count': payment_count,
                'average_payment': total_payments / payment_count if payment_count > 0 else 0,
                'payment_methods': methods_stats
            }
            
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {str(e)}")
            self.error_occurred.emit(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {
                'total_payments': 0,
                'payment_count': 0,
                'average_payment': 0,
                'payment_methods': []
            }
