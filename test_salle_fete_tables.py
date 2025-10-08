#!/usr/bin/env python3
"""
Test de création spécifique des tables salle de fête
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

print("=== TEST CREATION TABLES SALLE DE FETE ===")

try:
    from ayanna_erp.database.base import Base
    from ayanna_erp.database.database_manager import DatabaseManager
    from sqlalchemy import text, create_engine
    
    # Importer les modèles salle de fête
    from ayanna_erp.modules.salle_fete.model.salle_fete import (
        EventClient, EventService, EventReservation, EventReservationService,
        EventReservationProduct, EventPayment, EventStockMovement, EventExpense
    )
    print("OK Modeles salle de fete importes")
    
    # Créer un engine temporaire pour tester
    engine = create_engine('sqlite:///test_salle_fete.db', echo=False)
    
    # Créer uniquement les tables salle de fête
    Base.metadata.create_all(bind=engine)
    print("OK Base.metadata.create_all() execute")
    
    # Vérifier les tables créées
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    tables_result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
    table_names = [row[0] for row in tables_result]
    
    print(f"Tables creees dans test_salle_fete.db: {len(table_names)}")
    for table in table_names:
        print(f"  - {table}")
    
    # Vérifier spécifiquement les tables event_*
    event_tables = [t for t in table_names if t.startswith('event_')]
    print(f"\nTables event_* trouvees: {len(event_tables)}")
    for table in event_tables:
        print(f"  - {table}")
    
    session.close()
    
    # Supprimer le fichier de test
    if os.path.exists('test_salle_fete.db'):
        os.remove('test_salle_fete.db')
        print("Fichier de test supprime")
    
    print("TEST TERMINE")
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()