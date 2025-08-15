"""
Script de test pour les réservations
Test d'ajout de réservations d'exemple
"""

import sys
import os
from datetime import datetime, timedelta

# Ajouter le chemin de l'application
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
from ayanna_erp.modules.salle_fete.controller.client_controller import ClientController
from ayanna_erp.modules.salle_fete.controller.mainWindow_controller import MainWindowController


def test_reservations():
    """Tester l'ajout de réservations d'exemple"""
    print("🧪 Test des réservations...")
    
    # Initialiser la base de données
    main_controller = MainWindowController(pos_id=1)
    main_controller.initialize_database()
    
    # Contrôleurs
    client_controller = ClientController(pos_id=1)
    reservation_controller = ReservationController(pos_id=1)
    
    # Variables pour stocker les données
    clients_data = []
    reservations_data = []
    
    # Mock des signaux pour récupérer les données
    def mock_clients_loaded(clients):
        nonlocal clients_data
        clients_data = clients
    
    def mock_reservations_loaded(reservations):
        nonlocal reservations_data
        reservations_data = reservations
    
    # Connecter les signaux
    client_controller.clients_loaded.connect(mock_clients_loaded)
    reservation_controller.reservations_loaded.connect(mock_reservations_loaded)
    
    try:
        # Charger les clients
        client_controller.load_clients()
        
        if not clients_data:
            print("❌ Aucun client trouvé. Les réservations nécessitent des clients.")
            return
        
        print(f"✅ {len(clients_data)} clients trouvés")
        
        # Créer quelques réservations d'exemple
        reservations_exemple = [
            {
                'partner_id': clients_data[0]['id'],
                'event_date': datetime.now() + timedelta(days=30),
                'event_type': 'Mariage',
                'guests_count': 120,
                'notes': 'Mariage de printemps avec décoration florale'
            },
            {
                'partner_id': clients_data[1]['id'] if len(clients_data) > 1 else clients_data[0]['id'],
                'event_date': datetime.now() + timedelta(days=45),
                'event_type': 'Anniversaire',
                'guests_count': 50,
                'notes': 'Anniversaire 50 ans avec animation DJ'
            },
            {
                'partner_id': clients_data[2]['id'] if len(clients_data) > 2 else clients_data[0]['id'],
                'event_date': datetime.now() + timedelta(days=60),
                'event_type': 'Baptême',
                'guests_count': 30,
                'notes': 'Baptême avec repas traditionnel'
            }
        ]
        
        # Ajouter les réservations
        for i, reservation_data in enumerate(reservations_exemple):
            success = reservation_controller.add_reservation(reservation_data)
            if success:
                print(f"✅ Réservation {i+1} ajoutée")
            else:
                print(f"❌ Erreur lors de l'ajout de la réservation {i+1}")
        
        # Charger et afficher toutes les réservations
        print("\n📋 Liste des réservations:")
        reservation_controller.load_reservations()
        
        if reservations_data:
            for reservation in reservations_data:
                print(f"  • {reservation['reference']} - {reservation['client_nom']} - {reservation['event_type']} - {reservation['event_date'].strftime('%d/%m/%Y')}")
        else:
            print("  Aucune réservation trouvée")
        
        print("\n🎉 Test des réservations terminé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Fonction principale"""
    app = QApplication(sys.argv)
    
    # Mock du signal pour récupérer les données
    def mock_reservations_loaded(reservations):
        # Stocker les données dans le contrôleur pour le test
        reservation_controller.reservations_data = reservations
    
    def mock_clients_loaded(clients):
        client_controller.clients_data = clients
    
    # Créer les contrôleurs
    client_controller = ClientController(pos_id=1)
    reservation_controller = ReservationController(pos_id=1)
    
    # Connecter les signaux mock
    client_controller.clients_loaded.connect(mock_clients_loaded)
    reservation_controller.reservations_loaded.connect(mock_reservations_loaded)
    
    # Exécuter le test
    test_reservations()


if __name__ == "__main__":
    main()
