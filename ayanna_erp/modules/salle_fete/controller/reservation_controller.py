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
        from ayanna_erp.modules.comptabilite.model.comptabilite import (
            ComptaEcritures as EcritureComptable, 
            ComptaJournaux as JournalComptable, 
            ComptaComptes as CompteComptable
        )
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
            
            if deposit_amount > 0:
                from ayanna_erp.modules.salle_fete.model.salle_fete import EventPayment
                from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
                
                payment = EventPayment(
                    reservation_id=reservation.id,
                    amount=deposit_amount,
                    payment_method='Espèces',  # Simplifier en utilisant espèces par défaut
                    payment_date=datetime.now(),
                    status='validated',
                    user_id=1,  # TODO: Récupérer l'ID de l'utilisateur connecté
                    notes=f"Acompte automatique pour réservation {reservation.client_nom} {reservation.client_prenom}"
                )
                session.add(payment)
                session.flush()  # Pour avoir l'ID du paiement
                print(f"💰 Paiement d'acompte créé: {deposit_amount}€")
                
                # Récupérer la configuration comptable pour ce POS
                config = session.query(ComptaConfig).filter_by(pos_id=self.pos_id).first()
                if not config:
                    print("⚠️  Configuration comptable manquante pour ce point de vente")
                else:
                    # Créer la ligne de journal comptable
                    libelle = f"Paiement Accompte Reservation: {reservation.client_nom} {reservation.client_prenom}"
                    journal = JournalComptable(
                        enterprise_id=1,  # TODO: Récupérer l'ID de l'entreprise du POS
                        libelle=libelle,
                        montant=deposit_amount,
                        type_operation="entree",  # 'entree' pour un paiement
                        reference=f"PAY-{payment.id}",
                        description=f"Acompte réservation ID: {reservation.id}",
                        user_id=1,  # TODO: Récupérer l'ID de l'utilisateur connecté
                        date_operation=datetime.now()
                    )
                    session.add(journal)
                    session.flush()  # Pour avoir l'id du journal

                    # Récupérer les comptes configurés
                    compte_debit = session.query(CompteComptable).filter(CompteComptable.id == config.compte_caisse_id).first()
                    if not compte_debit:
                        raise Exception("Le compte caisse configuré n'existe pas ou n'est pas actif.")

                    # Vérifier si le compte TVA est configuré
                    compte_tva_id = config.compte_tva_id if hasattr(config, 'compte_tva_id') else None
                    if compte_tva_id:
                        compte_tva = session.query(CompteComptable).filter(CompteComptable.id == compte_tva_id).first()
                        if not compte_tva:
                            print("⚠️  Compte TVA configuré mais inexistant, TVA sera ignorée")
                            compte_tva_id = None

                    # Calculer la répartition du paiement selon les comptes spécifiques
                    repartition = self.calculer_repartition_paiement(reservation, deposit_amount)
                    
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
                        ecriture_debit = EcritureComptable(
                            journal_id=journal.id,
                            compte_comptable_id=compte_debit.id,
                            debit=deposit_amount,
                            credit=0,
                            ordre=1,
                            libelle=f"Encaissement acompte - {reservation.client_nom}"
                        )
                        session.add(ecriture_debit)
                        
                        # Utiliser le compte vente général en fallback
                        compte_vente_general = session.query(CompteComptable).filter(CompteComptable.id == config.compte_vente_id).first()
                        if compte_vente_general:
                            ecriture_credit = EcritureComptable(
                                journal_id=journal.id,
                                compte_comptable_id=compte_vente_general.id,
                                debit=0,
                                credit=deposit_amount,
                                ordre=2,
                                libelle=f"Avance reçue - {reservation.client_nom}"
                            )
                            session.add(ecriture_credit)
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

    def calculer_repartition_paiement(self, reservation, montant_paiement):
        """
        Calcule la répartition proportionnelle d'un paiement selon les comptes spécifiques
        
        NOUVELLE LOGIQUE : 
        - reservation.total_amount contient le TTC SANS remise
        - Calculer les proportions basées sur les montants BRUTS de chaque service/produit
        - La remise est gérée séparément dans les écritures comptables
        
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
            
            # Total TTC SANS remise (nouveau système)
            total_ttc_sans_remise = float(reservation.total_amount or 0)
            
            if total_ttc_sans_remise <= 0:
                print("⚠️  Total de la réservation = 0, aucune répartition possible")
                return repartition
            
            print(f"📊 Répartition paiement: {montant_paiement}€ sur {total_ttc_sans_remise}€ TTC brut ({montant_paiement/total_ttc_sans_remise:.2%})")
            
            # === CALCUL DES MONTANTS BRUTS (HT SANS REMISE) ===
            
            # Services : montant brut = prix_unitaire * quantité (SANS remise)
            services_details = {}  # {account_id: {'total_brut': x, 'names': []}}
            for service_item in reservation.services:
                service = service_item.service
                if service and hasattr(service, 'account_id') and service.account_id:
                    # Montant brut HT (sans remise)
                    montant_ht_brut = float(service_item.unit_price or 0) * float(service_item.quantity or 1)
                    
                    account_id = service.account_id
                    if account_id not in services_details:
                        services_details[account_id] = {'total_brut': 0, 'names': []}
                    
                    services_details[account_id]['total_brut'] += montant_ht_brut
                    services_details[account_id]['names'].append(service.name)
            
            # Produits : montant brut = prix_unitaire * quantité (SANS remise)
            produits_details = {}  # {account_id: {'total_brut': x, 'names': []}}
            for product_item in reservation.products:
                product = product_item.product
                if product and hasattr(product, 'account_id') and product.account_id:
                    # Montant brut HT (sans remise)
                    montant_ht_brut = float(product_item.unit_price or 0) * float(product_item.quantity or 1)
                    
                    account_id = product.account_id
                    if account_id not in produits_details:
                        produits_details[account_id] = {'total_brut': 0, 'names': []}
                    
                    produits_details[account_id]['total_brut'] += montant_ht_brut
                    produits_details[account_id]['names'].append(product.name)
            
            # === RÉPARTITION PROPORTIONNELLE SELON MONTANT BRUT / TOTAL TTC BRUT ===
            
            # Répartition des services
            for account_id, details in services_details.items():
                proportion = details['total_brut'] / total_ttc_sans_remise
                montant_service = montant_paiement * proportion
                repartition['services'][account_id] = {
                    'montant_net': montant_service,
                    'total_brut': details['total_brut'],
                    'proportion': proportion
                }
                
                names_str = ', '.join(details['names'][:3])
                if len(details['names']) > 3:
                    names_str += f" (+{len(details['names'])-3} autres)"
                
                print(f"  🛎️  Services [{names_str}]: {details['total_brut']:.2f}€ brut ({proportion:.1%}) -> {montant_service:.2f}€ sur compte {account_id}")
            
            # Répartition des produits
            for account_id, details in produits_details.items():
                proportion = details['total_brut'] / total_ttc_sans_remise
                montant_produit = montant_paiement * proportion
                repartition['produits'][account_id] = {
                    'montant_net': montant_produit,
                    'total_brut': details['total_brut'],
                    'proportion': proportion
                }
                
                names_str = ', '.join(details['names'][:3])
                if len(details['names']) > 3:
                    names_str += f" (+{len(details['names'])-3} autres)"
                
                print(f"  📦 Produits [{names_str}]: {details['total_brut']:.2f}€ brut ({proportion:.1%}) -> {montant_produit:.2f}€ sur compte {account_id}")
            
            # === CALCUL DE LA TVA ===
            
            # TVA brute de la réservation (calculée sur montants bruts)
            tva_totale_brute = float(reservation.tax_amount or 0)
            if tva_totale_brute > 0:
                proportion_tva = tva_totale_brute / total_ttc_sans_remise
                repartition['tva'] = montant_paiement * proportion_tva
                repartition['tva_proportion'] = proportion_tva  # Stocker la proportion
                print(f"  🧾 TVA: {tva_totale_brute:.2f}€ brute ({proportion_tva:.1%}) -> {repartition['tva']:.2f}€")
            else:
                repartition['tva'] = 0.0
                repartition['tva_proportion'] = 0.0
                print(f"  🧾 TVA: 0.00€")
            
            # Total HT
            total_ht_reparti = sum([item['montant_net'] for item in repartition['services'].values()]) + sum([item['montant_net'] for item in repartition['produits'].values()])
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
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaEcritures as EcritureComptable, ComptaConfig
            
            ecritures = []
            libelle_base = f"Paiement Réservation: {reservation.client_nom} {reservation.client_prenom}"
            
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
            
            # === 2. ÉCRITURES DE CRÉDIT PROPORTIONNELLES (ACCOMPTE + PART DE REMISE) ===
            # LOGIQUE CORRECTE : Créditer proportionnellement (accompte + part de remise par compte)
            total_ttc_sans_remise = float(reservation.total_amount or 0)
            remise_totale = total_ttc_sans_remise * (reservation.discount_percent / 100) if reservation.discount_percent else 0
            montant_a_ventiler = payment.amount + remise_totale  # Accompte + Remise totale
            
            print(f"  📊 Ventilation: Accompte {payment.amount:.2f}€ + Remise {remise_totale:.2f}€ = {montant_a_ventiler:.2f}€")
            
            for account_id, details in repartition['services'].items():
                if details['montant_net'] > 0:
                    # Utiliser la proportion déjà calculée correctement
                    proportion = details['proportion']
                    montant_credit = montant_a_ventiler * proportion
                    
                    ecriture_service = EcritureComptable(
                        journal_id=journal_id,
                        compte_comptable_id=account_id,
                        debit=0,
                        credit=montant_credit,
                        ordre=ordre,
                        libelle=f"{libelle_base} - Services (proportionnel)"
                    )
                    session.add(ecriture_service)
                    ecritures.append(ecriture_service)
                    print(f"  📤 Crédit Services: {montant_credit:.2f} sur compte {account_id} (proportion: {proportion:.1%})")
                    ordre += 1
            
            # === 3. ÉCRITURES DE CRÉDIT POUR LES PRODUITS (PROPORTIONNEL) ===
            for account_id, details in repartition['produits'].items():
                if details['montant_net'] > 0:
                    # Utiliser la proportion déjà calculée correctement
                    proportion = details['proportion']
                    montant_credit = montant_a_ventiler * proportion
                    
                    ecriture_produit = EcritureComptable(
                        journal_id=journal_id,
                        compte_comptable_id=account_id,
                        debit=0,
                        credit=montant_credit,
                        ordre=ordre,
                        libelle=f"{libelle_base} - Produits (proportionnel)"
                    )
                    session.add(ecriture_produit)
                    ecritures.append(ecriture_produit)
                    print(f"  📤 Crédit Produits: {montant_credit:.2f} sur compte {account_id} (proportion: {proportion:.1%})")
                    ordre += 1
            
            # === 4. ÉCRITURE DE CRÉDIT POUR LA TVA (PROPORTIONNEL) ===
            if repartition.get('tva', 0) > 0 and compte_tva_id:
                # Utiliser la proportion déjà calculée correctement
                proportion_tva = repartition.get('tva_proportion', 0)
                montant_tva_credit = montant_a_ventiler * proportion_tva
                
                ecriture_tva = EcritureComptable(
                    journal_id=journal_id,
                    compte_comptable_id=compte_tva_id,
                    debit=0,
                    credit=montant_tva_credit,
                    ordre=ordre,
                    libelle=f"{libelle_base} - TVA (proportionnel)"
                )
                session.add(ecriture_tva)
                ecritures.append(ecriture_tva)
                print(f"  📤 Crédit TVA: {montant_tva_credit:.2f} sur compte {compte_tva_id} (proportion: {proportion_tva:.1%})")
                ordre += 1
            
            # === 5. ÉCRITURE DE DÉBIT POUR LA REMISE (TOTALITÉ DE LA REMISE) ===
            # NOUVELLE LOGIQUE : Débiter TOUTE la remise en une seule fois lors de la création
            if reservation.discount_percent and reservation.discount_percent > 0:
                # Récupérer le compte remise depuis la config
                config = session.query(ComptaConfig).first()
                if config and config.compte_remise_id:
                    # Calculer la REMISE TOTALE sur le TTC de la réservation
                    total_ttc_brut = float(reservation.total_amount or 0)  # TTC stocké SANS remise
                    remise_totale = total_ttc_brut * (reservation.discount_percent / 100)
                    
                    if remise_totale > 0:
                        ecriture_remise = EcritureComptable(
                            journal_id=journal_id,
                            compte_comptable_id=config.compte_remise_id,
                            debit=remise_totale,
                            credit=0,
                            ordre=1,
                            libelle=f"{libelle_base} - Remise {reservation.discount_percent}% (TOTALE)"
                        )
                        session.add(ecriture_remise)
                        ecritures.append(ecriture_remise)
                        print(f"  💳 Débit Remise TOTALE: {remise_totale:.2f}€ sur compte {config.compte_remise_id}")
                        print(f"      Total TTC brut: {total_ttc_brut:.2f}€ × {reservation.discount_percent}% = {remise_totale:.2f}€")
            
            return ecritures
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des écritures: {e}")
            import traceback
            traceback.print_exc()
            return []
            return []
