"""
Contrôleur pour la gestion des paiements du module Salle de Fête
Gestion des réservations, paiements et interactions avec la base de données
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import desc, and_, or_, func, text
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
            
            # Préparer les paiements avec les noms d'utilisateurs
            payments = []
            total_paid = 0
            
            # Récupérer les paiements avec une jointure sur la table core_users
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
            
            for payment_row in payments_query:
                if payment_row.status == 'validated':
                    total_paid += payment_row.amount
                    
                payment_data = {
                    'id': payment_row.id,
                    'amount': payment_row.amount,
                    'payment_method': payment_row.payment_method,
                    'payment_date': payment_row.payment_date,
                    'status': payment_row.status,
                    'user_id': payment_row.user_id,
                    'user_name': payment_row.user_name,
                    'notes': payment_row.notes
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
                user_id=payment_data.get('user_id', 1),  # TODO: Récupérer l'ID de l'utilisateur connecté
                notes=payment_data.get('notes', '')
            )
            
            session.add(payment)
            session.flush()  # Pour avoir l'ID du paiement
            
            # === INTEGRATION COMPTABLE ===
            from ayanna_erp.modules.comptabilite.model.comptabilite import (
                ComptaConfig,
                ComptaEcritures as EcritureComptable, 
                ComptaJournaux as JournalComptable, 
                ComptaComptes as CompteComptable
            )
            
            # Récupérer la configuration comptable pour ce POS
            config = session.query(ComptaConfig).filter_by(pos_id=self.pos_id).first()
            if not config:
                print("⚠️  Configuration comptable manquante pour ce point de vente")
            else:
                # Créer la ligne de journal comptable
                libelle = f"Paiement Réservation: {reservation.get_client_name()}"
                journal = JournalComptable(
                    enterprise_id=1,  # TODO: Récupérer l'ID de l'entreprise du POS
                    libelle=libelle,
                    montant=payment_data['amount'],
                    type_operation="entree",  # 'entree' pour un paiement
                    reference=f"PAY-{payment.id}",
                    description=f"Paiement réservation ID: {reservation.id}",
                    user_id=payment_data.get('user_id', 1),
                    date_operation=payment_data.get('payment_date', datetime.now())
                )
                session.add(journal)
                session.flush()  # Pour avoir l'id du journal

                # Récupérer les comptes configurés
                compte_debit = session.query(CompteComptable).filter(CompteComptable.id == config.compte_caisse_id).first()
                if not compte_debit:
                    print("⚠️  Le compte caisse configuré n'existe pas ou n'est pas actif.")
                else:
                    # Vérifier si le compte TVA est configuré
                    compte_tva_id = config.compte_tva_id if hasattr(config, 'compte_tva_id') else None
                    if compte_tva_id:
                        compte_tva = session.query(CompteComptable).filter(CompteComptable.id == compte_tva_id).first()
                        if not compte_tva:
                            print("⚠️  Compte TVA configuré mais inexistant, TVA sera ignorée")
                            compte_tva_id = None

                    # NOUVELLE LOGIQUE : Calculer la répartition du paiement selon les comptes spécifiques
                    repartition = self.calculer_repartition_paiement(reservation, payment_data['amount'])
                    
                    # Créer les écritures comptables réparties
                    ecritures = self.creer_ecritures_comptables_reparties(
                        session=session,
                        reservation=reservation,
                        payment=payment,
                        repartition=repartition,
                        compte_debit_id=compte_debit.id,
                        compte_tva_id=compte_tva_id,
                        journal_id=journal.id
                    )
                    
                    if ecritures:
                        print(f"📊 {len(ecritures)} écritures comptables créées avec répartition")
                    else:
                        # Fallback à l'ancienne méthode si problème
                        print("⚠️  Fallback: création d'écriture simple")
                        compte_credit = session.query(CompteComptable).filter(CompteComptable.id == config.compte_vente_id).first()
                        if not compte_credit:
                            print("⚠️  Le compte vente configuré n'existe pas ou n'est pas actif.")
                        else:
                            # Créer l'écriture comptable de débit (caisse augmente)
                            ecriture_debit = EcritureComptable(
                                journal_id=journal.id,
                                compte_comptable_id=compte_debit.id,
                                debit=payment_data['amount'],
                                credit=0,
                                ordre=1,
                                libelle=f"Encaissement - {reservation.get_client_name()}"
                            )
                            session.add(ecriture_debit)
                            
                            # Créer l'écriture comptable de crédit (client diminue - paiement reçu)
                            ecriture_credit = EcritureComptable(
                                journal_id=journal.id,
                                compte_comptable_id=compte_credit.id,
                                debit=0,
                                credit=payment_data['amount'],
                                ordre=2,
                                libelle=f"Paiement reçu - {reservation.get_client_name()}"
                            )
                            session.add(ecriture_credit)
                            print(f"📊 Écritures comptables créées: Débit {compte_debit.numero} / Crédit {compte_credit.numero}")
            
            session.commit()
            
            # Émettre le signal de succès
            self.payment_added.emit(payment)
            
            session.close()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Erreur lors de la création du paiement: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(f"Erreur lors de la création du paiement: {str(e)}")
            session.close()
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
    
    def get_payments_by_date(self, target_date):
        """
        Récupérer tous les paiements pour une date donnée
        
        Args:
            target_date (date): Date pour laquelle récupérer les paiements
            
        Returns:
            list: Liste des paiements avec les informations utilisateur
        """
        try:
            session = self.get_session()
            
            # Définir les bornes de la journée
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            # Requête avec jointure pour récupérer le nom de l'utilisateur
            payments = session.query(EventPayment)\
                .filter(EventPayment.payment_date.between(start_datetime, end_datetime))\
                .order_by(desc(EventPayment.payment_date))\
                .all()
            
            # Ajouter les noms d'utilisateur
            for payment in payments:
                if payment.user_id:
                    # Requête pour récupérer le nom de l'utilisateur
                    user_name = session.execute(
                        text("SELECT name FROM core_users WHERE id = :user_id"),
                        {"user_id": payment.user_id}
                    ).scalar()
                    payment.user_nom = user_name or "Utilisateur inconnu"
                else:
                    payment.user_nom = "Système"
            
            session.close()
            return payments
            
        except Exception as e:
            print(f"Erreur lors de la récupération des paiements: {str(e)}")
            self.error_occurred.emit(f"Erreur lors de la récupération des paiements: {str(e)}")
            return []
    
    def get_payments_by_date_and_pos(self, target_date, pos_id):
        """
        Récupérer les paiements pour une date et un POS donnés
        
        Args:
            target_date (date): La date cible  
            pos_id (int): L'ID du point de vente
            
        Returns:
            list: Liste des paiements avec les informations utilisateur
        """
        try:
            session = self.get_session()
            
            if isinstance(target_date, datetime):
                target_date = target_date.date()
                
            # Définir les bornes de la journée
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            # Requête pour récupérer les paiements de la date (EventPayment est toujours pour POS 1 - salle de fête)
            payments = session.query(EventPayment)\
                .filter(
                    EventPayment.payment_date.between(start_datetime, end_datetime)
                )\
                .order_by(desc(EventPayment.payment_date))\
                .all()
            
            # Ajouter les noms d'utilisateur et informations supplémentaires
            for payment in payments:
                if payment.user_id:
                    # Requête pour récupérer le nom de l'utilisateur
                    user_name = session.execute(
                        text("SELECT name FROM core_users WHERE id = :user_id"),
                        {"user_id": payment.user_id}
                    ).scalar()
                    payment.user_nom = user_name or "Utilisateur inconnu"
                else:
                    payment.user_nom = "Système"
                
                # Ajouter des alias pour compatibilité avec l'interface
                payment.utilisateur_nom = payment.user_nom
                payment.date_paiement = payment.payment_date
                payment.mode_paiement = payment.payment_method
                payment.montant = payment.amount
            
            session.close()
            return payments
            
        except Exception as e:
            print(f"Erreur lors de la récupération des paiements par date et POS: {str(e)}")
            self.error_occurred.emit(f"Erreur lors de la récupération des paiements: {str(e)}")
            return []

    def calculer_repartition_paiement(self, reservation, montant_paiement):
        """
        Calcule la répartition proportionnelle d'un paiement selon les comptes spécifiques
        
        LOGIQUE SIMPLIFIÉE POUR PAIEMENTS :
        - Utilise directement les montants nets stockés en BDD (déjà après remise)
        - Pas de recalcul de remise car elle a été appliquée à la création de réservation
        - Répartition simple basée sur les proportions des montants nets
        
        Args:
            reservation: Instance de EventReservation
            montant_paiement: Montant du paiement à répartir
            
        Returns:
            dict: {
                'services': {account_id: montant},
                'produits': {account_id: montant},
                'tva': montant_tva,
                'total_ht': montant_ht
            }
        """
        try:
            repartition = {
                'services': {},
                'produits': {},
                'tva': 0.0,
                'total_ht': 0.0
            }
            
            # Total TTC de la réservation (déjà net, après remise)
            total_ttc_net = float(reservation.total_amount or 0)
            taux_tva = float(reservation.tax_rate or 0) / 100
            
            if total_ttc_net <= 0:
                print("⚠️  Total de la réservation = 0, aucune répartition possible")
                return repartition
            
            print(f"📊 Répartition paiement simple: {montant_paiement}€ sur {total_ttc_net}€ net ({montant_paiement/total_ttc_net:.2%})")
            print(f"   Taux TVA: {taux_tva:.1%}")
            
            # === PHASE 1: CALCULER LES TOTAUX NETS DES COMPTES ===
            
            # Calculer les totaux nets des services (déjà après remise en BDD)
            services_details = {}  # {account_id: {'total_ttc_net': x, 'names': []}}
            for service_item in reservation.services:
                service = service_item.service
                if service and hasattr(service, 'account_id') and service.account_id:
                    line_total_ttc_net = float(service_item.line_total or 0)  # Déjà net
                    
                    account_id = service.account_id
                    if account_id not in services_details:
                        services_details[account_id] = {'total_ttc_net': 0, 'names': []}
                    
                    services_details[account_id]['total_ttc_net'] += line_total_ttc_net
                    services_details[account_id]['names'].append(service.name)
            
            # Calculer les totaux nets des produits (déjà après remise en BDD)
            produits_details = {}  # {account_id: {'total_ttc_net': x, 'names': []}}
            for product_item in reservation.products:
                product = product_item.product
                if product and hasattr(product, 'account_id') and product.account_id:
                    line_total_ttc_net = float(product_item.line_total or 0)  # Déjà net
                    
                    account_id = product.account_id
                    if account_id not in produits_details:
                        produits_details[account_id] = {'total_ttc_net': 0, 'names': []}
                    
                    produits_details[account_id]['total_ttc_net'] += line_total_ttc_net
                    produits_details[account_id]['names'].append(product.name)
            
            # === PHASE 2: RÉPARTITION PROPORTIONNELLE SIMPLE ===
            
            # Répartition des services
            for account_id, details in services_details.items():
                proportion = details['total_ttc_net'] / total_ttc_net
                montant_service = montant_paiement * proportion
                repartition['services'][account_id] = montant_service
                
                names_str = ', '.join(details['names'][:3])  # Max 3 noms
                if len(details['names']) > 3:
                    names_str += f" (+{len(details['names'])-3} autres)"
                
                print(f"  🛎️  Services [{names_str}]: {details['total_ttc_net']:.2f}€ net ({proportion:.1%}) -> {montant_service:.2f}€ sur compte {account_id}")
            
            # Répartition des produits
            for account_id, details in produits_details.items():
                proportion = details['total_ttc_net'] / total_ttc_net
                montant_produit = montant_paiement * proportion
                repartition['produits'][account_id] = montant_produit
                
                names_str = ', '.join(details['names'][:3])  # Max 3 noms
                if len(details['names']) > 3:
                    names_str += f" (+{len(details['names'])-3} autres)"
                
                print(f"  📦 Produits [{names_str}]: {details['total_ttc_net']:.2f}€ net ({proportion:.1%}) -> {montant_produit:.2f}€ sur compte {account_id}")
            
            # === PHASE 3: CALCUL DE LA TVA NETTE ===
            
            # Total HT réparti
            total_ht_reparti = sum(repartition['services'].values()) + sum(repartition['produits'].values())
            
            # TVA proportionnelle sur les montants nets
            if taux_tva > 0:
                # La TVA est calculée sur le total net après remise
                tva_totale_nette = float(reservation.tax_amount or 0)  # TVA déjà nette en BDD
                proportion_tva = tva_totale_nette / total_ttc_net if total_ttc_net > 0 else 0
                repartition['tva'] = montant_paiement * proportion_tva
                
                print(f"  🧾 TVA: {tva_totale_nette:.2f}€ nette sur {total_ttc_net:.2f}€ ({proportion_tva:.1%}) -> {repartition['tva']:.2f}€")
            else:
                repartition['tva'] = 0.0
                print(f"  🧾 TVA: 0.00€ (taux 0%)")
            
            repartition['total_ht'] = total_ht_reparti
            
            # === VÉRIFICATION ===
            total_reparti = total_ht_reparti + repartition['tva']
            ecart = abs(total_reparti - montant_paiement)
            
            print(f"  💰 Total HT: {total_ht_reparti:.2f}€")
            print(f"  📊 Total réparti: {total_reparti:.2f}€ (écart: {ecart:.2f}€)")
            
            if ecart > 0.01:  # Plus de 1 centime d'écart
                print(f"  ⚠️  Écart de répartition détecté: {ecart:.2f}€")
            
            return repartition
            
        except Exception as e:
            print(f"❌ Erreur lors du calcul de répartition: {e}")
            import traceback
            traceback.print_exc()
            return {
                'services': {},
                'produits': {},
                'tva': 0.0,
                'total_ht': 0.0
            }

    def creer_ecritures_comptables_reparties(self, session, reservation, payment, repartition, compte_debit_id, compte_tva_id, journal_id):
        """
        Crée les écritures comptables réparties selon les comptes spécifiques
        
        Args:
            session: Session de base de données
            reservation: Instance de EventReservation  
            payment: Instance de EventPayment
            repartition: Résultat de calculer_repartition_paiement
            compte_debit_id: Compte caisse/banque (débit)
            compte_tva_id: Compte TVA collectée
            journal_id: Journal comptable
            
        Returns:
            list: Liste des écritures créées
        """
        try:
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaEcritures as EcritureComptable
            
            ecritures = []
            libelle_base = f"Paiement Réservation: {reservation.get_client_name()}"
            
            # === 1. ÉCRITURE DE DÉBIT (Caisse/Banque) ===
            ecriture_debit = EcritureComptable(
                journal_id=journal_id,
                compte_comptable_id=compte_debit_id,
                debit=payment.amount,
                credit=0,
                ordre=1,
                libelle=libelle_base
            )
            session.add(ecriture_debit)
            ecritures.append(ecriture_debit)
            print(f"  📥 Débit: {payment.amount:.2f} sur compte {compte_debit_id}")
            
            ordre = 2
            
            # === 2. ÉCRITURES DE CRÉDIT POUR LES SERVICES (MONTANT BRUT) ===
            for account_id, montant_net in repartition['services'].items():
                if montant_net > 0:
                    # Si il y a une remise, recalculer le montant brut pour l'écriture
                    if reservation.discount_percent and reservation.discount_percent > 0:
                        facteur_remise = 1 - (reservation.discount_percent / 100)
                        montant_brut = montant_net / facteur_remise if facteur_remise > 0 else montant_net
                    else:
                        montant_brut = montant_net
                    
                    ecriture_service = EcritureComptable(
                        journal_id=journal_id,
                        compte_comptable_id=account_id,
                        debit=0,
                        credit=montant_brut,
                        ordre=ordre,
                        libelle=f"{libelle_base} - Services"
                    )
                    session.add(ecriture_service)
                    ecritures.append(ecriture_service)
                    print(f"  📤 Crédit Services: {montant_brut:.2f} sur compte {account_id} (brut)")
                    ordre += 1
            
            # === 3. ÉCRITURES DE CRÉDIT POUR LES PRODUITS (MONTANT BRUT) ===
            for account_id, montant_net in repartition['produits'].items():
                if montant_net > 0:
                    # Si il y a une remise, recalculer le montant brut pour l'écriture
                    if reservation.discount_percent and reservation.discount_percent > 0:
                        facteur_remise = 1 - (reservation.discount_percent / 100)
                        montant_brut = montant_net / facteur_remise if facteur_remise > 0 else montant_net
                    else:
                        montant_brut = montant_net
                    
                    ecriture_produit = EcritureComptable(
                        journal_id=journal_id,
                        compte_comptable_id=account_id,
                        debit=0,
                        credit=montant_brut,
                        ordre=ordre,
                        libelle=f"{libelle_base} - Produits"
                    )
                    session.add(ecriture_produit)
                    ecritures.append(ecriture_produit)
                    print(f"  📤 Crédit Produits: {montant_brut:.2f} sur compte {account_id} (brut)")
                    ordre += 1
            
            # === 4. ÉCRITURE DE CRÉDIT POUR LA TVA (sur montant brut) ===
            if repartition['tva'] > 0 and compte_tva_id:
                montant_tva_net = repartition['tva']
                
                # Si il y a une remise, recalculer la TVA sur le montant brut
                if reservation.discount_percent and reservation.discount_percent > 0:
                    facteur_remise = 1 - (reservation.discount_percent / 100)
                    montant_tva_brut = montant_tva_net / facteur_remise if facteur_remise > 0 else montant_tva_net
                else:
                    montant_tva_brut = montant_tva_net
                
                ecriture_tva = EcritureComptable(
                    journal_id=journal_id,
                    compte_comptable_id=compte_tva_id,
                    debit=0,
                    credit=montant_tva_brut,
                    ordre=ordre,
                    libelle=f"{libelle_base} - TVA"
                )
                session.add(ecriture_tva)
                ecritures.append(ecriture_tva)
                print(f"  📤 Crédit TVA: {montant_tva_brut:.2f} sur compte {compte_tva_id} (brut)")
                ordre += 1
            
            # === 5. ÉCRITURE DE DÉBIT POUR LA REMISE (si applicable) ===
            # NOUVELLE APPROCHE SIMPLE : Prendre X% du total TTC directement
            if reservation.discount_percent and reservation.discount_percent > 0:
                # Récupérer le compte remise depuis la config
                from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
                config = session.query(ComptaConfig).first()
                if config and config.compte_remise_id:
                    # Calculer la remise comme pourcentage direct du total TTC
                    total_ttc = float(reservation.total_amount or 0)
                    if total_ttc > 0:
                        # Remise totale = X% du total TTC de la réservation
                        remise_totale_reservation = total_ttc * (reservation.discount_percent / 100)
                        
                        # Remise proportionnelle pour ce paiement
                        remise_paiement = (payment.amount / total_ttc) * remise_totale_reservation
                        
                        if remise_paiement > 0:
                            ecriture_remise = EcritureComptable(
                                journal_id=journal_id,
                                compte_comptable_id=config.compte_remise_id,
                                debit=remise_paiement,
                                credit=0,
                                ordre=ordre,
                                libelle=f"{libelle_base} - Remise {reservation.discount_percent}%"
                            )
                            session.add(ecriture_remise)
                            ecritures.append(ecriture_remise)
                            print(f"  💳 Débit Remise: {remise_paiement:.2f} sur compte {config.compte_remise_id} ({reservation.discount_percent}% de {total_ttc}€)")
            
            return ecritures
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des écritures: {e}")
            import traceback
            traceback.print_exc()
            return []
