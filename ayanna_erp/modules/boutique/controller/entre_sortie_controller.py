"""
Contrôleur pour la gestion des entrées/sorties du module Boutique
Gère les dépenses via la table shop_expenses
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date

# Import du modèle shop_expenses
from ayanna_erp.modules.boutique.model.models import ShopExpense
from ayanna_erp.database.database_manager import DatabaseManager


class EntreSortieController(QObject):
    """Contrôleur pour la gestion des entrées/sorties"""
    
    # Signaux pour la communication avec la vue
    expense_added = pyqtSignal(object)
    expense_updated = pyqtSignal(object)
    expense_deleted = pyqtSignal(int)
    expenses_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
        
    def set_pos_id(self, pos_id):
        """Définir l'ID de l'entreprise"""
        self.pos_id = pos_id
        
    def create_expense(self, expense_data):
        """
        Créer une nouvelle dépense
        
        Args:
            expense_data (dict): Données de la dépense
            
        Returns:
            ShopExpense: La dépense créée ou None
        """
        try:
            with self.db_manager.get_session() as session:
                expense = ShopExpense(
                    pos_id=self.pos_id,
                    expense_type=expense_data.get('expense_type', 'Autre'),
                    description=expense_data.get('description', ''),
                    amount=float(expense_data.get('amount', 0.0)),
                    notes=expense_data.get('notes', ''),
                    user_id=expense_data.get('user_id', 1),
                    expense_date=expense_data.get('expense_date', datetime.now()),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(expense)
                session.commit()
                session.refresh(expense)
                
                print(f"✅ Dépense créée: {expense.description} - {expense.amount} FC")
                self.expense_added.emit(expense)
                return expense
                
        except IntegrityError as e:
            error_msg = f"Erreur d'intégrité: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Erreur lors de la création de la dépense: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
    
    def get_expenses_by_date(self, target_date):
        """
        Récupérer les dépenses pour une date donnée
        
        Args:
            target_date (date): Date cible
            
        Returns:
            list: Liste des dépenses
        """
        try:
            with self.db_manager.get_session() as session:
                # Convertir en date si nécessaire
                if isinstance(target_date, datetime):
                    target_date = target_date.date()
                
                # Requête pour récupérer les dépenses du jour
                from sqlalchemy import func, and_
                
                expenses = session.query(ShopExpense).filter(
                    and_(
                        ShopExpense.pos_id == self.pos_id,
                        func.date(ShopExpense.expense_date) == target_date
                    )
                ).order_by(ShopExpense.expense_date.desc()).all()
                
                print(f"✅ {len(expenses)} dépenses trouvées pour le {target_date}")
                return expenses
                
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des dépenses: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
    
    def get_all_expenses(self, limit=100):
        """
        Récupérer toutes les dépenses
        
        Args:
            limit (int): Limite du nombre de résultats
            
        Returns:
            list: Liste des dépenses
        """
        try:
            with self.db_manager.get_session() as session:
                expenses = session.query(ShopExpense).filter(
                    ShopExpense.pos_id == self.pos_id
                ).order_by(ShopExpense.expense_date.desc()).limit(limit).all()
                
                self.expenses_loaded.emit(expenses)
                return expenses
                
        except Exception as e:
            error_msg = f"Erreur lors du chargement des dépenses: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
    
    def update_expense(self, expense_id, expense_data):
        """
        Mettre à jour une dépense
        
        Args:
            expense_id (int): ID de la dépense
            expense_data (dict): Nouvelles données
            
        Returns:
            bool: True si succès
        """
        try:
            with self.db_manager.get_session() as session:
                expense = session.query(ShopExpense).filter(
                    ShopExpense.id == expense_id,
                    ShopExpense.pos_id == self.pos_id
                ).first()
                
                if not expense:
                    self.error_occurred.emit("Dépense introuvable")
                    return False
                
                # Mettre à jour les champs
                expense.expense_type = expense_data.get('expense_type', expense.expense_type)
                expense.description = expense_data.get('description', expense.description)
                expense.amount = float(expense_data.get('amount', expense.amount))
                expense.notes = expense_data.get('notes', expense.notes)
                expense.updated_at = datetime.now()
                
                session.commit()
                session.refresh(expense)
                
                print(f"✅ Dépense modifiée: {expense.description}")
                self.expense_updated.emit(expense)
                return True
                
        except Exception as e:
            error_msg = f"Erreur lors de la modification de la dépense: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def delete_expense(self, expense_id):
        """
        Supprimer une dépense
        
        Args:
            expense_id (int): ID de la dépense
            
        Returns:
            bool: True si succès
        """
        try:
            with self.db_manager.get_session() as session:
                expense = session.query(ShopExpense).filter(
                    ShopExpense.id == expense_id,
                    ShopExpense.pos_id == self.pos_id
                ).first()
                
                if not expense:
                    self.error_occurred.emit("Dépense introuvable")
                    return False
                
                expense_description = expense.description
                session.delete(expense)
                session.commit()
                
                print(f"✅ Dépense supprimée: {expense_description}")
                self.expense_deleted.emit(expense_id)
                return True
                
        except Exception as e:
            error_msg = f"Erreur lors de la suppression de la dépense: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def get_expenses_statistics(self, start_date=None, end_date=None):
        """
        Récupérer les statistiques des dépenses
        
        Args:
            start_date (date): Date de début
            end_date (date): Date de fin
            
        Returns:
            dict: Statistiques
        """
        try:
            with self.db_manager.get_session() as session:
                from sqlalchemy import func, and_
                
                query = session.query(ShopExpense).filter(
                    ShopExpense.pos_id == self.pos_id
                )
                
                # Filtres par date
                if start_date:
                    query = query.filter(func.date(ShopExpense.expense_date) >= start_date)
                if end_date:
                    query = query.filter(func.date(ShopExpense.expense_date) <= end_date)
                
                expenses = query.all()
                
                # Calculs
                total_amount = sum(expense.amount for expense in expenses)
                total_count = len(expenses)
                
                # Grouper par type
                by_type = {}
                for expense in expenses:
                    expense_type = expense.expense_type
                    if expense_type not in by_type:
                        by_type[expense_type] = {'count': 0, 'amount': 0}
                    by_type[expense_type]['count'] += 1
                    by_type[expense_type]['amount'] += expense.amount
                
                return {
                    'total_amount': total_amount,
                    'total_count': total_count,
                    'average_amount': total_amount / total_count if total_count > 0 else 0,
                    'by_type': by_type
                }
                
        except Exception as e:
            error_msg = f"Erreur lors du calcul des statistiques: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return {
                'total_amount': 0,
                'total_count': 0,
                'average_amount': 0,
                'by_type': {}
            }
    
    def search_expenses(self, query, start_date=None, end_date=None):
        """
        Rechercher des dépenses
        
        Args:
            query (str): Terme de recherche
            start_date (date): Date de début
            end_date (date): Date de fin
            
        Returns:
            list: Liste des dépenses correspondantes
        """
        try:
            with self.db_manager.get_session() as session:
                from sqlalchemy import func, and_, or_
                
                db_query = session.query(ShopExpense).filter(
                    ShopExpense.pos_id == self.pos_id
                )
                
                # Filtres par date
                if start_date:
                    db_query = db_query.filter(func.date(ShopExpense.expense_date) >= start_date)
                if end_date:
                    db_query = db_query.filter(func.date(ShopExpense.expense_date) <= end_date)
                
                # Recherche textuelle
                if query:
                    search_pattern = f"%{query}%"
                    db_query = db_query.filter(
                        or_(
                            ShopExpense.description.ilike(search_pattern),
                            ShopExpense.expense_type.ilike(search_pattern),
                            ShopExpense.notes.ilike(search_pattern)
                        )
                    )
                
                expenses = db_query.order_by(ShopExpense.expense_date.desc()).all()
                return expenses
                
        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []