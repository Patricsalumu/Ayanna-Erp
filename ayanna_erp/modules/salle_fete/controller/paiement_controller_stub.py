"""
Contrôleur stub pour la gestion des paiements du module Salle de Fête
Version temporaire pour contourner les problèmes de compatibilité SQLAlchemy
"""

from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta


class PaiementController(QObject):
    """Contrôleur stub pour la gestion des paiements et réservations"""
    
    # Signaux pour la communication avec l'interface
    payment_added = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        print(f"PaiementController initialisé (mode stub) pour pos_id: {pos_id}")
    
    def get_latest_reservations(self, limit=10):
        """
        Récupérer les dernières réservations (version démo)
        """
        print(f"Récupération des {limit} dernières réservations...")
        
        # Données de démonstration pour les tests
        demo_reservations = [
            {
                'id': 1,
                'reference': '1',
                'client_nom': 'Jean Dupont',
                'client_telephone': '0123456789',
                'event_date': datetime.now() + timedelta(days=5),
                'event_type': 'Mariage',
                'theme': 'Champêtre',
                'guests_count': 50,
                'status': 'confirmed',
                'total_amount': 1500.00,
                'total_services': 800.00,
                'total_products': 700.00,
                'tax_amount': 200.00,
                'discount_percent': 0.00,
                'notes': 'Mariage en extérieur',
                'created_at': datetime.now() - timedelta(days=10),
                'total_paid': 1050.00,
                'balance': 450.00
            },
            {
                'id': 2,
                'reference': '2',
                'client_nom': 'Marie Martin',
                'client_telephone': '0987654321',
                'event_date': datetime.now() + timedelta(days=10),
                'event_type': 'Anniversaire',
                'theme': 'Tropical',
                'guests_count': 30,
                'status': 'confirmed',
                'total_amount': 800.00,
                'total_services': 400.00,
                'total_products': 400.00,
                'tax_amount': 100.00,
                'discount_percent': 5.00,
                'notes': 'Anniversaire 30 ans',
                'created_at': datetime.now() - timedelta(days=5),
                'total_paid': 400.00,
                'balance': 400.00
            },
            {
                'id': 3,
                'reference': '3',
                'client_nom': 'Pierre Durand',
                'client_telephone': '0556781234',
                'event_date': datetime.now() + timedelta(days=15),
                'event_type': 'Baptême',
                'theme': 'Pastel',
                'guests_count': 25,
                'status': 'draft',
                'total_amount': 600.00,
                'total_services': 300.00,
                'total_products': 300.00,
                'tax_amount': 80.00,
                'discount_percent': 0.00,
                'notes': 'Baptême en après-midi',
                'created_at': datetime.now() - timedelta(days=2),
                'total_paid': 0.00,
                'balance': 600.00
            }
        ]
        
        return demo_reservations[:limit]
    
    def search_reservations(self, search_term, search_type='all'):
        """
        Rechercher des réservations par différents critères (version démo)
        """
        print(f"Recherche de réservations: '{search_term}' (type: {search_type})")
        
        all_reservations = self.get_latest_reservations(limit=20)
        
        if not search_term:
            return all_reservations
        
        # Filtrer selon le terme de recherche
        filtered_reservations = []
        search_term_lower = search_term.lower()
        
        for reservation in all_reservations:
            match = False
            
            # Recherche dans le nom du client
            if search_type in ['all', 'client']:
                if search_term_lower in reservation['client_nom'].lower():
                    match = True
            
            # Recherche dans le téléphone
            if search_type in ['all', 'phone']:
                if search_term_lower in reservation['client_telephone']:
                    match = True
            
            # Recherche par ID/référence
            if search_type in ['all', 'id', 'reference']:
                if search_term_lower in str(reservation['id']) or search_term_lower in str(reservation['reference']):
                    match = True
            
            # Recherche dans le type d'événement
            if search_type in ['all']:
                if search_term_lower in reservation['event_type'].lower():
                    match = True
            
            # Recherche dans le thème
            if search_type in ['all']:
                if reservation['theme'] and search_term_lower in reservation['theme'].lower():
                    match = True
            
            if match:
                filtered_reservations.append(reservation)
        
        return filtered_reservations
    
    def filter_reservations_by_date(self, start_date=None, end_date=None):
        """
        Filtrer les réservations par date d'événement (version démo)
        """
        print(f"Filtrage par date: {start_date} à {end_date}")
        
        all_reservations = self.get_latest_reservations(limit=20)
        
        if not start_date and not end_date:
            return all_reservations
        
        filtered_reservations = []
        
        for reservation in all_reservations:
            event_date = reservation['event_date']
            
            include = True
            
            if start_date and event_date < start_date:
                include = False
            
            if end_date and event_date > end_date:
                include = False
            
            if include:
                filtered_reservations.append(reservation)
        
        return filtered_reservations
    
    def get_reservation_details(self, reservation_id):
        """
        Récupérer les détails complets d'une réservation (version démo)
        """
        print(f"Récupération des détails pour la réservation {reservation_id}")
        
        # Trouver la réservation
        reservations = self.get_latest_reservations(limit=20)
        reservation = None
        
        for res in reservations:
            if res['id'] == reservation_id:
                reservation = res
                break
        
        if not reservation:
            return None
        
        # Ajouter les services et produits de démo
        services = [
            {
                'id': 1,
                'name': 'Décoration florale',
                'description': 'Décoration avec fleurs fraîches',
                'quantity': 1,
                'unit_price': 300.00,
                'line_total': 300.00,
                'line_cost': 200.00
            },
            {
                'id': 2,
                'name': 'Animation musicale',
                'description': 'DJ professionnel',
                'quantity': 1,
                'unit_price': 500.00,
                'line_total': 500.00,
                'line_cost': 300.00
            }
        ]
        
        products = [
            {
                'id': 1,
                'name': 'Boissons',
                'description': 'Assortiment de boissons',
                'quantity': 50,
                'unit_price': 8.00,
                'line_total': 400.00,
                'line_cost': 300.00,
                'unit': 'litre'
            },
            {
                'id': 2,
                'name': 'Repas',
                'description': 'Menu 3 services',
                'quantity': reservation['guests_count'],
                'unit_price': 25.00,
                'line_total': reservation['guests_count'] * 25.00,
                'line_cost': reservation['guests_count'] * 15.00,
                'unit': 'personne'
            }
        ]
        
        # Paiements de démo
        payments = []
        if reservation['total_paid'] > 0:
            # Créer des paiements de démo
            if reservation['total_paid'] >= 500:
                payments.append({
                    'id': 1,
                    'amount': 500.00,
                    'payment_method': 'Carte bancaire',
                    'payment_date': datetime.now() - timedelta(days=15),
                    'status': 'validated',
                    'notes': 'Acompte initial'
                })
            
            remaining = reservation['total_paid'] - 500
            if remaining > 0:
                payments.append({
                    'id': 2,
                    'amount': remaining,
                    'payment_method': 'Espèces',
                    'payment_date': datetime.now() - timedelta(days=5),
                    'status': 'validated',
                    'notes': 'Deuxième versement'
                })
        
        # Ajouter les détails
        reservation['services'] = services
        reservation['products'] = products
        reservation['payments'] = payments
        
        return reservation
    
    def create_payment(self, payment_data):
        """
        Créer un nouveau paiement (version démo)
        """
        print(f"Création d'un paiement de {payment_data['amount']} € pour la réservation {payment_data['reservation_id']}")
        
        try:
            # Simuler la création du paiement
            print(f"Paiement créé avec succès:")
            print(f"- Montant: {payment_data['amount']} €")
            print(f"- Méthode: {payment_data['payment_method']}")
            print(f"- Date: {payment_data['payment_date']}")
            print(f"- Notes: {payment_data.get('notes', 'Aucune')}")
            
            # Émettre le signal de succès
            self.payment_added.emit(payment_data)
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création du paiement: {str(e)}")
            self.error_occurred.emit(f"Erreur lors de la création du paiement: {str(e)}")
            return False
    
    def get_payments_by_reservation(self, reservation_id):
        """
        Récupérer tous les paiements d'une réservation (version démo)
        """
        print(f"Récupération des paiements pour la réservation {reservation_id}")
        
        # Simuler des paiements
        if reservation_id == 1:
            return [
                {
                    'payment_date': datetime.now() - timedelta(days=15),
                    'amount': 500.00,
                    'payment_method': 'Carte bancaire',
                    'notes': 'Acompte initial'
                },
                {
                    'payment_date': datetime.now() - timedelta(days=5),
                    'amount': 550.00,
                    'payment_method': 'Espèces',
                    'notes': 'Deuxième versement'
                }
            ]
        elif reservation_id == 2:
            return [
                {
                    'payment_date': datetime.now() - timedelta(days=10),
                    'amount': 400.00,
                    'payment_method': 'Chèque',
                    'notes': 'Acompte'
                }
            ]
        else:
            return []
    
    def get_payment_balance(self, reservation_id):
        """
        Calculer le solde de paiement d'une réservation (version démo)
        """
        reservation = self.get_reservation_details(reservation_id)
        
        if not reservation:
            return {'total_amount': 0, 'total_paid': 0, 'balance': 0}
        
        return {
            'total_amount': reservation['total_amount'],
            'total_paid': reservation['total_paid'],
            'balance': reservation['balance']
        }
