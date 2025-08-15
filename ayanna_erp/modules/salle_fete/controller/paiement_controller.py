"""
Contrôleur pour la gestion des paiements du module Salle de Fête
Gère toutes les opérations CRUD pour les paiements et les statistiques financières
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime, date

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from model.salle_fete import EventPayment, EventReservation, get_database_manager


class PaiementController(QObject):
    """Contrôleur pour la gestion des paiements"""
    
    # Signaux pour la communication avec la vue
    payment_added = pyqtSignal(object)
    payment_updated = pyqtSignal(object)
    payment_deleted = pyqtSignal(int)
    payments_loaded = pyqtSignal(list)
    payment_statistics_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        
    def set_pos_id(self, pos_id):
        """Définir l'ID de l'entreprise"""
        self.pos_id = pos_id
        
    def create_payment(self, payment_data):
        """
        Créer un nouveau paiement
        
        Args:
            payment_data (dict): Données du paiement
            
        Returns:
            EventPayment: Le paiement créé ou None
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            # Vérifier que la réservation existe
            reservation = session.query(EventReservation).filter(
                EventReservation.id == payment_data.get('reservation_id'),
                EventReservation.pos_id == self.pos_id
            ).first()
            
            if not reservation:
                error_msg = "Réservation non trouvée"
                self.error_occurred.emit(error_msg)
                return None
                
            payment = EventPayment(
                reservation_id=payment_data.get('reservation_id'),
                payment_method=payment_data.get('payment_method', 'Espèces'),
                amount=payment_data.get('amount', 0.0),
                payment_date=payment_data.get('payment_date', datetime.now()),
                status=payment_data.get('status', 'validated'),
                notes=payment_data.get('notes', ''),
                journal_id=payment_data.get('journal_id')
            )
            
            session.add(payment)
            session.commit()
            session.refresh(payment)
            
            print(f"✅ Paiement créé: {payment.amount}€ pour réservation {reservation.reference}")
            self.payment_added.emit(payment)
            return payment
            
        except IntegrityError as e:
            session.rollback()
            error_msg = f"Erreur d'intégrité: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la création du paiement: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_payment(self, payment_id):
        """Récupérer un paiement par ID"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            payment = session.query(EventPayment).join(EventReservation).filter(
                EventPayment.id == payment_id,
                EventReservation.pos_id == self.pos_id
            ).first()
            return payment
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du paiement: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_payments_by_reservation(self, reservation_id):
        """Récupérer tous les paiements d'une réservation"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            payments = session.query(EventPayment).join(EventReservation).filter(
                EventPayment.reservation_id == reservation_id,
                EventReservation.pos_id == self.pos_id
            ).order_by(EventPayment.payment_date.desc()).all()
            
            return payments
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des paiements: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def get_all_payments(self, date_from=None, date_to=None, payment_method=None):
        """
        Récupérer tous les paiements avec filtres optionnels
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            query = session.query(EventPayment).join(EventReservation).filter(
                EventReservation.pos_id == self.pos_id
            )
            
            if date_from:
                query = query.filter(EventPayment.payment_date >= date_from)
            if date_to:
                query = query.filter(EventPayment.payment_date <= date_to)
            if payment_method:
                query = query.filter(EventPayment.payment_method == payment_method)
                
            payments = query.order_by(EventPayment.payment_date.desc()).all()
            
            self.payments_loaded.emit(payments)
            return payments
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des paiements: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def update_payment(self, payment_id, payment_data):
        """Mettre à jour un paiement"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            payment = session.query(EventPayment).join(EventReservation).filter(
                EventPayment.id == payment_id,
                EventReservation.pos_id == self.pos_id
            ).first()
            
            if not payment:
                error_msg = f"Paiement avec l'ID {payment_id} non trouvé"
                self.error_occurred.emit(error_msg)
                return None
                
            # Mettre à jour les champs
            for field, value in payment_data.items():
                if hasattr(payment, field):
                    setattr(payment, field, value)
                    
            session.commit()
            session.refresh(payment)
            
            print(f"✅ Paiement modifié: {payment.amount}€")
            self.payment_updated.emit(payment)
            return payment
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la modification du paiement: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def delete_payment(self, payment_id):
        """Supprimer un paiement"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            payment = session.query(EventPayment).join(EventReservation).filter(
                EventPayment.id == payment_id,
                EventReservation.pos_id == self.pos_id
            ).first()
            
            if not payment:
                error_msg = f"Paiement avec l'ID {payment_id} non trouvé"
                self.error_occurred.emit(error_msg)
                return False
                
            amount = payment.amount
            session.delete(payment)
            session.commit()
            
            print(f"✅ Paiement supprimé: {amount}€")
            self.payment_deleted.emit(payment_id)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la suppression du paiement: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def get_payment_balance(self, reservation_id):
        """
        Calculer le solde d'une réservation (montant dû - paiements)
        
        Returns:
            dict: {'total_due': float, 'total_paid': float, 'balance': float}
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            # Récupérer la réservation
            reservation = session.query(EventReservation).filter(
                EventReservation.id == reservation_id,
                EventReservation.pos_id == self.pos_id
            ).first()
            
            if not reservation:
                return {'total_due': 0, 'total_paid': 0, 'balance': 0}
                
            # Calculer le total des paiements
            total_paid = session.query(func.sum(EventPayment.amount)).filter(
                EventPayment.reservation_id == reservation_id,
                EventPayment.status == 'validated'
            ).scalar() or 0
            
            balance = reservation.total_amount - total_paid
            
            return {
                'total_due': reservation.total_amount,
                'total_paid': total_paid,
                'balance': balance
            }
            
        except Exception as e:
            error_msg = f"Erreur lors du calcul du solde: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return {'total_due': 0, 'total_paid': 0, 'balance': 0}
            
        finally:
            db_manager.close_session()
            
    def get_payment_statistics(self, date_from=None, date_to=None):
        """
        Obtenir des statistiques sur les paiements
        
        Returns:
            dict: Statistiques détaillées
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            query = session.query(EventPayment).join(EventReservation).filter(
                EventReservation.pos_id == self.pos_id,
                EventPayment.status == 'validated'
            )
            
            if date_from:
                query = query.filter(EventPayment.payment_date >= date_from)
            if date_to:
                query = query.filter(EventPayment.payment_date <= date_to)
                
            # Total des paiements
            total_payments = query.with_entities(func.sum(EventPayment.amount)).scalar() or 0
            
            # Nombre de paiements
            count_payments = query.count()
            
            # Paiements par méthode
            payments_by_method = session.query(
                EventPayment.payment_method,
                func.sum(EventPayment.amount).label('total'),
                func.count(EventPayment.id).label('count')
            ).join(EventReservation).filter(
                EventReservation.pos_id == self.pos_id,
                EventPayment.status == 'validated'
            )
            
            if date_from:
                payments_by_method = payments_by_method.filter(EventPayment.payment_date >= date_from)
            if date_to:
                payments_by_method = payments_by_method.filter(EventPayment.payment_date <= date_to)
                
            payments_by_method = payments_by_method.group_by(EventPayment.payment_method).all()
            
            # Réservations impayées
            unpaid_reservations = session.query(EventReservation).filter(
                EventReservation.pos_id == self.pos_id,
                EventReservation.status.in_(['confirmed', 'in_progress'])
            ).all()
            
            unpaid_amount = 0
            for reservation in unpaid_reservations:
                balance = self.get_payment_balance(reservation.id)
                if balance['balance'] > 0:
                    unpaid_amount += balance['balance']
                    
            stats = {
                'total_payments': total_payments,
                'count_payments': count_payments,
                'average_payment': total_payments / count_payments if count_payments > 0 else 0,
                'payments_by_method': {method: {'total': total, 'count': count} 
                                     for method, total, count in payments_by_method},
                'unpaid_amount': unpaid_amount
            }
            
            self.payment_statistics_updated.emit(stats)
            return stats
            
        except Exception as e:
            error_msg = f"Erreur lors du calcul des statistiques: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return {}
            
        finally:
            db_manager.close_session()
            
    def get_daily_payments(self, target_date):
        """Récupérer les paiements d'une journée"""
        try:
            if isinstance(target_date, datetime):
                target_date = target_date.date()
                
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            payments = session.query(EventPayment).join(EventReservation).filter(
                EventReservation.pos_id == self.pos_id,
                func.date(EventPayment.payment_date) == target_date
            ).order_by(EventPayment.payment_date.desc()).all()
            
            return payments
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des paiements du jour: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
