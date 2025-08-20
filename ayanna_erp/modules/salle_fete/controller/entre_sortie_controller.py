"""
Contrôleur pour la gestion des entrées et sorties de caisse du module Salle de Fête
Gère les dépenses avec intégration comptable automatique
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ayanna_erp.modules.salle_fete.model.salle_fete import EventExpense, get_database_manager


class EntreSortieController(QObject):
    """Contrôleur pour la gestion des entrées et sorties de caisse"""
    
    # Signaux pour la communication avec la vue
    expense_added = pyqtSignal(object)
    expense_updated = pyqtSignal(object)
    expense_deleted = pyqtSignal(int)
    expenses_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        
    def set_pos_id(self, pos_id):
        """Définir l'ID du point de vente"""
        self.pos_id = pos_id
        
    def create_expense(self, expense_data):
        """
        Créer une nouvelle dépense avec intégration comptable
        
        Args:
            expense_data (dict): Données de la dépense
                - libelle: Libellé de la dépense
                - montant: Montant de la dépense
                - compte_id: ID du compte de charges (débit)
                - categorie: Catégorie de la dépense
                - fournisseur: Nom du fournisseur (optionnel)
                - facture: Numéro de facture (optionnel)
                - description: Description détaillée
                - reservation_id: ID de la réservation (optionnel)
                
        Returns:
            EventExpense: La dépense créée ou None
        """
        try:
            from ayanna_erp.modules.comptabilite.model.comptabilite import (
                ComptaConfig,
                ComptaEcritures as EcritureComptable, 
                ComptaJournaux as JournalComptable, 
                ComptaComptes as CompteComptable
            )
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
                
            # Créer la dépense
            expense = EventExpense(
                pos_id=self.pos_id,
                reservation_id=expense_data.get('reservation_id'),  # Optionnel
                expense_type=expense_data.get('categorie', 'Dépense générale'),
                description=expense_data.get('libelle'),
                amount=expense_data.get('montant'),
                expense_date=datetime.now(),
                supplier=expense_data.get('fournisseur'),
                invoice_number=expense_data.get('facture'),
                payment_method='Espèces',  # Toujours espèces pour commencer
                account_id=expense_data.get('compte_id'),
                created_by=1,  # TODO: Récupérer l'ID de l'utilisateur connecté
                created_at=datetime.now()
            )
            
            session.add(expense)
            session.flush()  # Pour obtenir l'ID
            
            print(f"💸 Dépense créée: {expense.description} - {expense.amount}€")
            
            # === INTEGRATION COMPTABLE ===
            # Récupérer la configuration comptable pour ce POS
            config = session.query(ComptaConfig).filter_by(pos_id=self.pos_id).first()
            if not config:
                print("⚠️  Configuration comptable manquante pour ce point de vente")
            else:
                # Créer la ligne de journal comptable
                libelle = f"Dépense: {expense.description}"
                journal = JournalComptable(
                    enterprise_id=1,  # TODO: Récupérer l'ID de l'entreprise du POS
                    libelle=libelle,
                    montant=expense.amount,
                    type_operation="sortie",  # 'sortie' pour une dépense
                    reference=f"EXP-{expense.id}",
                    description=f"Dépense ID: {expense.id} - {expense.expense_type}",
                    user_id=1,  # TODO: Récupérer l'ID de l'utilisateur connecté
                    date_operation=datetime.now()
                )
                session.add(journal)
                session.flush()  # Pour avoir l'id du journal

                # Récupérer les comptes configurés
                compte_debit = session.query(CompteComptable).filter(CompteComptable.id == expense_data.get('compte_id')).first()
                if not compte_debit:
                    raise Exception("Le compte de charges sélectionné n'existe pas ou n'est pas actif.")

                compte_credit = session.query(CompteComptable).filter(CompteComptable.id == config.compte_caisse_id).first()
                if not compte_credit:
                    raise Exception("Le compte caisse configuré n'existe pas ou n'est pas actif.")

                # Créer l'écriture comptable de débit (charge augmente)
                ecriture_debit = EcritureComptable(
                    journal_id=journal.id,
                    compte_comptable_id=compte_debit.id,
                    debit=expense.amount,
                    credit=0,
                    ordre=1,
                    libelle=f"Dépense - {expense.description}"
                )
                session.add(ecriture_debit)
                
                # Créer l'écriture comptable de crédit (caisse diminue)
                ecriture_credit = EcritureComptable(
                    journal_id=journal.id,
                    compte_comptable_id=compte_credit.id,
                    debit=0,
                    credit=expense.amount,
                    ordre=2,
                    libelle=f"Sortie caisse - {expense.description}"
                )
                session.add(ecriture_credit)
                print(f"📊 Écritures comptables créées: Débit {compte_debit.numero} / Crédit {compte_credit.numero}")
                
            session.commit()
            session.refresh(expense)
            
            print(f"✅ Dépense enregistrée avec succès: {expense.description}")
            self.expense_added.emit(expense)
            return expense
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la création de la dépense: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_expenses_by_date(self, target_date):
        """Récupérer les dépenses pour une date donnée"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            if isinstance(target_date, datetime):
                target_date = target_date.date()
                
            # Définir les bornes de la journée
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            expenses = session.query(EventExpense).filter(
                EventExpense.pos_id == self.pos_id,
                EventExpense.expense_date.between(start_datetime, end_datetime)
            ).order_by(EventExpense.expense_date.desc()).all()
            
            return expenses
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des dépenses: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
    
    def get_all_expenses(self, date_from=None, date_to=None):
        """
        Récupérer toutes les dépenses avec filtres optionnels
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Filtrage principal par pos_id
            query = session.query(EventExpense).filter(
                EventExpense.pos_id == self.pos_id
            )
            
            # Filtres optionnels
            if date_from:
                query = query.filter(EventExpense.expense_date >= date_from)
            if date_to:
                query = query.filter(EventExpense.expense_date <= date_to)
                
            expenses = query.order_by(EventExpense.expense_date.desc()).all()
            
            self.expenses_loaded.emit(expenses)
            return expenses
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des dépenses: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def update_expense(self, expense_id, expense_data):
        """Mettre à jour une dépense existante"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            expense = session.query(EventExpense).filter(
                EventExpense.id == expense_id,
                EventExpense.pos_id == self.pos_id
            ).first()
            
            if not expense:
                error_msg = f"Dépense {expense_id} non trouvée"
                self.error_occurred.emit(error_msg)
                return False
                
            # Mettre à jour les champs
            expense.expense_type = expense_data.get('categorie', expense.expense_type)
            expense.description = expense_data.get('libelle', expense.description)
            expense.amount = expense_data.get('montant', expense.amount)
            expense.supplier = expense_data.get('fournisseur', expense.supplier)
            expense.invoice_number = expense_data.get('facture', expense.invoice_number)
            expense.account_id = expense_data.get('compte_id', expense.account_id)
            
            session.commit()
            session.refresh(expense)
            
            print(f"✅ Dépense {expense_id} mise à jour avec succès")
            self.expense_updated.emit(expense)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la mise à jour de la dépense: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def delete_expense(self, expense_id):
        """Supprimer une dépense"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            expense = session.query(EventExpense).filter(
                EventExpense.id == expense_id,
                EventExpense.pos_id == self.pos_id
            ).first()
            
            if not expense:
                error_msg = f"Dépense {expense_id} non trouvée"
                self.error_occurred.emit(error_msg)
                return False
                
            # TODO: Supprimer aussi les écritures comptables liées
            session.delete(expense)
            session.commit()
            
            print(f"✅ Dépense supprimée: {expense.description}")
            self.expense_deleted.emit(expense_id)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la suppression: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def get_expenses_statistics(self, start_date=None, end_date=None):
        """
        Récupérer les statistiques des dépenses
        
        Args:
            start_date (datetime): Date de début (optionnelle)
            end_date (datetime): Date de fin (optionnelle)
            
        Returns:
            dict: Statistiques des dépenses
        """
        try:
            from sqlalchemy import func
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Query de base
            expenses_query = session.query(EventExpense).filter(
                EventExpense.pos_id == self.pos_id
            )
            
            if start_date:
                expenses_query = expenses_query.filter(EventExpense.expense_date >= start_date)
            
            if end_date:
                expenses_query = expenses_query.filter(EventExpense.expense_date <= end_date)
            
            # Calculer les statistiques
            total_expenses = expenses_query.with_entities(func.sum(EventExpense.amount)).scalar() or 0
            expense_count = expenses_query.count()
            
            # Grouper par catégorie
            categories = expenses_query.with_entities(
                EventExpense.expense_type,
                func.sum(EventExpense.amount),
                func.count(EventExpense.id)
            ).group_by(EventExpense.expense_type).all()
            
            categories_stats = []
            for category, amount, count in categories:
                categories_stats.append({
                    'category': category,
                    'total_amount': float(amount),
                    'expense_count': count,
                    'percentage': (float(amount) / total_expenses * 100) if total_expenses > 0 else 0
                })
            
            session.close()
            
            return {
                'total_expenses': float(total_expenses),
                'expense_count': expense_count,
                'average_expense': float(total_expenses) / expense_count if expense_count > 0 else 0,
                'categories': categories_stats
            }
            
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {str(e)}")
            self.error_occurred.emit(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {
                'total_expenses': 0,
                'expense_count': 0,
                'average_expense': 0,
                'categories': []
            }
    
    def get_expenses_by_date_and_pos(self, target_date, pos_id):
        """
        Récupérer les dépenses pour une date et un POS donnés
        
        Args:
            target_date (date): La date cible
            pos_id (int): L'ID du point de vente
            
        Returns:
            list: Liste des dépenses
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            if isinstance(target_date, datetime):
                target_date = target_date.date()
                
            # Définir les bornes de la journée
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            expenses = session.query(EventExpense).filter(
                EventExpense.pos_id == pos_id,
                EventExpense.expense_date.between(start_datetime, end_datetime)
            ).order_by(EventExpense.expense_date.desc()).all()
            
            # Ajouter des informations supplémentaires
            for expense in expenses:
                expense.libelle = expense.description
                expense.categorie = expense.expense_type
                expense.montant = expense.amount
                expense.date_creation = expense.expense_date
                expense.utilisateur_nom = "Utilisateur"  # TODO: récupérer le vrai nom d'utilisateur
            
            return expenses
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des dépenses: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
