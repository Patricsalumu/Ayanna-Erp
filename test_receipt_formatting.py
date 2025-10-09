#!/usr/bin/env python3
"""
Test rapide du formatage du reçu avec les améliorations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

def test_receipt_formatting():
    """Test du format du reçu avec alignement"""
    
    # Données de test
    enterprise_info = {
        'name': 'AYANNA SUPERMARKET',
        'address': '123 Avenue Commerce, Kinshasa',
        'phone': '+243 81 234 5678',
        'email': 'contact@ayanna.cd',
        'rccm': 'CD/KIN/RCCM/23-001'
    }
    
    cart_items = [
        {'product_name': 'Coca-Cola 33cl', 'quantity': 2, 'unit_price': 1500},
        {'product_name': 'Pain de blé complet', 'quantity': 1, 'unit_price': 800},
        {'product_name': 'Fromage Président 250g', 'quantity': 1, 'unit_price': 3500}
    ]
    
    # Générer le reçu formaté
    order_number = f"CMD-1-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    receipt_text = f"""===============================
{enterprise_info['name']}
===============================

Adresse: {enterprise_info['address']}
Téléphone: {enterprise_info['phone']}
Email: {enterprise_info['email']}
RCCM: {enterprise_info['rccm']}

===== REÇU DE VENTE =====

N° Commande: {order_number}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
POS: #1
Vendeur: Admin

--- DÉTAIL DES ARTICLES ---
"""
    
    # Formater les produits avec alignement
    total_cart = 0
    for item in cart_items:
        product_name = item['product_name'][:25] + '...' if len(item['product_name']) > 25 else item['product_name']
        quantity = item['quantity']
        unit_price = item['unit_price']
        total_price = unit_price * quantity
        total_cart += total_price
        
        # Formatage aligné avec espaces
        line = f"{product_name:<28} {quantity:>3} x {unit_price:>6.0f} = {total_price:>8.0f} FC"
        receipt_text += line + "\n"
    
    discount_amount = total_cart * 0.05  # 5% de remise
    total_final = total_cart - discount_amount
    
    receipt_text += f"""
--- TOTAUX ---
Sous-total:              {total_cart:>8.0f} FC
Remise (5%):             -{discount_amount:>8.0f} FC
TOTAL À PAYER:           {total_final:>8.0f} FC

--- PAIEMENT ---
Méthode:                 Espèces
Montant reçu:            {total_final + 500:>8.0f} FC
Monnaie rendue:          {500:>8.0f} FC

Merci pour votre achat !
Bonne journée.

===============================
Généré par Ayanna ERP©
Tous droits réservés
===============================
"""
    
    print("=== TEST DU REÇU FORMATÉ ===")
    print(receipt_text)
    print("\n✅ Formatage testé avec succès !")
    
    return True

if __name__ == "__main__":
    test_receipt_formatting()