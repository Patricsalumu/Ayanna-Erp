"""
Contrôleur pour la génération de rapports dans le module Salle de Fête
Gestion des statistiques d'événements, revenus et dépenses
"""

import sys
import os
from datetime import datetime, timedelta, date
from calendar import monthrange
from sqlalchemy import func, and_, extract, text
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import (
    EventReservation, EventPayment, EventExpense, EventService, 
    EventProduct, EventReservationService, EventReservationProduct
)


class RapportController:
    """Contrôleur pour la génération des rapports"""
    
    def __init__(self, pos_id=1):
        self.db_manager = DatabaseManager()
        self.pos_id = pos_id
        
    def get_monthly_events_data(self, year: int, month: int, pos_id: int = None):
        """
        Récupérer les données des événements pour un mois donné
        """
        if pos_id is None:
            pos_id = self.pos_id
        session = self.db_manager.get_session()
        try:
            # Date de début et fin du mois
            start_date = datetime(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = datetime(year, month, last_day, 23, 59, 59)
            
            # Requête pour les événements du mois
            events = session.query(EventReservation)\
                .filter(
                    EventReservation.pos_id == pos_id,
                    EventReservation.event_date >= start_date,
                    EventReservation.event_date <= end_date
                )\
                .order_by(EventReservation.event_date)\
                .all()
            
            # Calcul des statistiques par jour
            events_by_day = {}
            for day in range(1, last_day + 1):
                events_by_day[day] = 0
                
            for event in events:
                day = event.event_date.day
                events_by_day[day] += 1
            
            # Calcul des revenus du mois (paiements)
            total_revenue = session.query(func.sum(EventPayment.amount))\
                .join(EventReservation)\
                .filter(
                    EventReservation.pos_id == pos_id,
                    EventPayment.payment_date >= start_date,
                    EventPayment.payment_date <= end_date,
                    EventPayment.status == 'validated'
                )\
                .scalar() or 0.0
            
            # Calcul des dépenses du mois
            total_expenses = session.query(func.sum(EventExpense.amount))\
                .filter(
                    EventExpense.pos_id == pos_id,
                    EventExpense.expense_date >= start_date,
                    EventExpense.expense_date <= end_date
                )\
                .scalar() or 0.0
            
            # TOP 5 des services
            top_services = session.query(
                EventService.name,
                func.count(EventReservationService.id).label('count'),
                func.sum(EventReservationService.quantity * EventReservationService.unit_price).label('total')
            )\
            .join(EventReservationService)\
            .join(EventReservation)\
            .filter(
                EventReservation.pos_id == pos_id,
                EventReservation.event_date >= start_date,
                EventReservation.event_date <= end_date
            )\
            .group_by(EventService.id, EventService.name)\
            .order_by(func.count(EventReservationService.id).desc())\
            .limit(5)\
            .all()
            
            return {
                'events_count': len(events),
                'events_by_day': events_by_day,
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'net_result': total_revenue - total_expenses,
                'average_revenue': total_revenue / len(events) if events else 0,
                'top_services': top_services,
                'period': f"{start_date.strftime('%B %Y')}"
            }
            
        finally:
            session.close()
    
    def get_yearly_events_data(self, year: int, pos_id: int = None):
        """
        Récupérer les données des événements pour une année donnée
        """
        if pos_id is None:
            pos_id = self.pos_id
        session = self.db_manager.get_session()
        try:
            # Date de début et fin de l'année
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            
            # Statistiques par mois
            events_by_month = {}
            for month in range(1, 13):
                events_by_month[month] = 0
            
            # Requête pour les événements de l'année
            events = session.query(EventReservation)\
                .filter(
                    EventReservation.pos_id == pos_id,
                    EventReservation.event_date >= start_date,
                    EventReservation.event_date <= end_date
                )\
                .all()
            
            for event in events:
                month = event.event_date.month
                events_by_month[month] += 1
            
            # Calcul des revenus de l'année
            total_revenue = session.query(func.sum(EventPayment.amount))\
                .join(EventReservation)\
                .filter(
                    EventReservation.pos_id == pos_id,
                    EventPayment.payment_date >= start_date,
                    EventPayment.payment_date <= end_date,
                    EventPayment.status == 'validated'
                )\
                .scalar() or 0.0
            
            # Calcul des dépenses de l'année
            total_expenses = session.query(func.sum(EventExpense.amount))\
                .filter(
                    EventExpense.pos_id == pos_id,
                    EventExpense.expense_date >= start_date,
                    EventExpense.expense_date <= end_date
                )\
                .scalar() or 0.0
            
            # TOP 5 des services de l'année
            top_services = session.query(
                EventService.name,
                func.count(EventReservationService.id).label('count'),
                func.sum(EventReservationService.quantity * EventReservationService.unit_price).label('total')
            )\
            .join(EventReservationService)\
            .join(EventReservation)\
            .filter(
                EventReservation.pos_id == pos_id,
                EventReservation.event_date >= start_date,
                EventReservation.event_date <= end_date
            )\
            .group_by(EventService.id, EventService.name)\
            .order_by(func.count(EventReservationService.id).desc())\
            .limit(5)\
            .all()
            
            return {
                'events_count': len(events),
                'events_by_month': events_by_month,
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'net_result': total_revenue - total_expenses,
                'average_revenue': total_revenue / len(events) if events else 0,
                'top_services': top_services,
                'period': f"Année {year}"
            }
            
        finally:
            session.close()
    
    def get_financial_report_data(self, start_date: datetime, end_date: datetime, pos_id: int = None):
        """
        Récupérer les données financières pour une période donnée
        """
        if pos_id is None:
            pos_id = self.pos_id
        session = self.db_manager.get_session()
        try:
            # Revenus par méthode de paiement
            payment_methods = session.query(
                EventPayment.payment_method,
                func.sum(EventPayment.amount).label('total')
            )\
            .join(EventReservation)\
            .filter(
                EventReservation.pos_id == pos_id,
                EventPayment.payment_date >= start_date,
                EventPayment.payment_date <= end_date,
                EventPayment.status == 'validated'
            )\
            .group_by(EventPayment.payment_method)\
            .order_by(func.sum(EventPayment.amount).desc())\
            .all()
            
            # Total des revenus
            total_revenue = sum(pm.total for pm in payment_methods)
            
            # Total des dépenses
            total_expenses = session.query(func.sum(EventExpense.amount))\
                .filter(
                    EventExpense.pos_id == pos_id,
                    EventExpense.expense_date >= start_date,
                    EventExpense.expense_date <= end_date
                )\
                .scalar() or 0.0
            
            # Revenus par type d'événement
            revenue_by_type = session.query(
                EventReservation.event_type,
                func.sum(EventPayment.amount).label('total')
            )\
            .join(EventPayment)\
            .filter(
                EventReservation.pos_id == pos_id,
                EventPayment.payment_date >= start_date,
                EventPayment.payment_date <= end_date,
                EventPayment.status == 'validated'
            )\
            .group_by(EventReservation.event_type)\
            .order_by(func.sum(EventPayment.amount).desc())\
            .all()
            
            # Calcul des revenus services vs produits
            service_revenue = session.query(func.sum(EventReservationService.quantity * EventReservationService.unit_price))\
                .join(EventReservation)\
                .filter(
                    EventReservation.pos_id == pos_id,
                    EventReservation.event_date >= start_date,
                    EventReservation.event_date <= end_date
                )\
                .scalar() or 0.0
            
            product_revenue = session.query(func.sum(EventReservationProduct.quantity * EventReservationProduct.unit_price))\
                .join(EventReservation)\
                .filter(
                    EventReservation.pos_id == pos_id,
                    EventReservation.event_date >= start_date,
                    EventReservation.event_date <= end_date
                )\
                .scalar() or 0.0
            
            # Données pour graphique courbes (par jour)
            daily_data = self._get_daily_financial_data(start_date, end_date, pos_id, session)
            
            return {
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'net_result': total_revenue - total_expenses,
                'service_revenue': service_revenue,
                'product_revenue': product_revenue,
                'payment_methods': payment_methods,
                'revenue_by_type': revenue_by_type,
                'daily_data': daily_data,
                'period': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            }
            
        finally:
            session.close()
    
    def _get_daily_financial_data(self, start_date: datetime, end_date: datetime, pos_id: int, session):
        """
        Récupérer les données financières par jour pour le graphique courbes
        """
        daily_revenue = {}
        daily_expenses = {}
        
        # Générer tous les jours de la période
        current_date = start_date
        while current_date <= end_date:
            day_key = current_date.strftime('%Y-%m-%d')
            daily_revenue[day_key] = 0.0
            daily_expenses[day_key] = 0.0
            current_date += timedelta(days=1)
        
        # Revenus par jour
        revenues = session.query(
            func.date(EventPayment.payment_date).label('date'),
            func.sum(EventPayment.amount).label('total')
        )\
        .join(EventReservation)\
        .filter(
            EventReservation.pos_id == pos_id,
            EventPayment.payment_date >= start_date,
            EventPayment.payment_date <= end_date,
            EventPayment.status == 'validated'
        )\
        .group_by(func.date(EventPayment.payment_date))\
        .all()
        
        for rev in revenues:
            daily_revenue[str(rev.date)] = float(rev.total)
        
        # Dépenses par jour
        expenses = session.query(
            func.date(EventExpense.expense_date).label('date'),
            func.sum(EventExpense.amount).label('total')
        )\
        .filter(
            EventExpense.pos_id == pos_id,
            EventExpense.expense_date >= start_date,
            EventExpense.expense_date <= end_date
        )\
        .group_by(func.date(EventExpense.expense_date))\
        .all()
        
        for exp in expenses:
            daily_expenses[str(exp.date)] = float(exp.total)
        
        return {
            'dates': list(daily_revenue.keys()),
            'revenues': list(daily_revenue.values()),
            'expenses': list(daily_expenses.values())
        }
    
    def get_comparison_data(self, current_year: int, current_month: int, pos_id: int = None):
        """
        Récupérer les données de comparaison avec la période précédente
        """
        if pos_id is None:
            pos_id = self.pos_id
        session = self.db_manager.get_session()
        try:
            # Mois précédent
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year
            
            # Données du mois actuel
            current_data = self.get_monthly_events_data(current_year, current_month, pos_id)
            
            # Données du mois précédent
            prev_data = self.get_monthly_events_data(prev_year, prev_month, pos_id)
            
            # Calcul des pourcentages d'évolution
            revenue_evolution = 0
            if prev_data['total_revenue'] > 0:
                revenue_evolution = ((current_data['total_revenue'] - prev_data['total_revenue']) / prev_data['total_revenue']) * 100
            
            net_result_evolution = 0
            if prev_data['net_result'] != 0:
                net_result_evolution = ((current_data['net_result'] - prev_data['net_result']) / abs(prev_data['net_result'])) * 100
            
            return {
                'revenue_evolution': revenue_evolution,
                'net_result_evolution': net_result_evolution,
                'previous_period': f"{prev_year}-{prev_month:02d}"
            }
            
        finally:
            session.close()
