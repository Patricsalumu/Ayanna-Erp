#!/usr/bin/env python3
"""
Script de test pour vérifier les quantités des services dans la base de données
"""

import sqlite3
import sys
import os

# Ajouter le chemin vers les modules
sys.path.append('.')

def test_service_quantities():
    """Tester les quantités de services dans la base de données"""
    
    # Connexion à la base de données
    db_path = "ayanna_erp.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Vérification des quantités de services dans la base de données...")
    print("=" * 60)
    
    # Vérifier la table event_reservation_services
    cursor.execute("""
        SELECT 
            ers.id,
            ers.reservation_id,
            ers.service_id,
            ers.quantity,
            ers.unit_price,
            ers.line_total,
            es.name as service_name
        FROM event_reservation_services ers
        JOIN event_services es ON ers.service_id = es.id
        ORDER BY ers.reservation_id DESC, ers.id DESC
        LIMIT 10
    """)
    
    services = cursor.fetchall()
    
    if services:
        print("📋 Derniers services dans les réservations:")
        print("-" * 60)
        for service in services:
            id_service, reservation_id, service_id, quantity, unit_price, line_total, service_name = service
            print(f"Réservation #{reservation_id}")
            print(f"  Service: {service_name}")
            print(f"  Quantité: {quantity}")
            print(f"  Prix unitaire: {unit_price:.2f} €")
            print(f"  Total ligne: {line_total:.2f} €")
            print(f"  ✅ Quantité {'> 1' if quantity > 1 else '= 1'}")
            print("-" * 30)
    else:
        print("❌ Aucun service trouvé dans les réservations")
    
    # Vérifier les totaux des réservations
    cursor.execute("""
        SELECT 
            id,
            client_nom,
            total_services,
            total_amount,
            event_date
        FROM event_reservations
        ORDER BY id DESC
        LIMIT 5
    """)
    
    reservations = cursor.fetchall()
    
    if reservations:
        print("\n📊 Dernières réservations - Totaux:")
        print("-" * 60)
        for reservation in reservations:
            id_res, client_nom, total_services, total_amount, event_date = reservation
            print(f"Réservation #{id_res} - {client_nom}")
            print(f"  Total services: {total_services:.2f} €")
            print(f"  Total général: {total_amount:.2f} €")
            print(f"  Date: {event_date}")
            print("-" * 30)
    
    conn.close()
    print("\n✅ Test terminé")

if __name__ == "__main__":
    test_service_quantities()
