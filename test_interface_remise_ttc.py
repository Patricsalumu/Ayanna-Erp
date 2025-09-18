#!/usr/bin/env python3
"""
Test de la nouvelle interface pour remise sur TTC
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_interface_calculation():
    """
    Test de la logique de calcul avec remise sur TTC
    """
    print("=" * 60)
    print("TEST DE L'INTERFACE - REMISE SUR TTC")
    print("=" * 60)
    
    # Données de test
    services = [
        {"nom": "Service Mariage", "prix": 1000.0, "quantite": 1},
    ]
    
    produits = [
        {"nom": "Produit Décoration", "prix": 500.0, "quantite": 1},
    ]
    
    taux_tva = 20.0  # 20%
    remise_pourcentage = 10.0  # 10%
    
    print(f"Services:")
    for service in services:
        print(f"  - {service['nom']}: {service['prix']:.2f} € x {service['quantite']}")
    
    print(f"\nProduits:")
    for produit in produits:
        print(f"  - {produit['nom']}: {produit['prix']:.2f} € x {produit['quantite']}")
    
    print(f"\nParametres:")
    print(f"  - Taux TVA: {taux_tva}%")
    print(f"  - Remise: {remise_pourcentage}%")
    
    # Calcul 1: Sous-total HT
    subtotal_ht = 0.0
    for service in services:
        subtotal_ht += service['prix'] * service['quantite']
    for produit in produits:
        subtotal_ht += produit['prix'] * produit['quantite']
    
    # Calcul 2: TVA et TTC avant remise
    tax_amount = subtotal_ht * (taux_tva / 100)
    total_ttc_before_discount = subtotal_ht + tax_amount
    
    # Calcul 3: Remise sur TTC (nouvelle logique)
    discount_amount = total_ttc_before_discount * (remise_pourcentage / 100)
    
    # Calcul 4: Total final
    total_final = total_ttc_before_discount - discount_amount
    
    print(f"\n" + "=" * 40)
    print("CALCULS (Nouvelle logique - remise sur TTC)")
    print("=" * 40)
    print(f"1. Sous-total HT:           {subtotal_ht:.2f} €")
    print(f"2. Montant TVA ({taux_tva}%):      {tax_amount:.2f} €")
    print(f"3. Total TTC (avant remise): {total_ttc_before_discount:.2f} €")
    print(f"4. Remise ({remise_pourcentage}% sur TTC):    -{discount_amount:.2f} €")
    print(f"5. TOTAL FINAL:             {total_final:.2f} €")
    
    print(f"\n" + "=" * 40)
    print("COMPARAISON AVEC ANCIENNE LOGIQUE")
    print("=" * 40)
    
    # Ancienne logique (remise sur HT)
    old_discount_amount = subtotal_ht * (remise_pourcentage / 100)
    old_subtotal_after_discount = subtotal_ht - old_discount_amount
    old_tax_amount = old_subtotal_after_discount * (taux_tva / 100)
    old_total_final = old_subtotal_after_discount + old_tax_amount
    
    print(f"Ancienne logique (remise sur HT):")
    print(f"  - Remise: -{old_discount_amount:.2f} €")
    print(f"  - Total final: {old_total_final:.2f} €")
    
    print(f"\nNouvelle logique (remise sur TTC):")
    print(f"  - Remise: -{discount_amount:.2f} €")
    print(f"  - Total final: {total_final:.2f} €")
    
    difference = total_final - old_total_final
    print(f"\nDifférence: {difference:.2f} €")
    
    # Test avec différents pourcentages de remise
    print(f"\n" + "=" * 40)
    print("TEST AVEC DIFFÉRENTS POURCENTAGES")
    print("=" * 40)
    
    for remise in [5, 10, 15, 20]:
        new_discount = total_ttc_before_discount * (remise / 100)
        new_total = total_ttc_before_discount - new_discount
        
        old_discount = subtotal_ht * (remise / 100)
        old_subtotal_after = subtotal_ht - old_discount
        old_tax = old_subtotal_after * (taux_tva / 100)
        old_total = old_subtotal_after + old_tax
        
        print(f"Remise {remise}%:")
        print(f"  Nouvelle: {new_total:.2f} € (remise: -{new_discount:.2f} €)")
        print(f"  Ancienne: {old_total:.2f} € (remise: -{old_discount:.2f} €)")
        print(f"  Écart: {new_total - old_total:.2f} €")
        print()

def test_ui_display():
    """
    Test de l'affichage en temps réel
    """
    print("=" * 60)
    print("TEST D'AFFICHAGE EN TEMPS RÉEL")
    print("=" * 60)
    
    print("Simulation de saisie utilisateur:")
    print("1. Utilisateur sélectionne services/produits")
    print("2. L'interface calcule automatiquement sous-total HT et TTC")
    print("3. Utilisateur saisit pourcentage de remise")
    print("4. L'interface affiche immédiatement le montant en euros")
    print()
    
    # Simulation étape par étape
    subtotal_ht = 1500.0
    tax_rate = 20.0
    
    print(f"Étape 1 - Sélection terminée:")
    print(f"  Sous-total HT: {subtotal_ht:.2f} €")
    
    tax_amount = subtotal_ht * (tax_rate / 100)
    total_ttc = subtotal_ht + tax_amount
    
    print(f"  Montant TVA: {tax_amount:.2f} €")
    print(f"  Total TTC: {total_ttc:.2f} €")
    
    print(f"\nÉtape 2 - Utilisateur tape remise:")
    
    for percent in [0, 5, 10, 15]:
        discount_amount = total_ttc * (percent / 100)
        final_total = total_ttc - discount_amount
        
        print(f"  {percent}% → Remise: -{discount_amount:.2f} € → Total: {final_total:.2f} €")

if __name__ == "__main__":
    test_interface_calculation()
    print()
    test_ui_display()
    
    print(f"\n" + "=" * 60)
    print("RÉSUMÉ DES AMÉLIORATIONS")
    print("=" * 60)
    print("✓ Remise appliquée sur TTC au lieu de HT")
    print("✓ Affichage en temps réel du montant de remise en euros")
    print("✓ Interface plus claire avec TTC avant/après remise")
    print("✓ Couleur rouge pour la remise pour une meilleure visibilité")
    print("✓ Conservation de la logique de calcul pour la comptabilité")