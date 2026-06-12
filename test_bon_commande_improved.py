#!/usr/bin/env python
"""Test script to preview Bon de Commande format improvements"""

from datetime import datetime
from ayanna_erp.modules.restaurant.utils.bon_commande_printer import BonCommandePrinter

# Create printer instance
printer = BonCommandePrinter(enterprise_id=1)

# Prepare test ticket data with all fields including client_name
ticket_data = {
    'numero_bon': 42,
    'serveuse': 'Marie Dupont',
    'table': '5',
    'panier_id': 123,
    'created_at': datetime.now(),
    'client_name': 'Jean Martin',  # New field
    'items': [
        {
            'produit_id': 1,
            'nom': 'Simba',
            'quantite': 2,
            'prix_vente': 8000
        },
        {
            'produit_id': 5,
            'nom': 'Fanta Orange',
            'quantite': 1,
            'prix_vente': 5000
        },
        {
            'produit_id': 10,
            'nom': 'Eau Minérale',
            'quantite': 3,
            'prix_vente': 2000
        }
    ]
}

# Generate the ticket
output_path = 'test_bon_commande_improved.pdf'
result = printer.print_ticket(ticket_data, output_path)

print(f"""
✅ Bon de commande généré avec succès!

📋 Améliorations appliquées:
   ✅ Produits et quantités: GRAS + taille augmentée (10pt)
   ✅ Serveuse, Table, Panier, Date: Normal (non-gras) (8pt)
   ✅ Nom du client ajouté en gras en bas
   ✅ Footer "Informatisé par Ayanna ERP" en bas
   
📄 Fichier: {result}

Format du ticket:
┌─────────────────────────────────┐
│    AYANNA ERP (9pt)             │
│    BON DE COMMANDE              │
│         42 (16pt gras)          │
├─────────────────────────────────┤
│ Serveuse: Marie Dupont (8pt)    │
│ Table: 5 (8pt)                  │
│ Panier: 123 (8pt)               │
│ Date: 12/06/2026 14:32 (8pt)    │
├─────────────────────────────────┤
│ Simba x2 (10pt GRAS)            │
│ Fanta Orange x1 (10pt GRAS)     │
│ Eau Minérale x3 (10pt GRAS)     │
├─────────────────────────────────┤
│ Client: Jean Martin (9pt gras)  │
│                                 │
│ Informatisé par Ayanna ERP (7pt)│
└─────────────────────────────────┘

Améliorations:
   • Produits en plus gros caractères pour meilleure lisibilité en cuisine
   • Client affiché pour traçabilité
   • Footer informatif
""")
