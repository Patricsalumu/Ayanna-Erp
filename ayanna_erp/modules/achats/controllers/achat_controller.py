"""
Contrôleur principal pour le module Achats
Gestion des fournisseurs, commandes, paiements et intégration stock
"""

from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.achats.models import (
    CoreFournisseur, AchatCommande, AchatCommandeLigne, 
    AchatDepense, EtatCommande
)
from ayanna_erp.modules.core.models import CoreProduct
from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot, StockMovement
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes, ComptaEcritures, ComptaJournaux, ComptaConfig


class AchatController:
    """Contrôleur principal pour la gestion des achats"""
    
    def __init__(self, pos_id: int = None, entreprise_id: int = None):
        self.db_manager = DatabaseManager()
        self.pos_id = pos_id
        self.entreprise_id = entreprise_id or self.db_manager.get_current_enterprise_id()
    
    # ================== GESTION DES FOURNISSEURS ==================
    
    def get_fournisseurs(self, session: Session, search: str = None) -> List[CoreFournisseur]:
        """Récupère la liste des fournisseurs"""
        query = session.query(CoreFournisseur)
        
        if search:
            query = query.filter(
                or_(
                    CoreFournisseur.nom.ilike(f"%{search}%"),
                    CoreFournisseur.email.ilike(f"%{search}%"),
                    CoreFournisseur.telephone.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(CoreFournisseur.nom).all()
    
    def create_fournisseur(self, session: Session, nom: str, telephone: str = None, 
                          adresse: str = None, email: str = None) -> CoreFournisseur:
        """Crée un nouveau fournisseur"""
        fournisseur = CoreFournisseur(
            nom=nom,
            telephone=telephone,
            adresse=adresse,
            email=email
        )
        session.add(fournisseur)
        session.commit()
        session.refresh(fournisseur)
        return fournisseur
    
    def update_fournisseur(self, session: Session, fournisseur_id: int, 
                          **kwargs) -> CoreFournisseur:
        """Met à jour un fournisseur"""
        fournisseur = session.query(CoreFournisseur).get(fournisseur_id)
        if not fournisseur:
            raise ValueError("Fournisseur introuvable")
        
        for key, value in kwargs.items():
            if hasattr(fournisseur, key):
                setattr(fournisseur, key, value)
        
        session.commit()
        session.refresh(fournisseur)
        return fournisseur
    
    # ================== GESTION DES COMMANDES ==================
    
    def generate_numero_commande(self, session: Session) -> str:
        """Génère un numéro de commande unique"""
        today = datetime.now()
        prefix = f"CMD{today.strftime('%Y%m%d')}"
        
        # Trouver le dernier numéro du jour
        last_cmd = session.query(AchatCommande).filter(
            AchatCommande.numero.like(f"{prefix}%")
        ).order_by(AchatCommande.numero.desc()).first()
        
        if last_cmd:
            last_num = int(last_cmd.numero.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}-{next_num:04d}"
    
    def create_commande(self, session: Session, entrepot_id: int, 
                       fournisseur_id: int = None, lignes: List[Dict] = None,
                       remise_global: Decimal = Decimal('0')) -> AchatCommande:
        """
        Crée une nouvelle commande d'achat
        
        Args:
            session: Session SQLAlchemy
            entrepot_id: ID de l'entrepôt de destination
            fournisseur_id: ID du fournisseur (optionnel)
            lignes: Liste des lignes de commande [{produit_id, quantite, prix_unitaire, remise_ligne}]
            remise_global: Remise globale sur la commande
        """
        # Vérifier que l'entrepôt existe
        entrepot = session.query(StockWarehouse).get(entrepot_id)
        if not entrepot:
            raise ValueError("Entrepôt introuvable")
        
        # Générer le numéro de commande
        numero = self.generate_numero_commande(session)
        
        # Créer la commande
        commande = AchatCommande(
            numero=numero,
            fournisseur_id=fournisseur_id,
            entrepot_id=entrepot_id,
            utilisateur_id=1,  # TODO: utiliser l'utilisateur connecté
            remise_global=remise_global,
            montant_total=Decimal('0')  # Sera calculé
        )
        session.add(commande)
        session.flush()  # Pour obtenir l'ID
        
        # Ajouter les lignes
        if lignes:
            for ligne_data in lignes:
                self.add_ligne_commande(session, commande.id, **ligne_data)
        
        # Recalculer le total
        self.recalculer_total_commande(session, commande.id)
        
        session.commit()
        session.refresh(commande)
        return commande
    
    def add_ligne_commande(self, session: Session, commande_id: int, 
                          produit_id: int, quantite: Decimal, prix_unitaire: Decimal,
                          remise_ligne: Decimal = Decimal('0')) -> AchatCommandeLigne:
        """Ajoute une ligne à une commande"""
        # Vérifier que le produit existe
        produit = session.query(CoreProduct).get(produit_id)
        if not produit:
            raise ValueError("Produit introuvable")
        
        # Calculer le total de la ligne
        total_ligne = (quantite * prix_unitaire) - remise_ligne
        
        ligne = AchatCommandeLigne(
            bon_commande_id=commande_id,
            produit_id=produit_id,
            quantite=quantite,
            prix_unitaire=prix_unitaire,
            remise_ligne=remise_ligne,
            total_ligne=total_ligne
        )
        session.add(ligne)
        session.flush()
        
        return ligne
    
    def update_ligne_commande(self, session: Session, ligne_id: int,
                             quantite: Decimal = None, prix_unitaire: Decimal = None,
                             remise_ligne: Decimal = None) -> AchatCommandeLigne:
        """Met à jour une ligne de commande"""
        ligne = session.query(AchatCommandeLigne).get(ligne_id)
        if not ligne:
            raise ValueError("Ligne de commande introuvable")
        
        # Vérifier que la commande est encore modifiable
        if ligne.commande.etat != EtatCommande.ENCOURS:
            raise ValueError("Cette commande ne peut plus être modifiée")
        
        # Mettre à jour les valeurs
        if quantite is not None:
            ligne.quantite = quantite
        if prix_unitaire is not None:
            ligne.prix_unitaire = prix_unitaire
        if remise_ligne is not None:
            ligne.remise_ligne = remise_ligne
        
        # Recalculer le total de la ligne
        ligne.total_ligne = (ligne.quantite * ligne.prix_unitaire) - ligne.remise_ligne
        
        # Recalculer le total de la commande
        self.recalculer_total_commande(session, ligne.bon_commande_id)
        
        session.commit()
        return ligne
    
    def delete_ligne_commande(self, session: Session, ligne_id: int) -> bool:
        """Supprime une ligne de commande"""
        ligne = session.query(AchatCommandeLigne).get(ligne_id)
        if not ligne:
            return False
        
        # Vérifier que la commande est encore modifiable
        if ligne.commande.etat != EtatCommande.ENCOURS:
            raise ValueError("Cette commande ne peut plus être modifiée")
        
        commande_id = ligne.bon_commande_id
        session.delete(ligne)
        
        # Recalculer le total de la commande
        self.recalculer_total_commande(session, commande_id)
        
        session.commit()
        return True
    
    def recalculer_total_commande(self, session: Session, commande_id: int) -> Decimal:
        """Recalcule le montant total d'une commande"""
        commande = session.query(AchatCommande).get(commande_id)
        if not commande:
            raise ValueError("Commande introuvable")
        
        total_lignes = sum(ligne.total_ligne for ligne in commande.lignes)
        commande.montant_total = total_lignes - commande.remise_global
        
        return commande.montant_total
    
    def get_commandes(self, session: Session, etat: EtatCommande = None,
                     fournisseur_id: int = None, limit: int = 100) -> List[AchatCommande]:
        """Récupère la liste des commandes avec filtres"""
        query = session.query(AchatCommande)
        
        if etat:
            query = query.filter(AchatCommande.etat == etat)
        if fournisseur_id:
            query = query.filter(AchatCommande.fournisseur_id == fournisseur_id)
        
        return query.order_by(AchatCommande.date_commande.desc()).limit(limit).all()
    
    def get_commande_by_id(self, session: Session, commande_id: int) -> Optional[AchatCommande]:
        """Récupère une commande par son ID"""
        return session.query(AchatCommande).get(commande_id)
    
    # ================== GESTION DES PAIEMENTS ==================
    
    def verify_solde_compte(self, session: Session, compte_id: int, montant: Decimal) -> bool:
        """Vérifie si le solde d'un compte est suffisant pour un paiement"""
        try:
            compte = session.query(ComptaComptes).get(compte_id)
            if not compte:
                raise ValueError("Compte introuvable")
            
            # Si c'est un compte fournisseur (classe 4), pas besoin de vérifier le solde
            if compte.numero.startswith('4'):  # Comptes de tiers
                return True
            
            # Pour les autres comptes, calculer le solde actuel
            # Récupérer toutes les écritures pour ce compte
            ecritures = session.query(ComptaEcritures).filter_by(compte_comptable_id=compte_id).all()
            
            # Calculer le solde : Débit - Crédit pour les comptes d'actif
            # Crédit - Débit pour les comptes de passif
            solde = Decimal('0')
            for ecriture in ecritures:
                if compte.numero.startswith(('1', '2', '3', '6')):  # Comptes d'actif et charges
                    solde += (ecriture.debit or Decimal('0')) - (ecriture.credit or Decimal('0'))
                else:  # Comptes de passif et produits
                    solde += (ecriture.credit or Decimal('0')) - (ecriture.debit or Decimal('0'))
            
            return solde >= montant
            
        except Exception as e:
            print(f"Erreur lors de la vérification du solde: {e}")
            return False
    
    def process_paiement_commande(self, session: Session, commande_id: int,
                                 montant: Decimal, mode_paiement: str, reference: str = None) -> bool:
        """
        Traite le paiement d'une commande
        
        Args:
            session: Session SQLAlchemy
            commande_id: ID de la commande à payer
            montant: Montant du paiement
            mode_paiement: Mode de paiement (Espèces, Chèque, etc.)
            reference: Référence du paiement
        
        Returns:
            bool: True si le paiement a réussi
        """
        try:
            commande = session.query(AchatCommande).get(commande_id)
            if not commande:
                raise ValueError("Commande introuvable")
            
            if commande.etat == EtatCommande.VALIDE:
                raise ValueError("Cette commande est déjà payée et validée")
            
            if commande.etat == EtatCommande.ANNULE:
                raise ValueError("Impossible de payer une commande annulée")
            
            # Vérifier que le montant ne dépasse pas le montant total de la commande
            try:
                montant_deja_paye = sum(d.montant for d in commande.depenses)
            except Exception as e:
                print(f"Erreur lors du calcul des paiements existants: {e}")
                # Si erreur de colonne, considérer qu'aucun paiement n'a été fait
                montant_deja_paye = Decimal('0')
                
            montant_restant = commande.montant_total - montant_deja_paye
            
            if montant > montant_restant:
                raise ValueError(f"Le montant du paiement ({montant}) dépasse le montant restant ({montant_restant})")
            
            # Créer l'enregistrement de dépense
            depense = AchatDepense(
                bon_commande_id=commande_id,
                montant=montant,
                mode_paiement=mode_paiement,
                reference=reference,
                date_paiement=datetime.now()
            )
            session.add(depense)
            session.flush()  # Pour obtenir l'ID
            
            # Si le paiement couvre le montant total, valider la commande
            nouveau_montant_paye = montant_deja_paye + montant
            if nouveau_montant_paye >= commande.montant_total:
                # Marquer la commande comme validée
                commande.etat = EtatCommande.VALIDE
                
                # Créer les mouvements de stock
                self.create_mouvements_stock(session, commande)
                
                # Créer l'écriture comptable
                self.create_ecriture_comptable_achat(session, commande, depense)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Erreur lors du paiement: {e}")
            raise e
    
    def create_ecriture_comptable_achat(self, session: Session, 
                                       commande: AchatCommande, depense: AchatDepense):
        """Crée l'écriture comptable pour un achat"""
        try:
            # Récupérer la configuration comptable
            config = session.query(ComptaConfig).filter_by(
                enterprise_id=self.entreprise_id
            ).first()
            
            if not config:
                print("Aucune configuration comptable trouvée")
                return
            
            # Créer le journal principal
            journal = ComptaJournaux(
                date_operation=datetime.now(),
                libelle=f"Achat - Commande {commande.numero}",
                montant=commande.montant_total,
                type_operation="sortie",
                reference=commande.numero,
                description=f"Achat auprès de {commande.fournisseur.nom if commande.fournisseur else 'Fournisseur divers'}",
                enterprise_id=self.entreprise_id,
                user_id=commande.utilisateur_id
            )
            session.add(journal)
            session.flush()  # Pour obtenir l'ID
            
            # Écriture de débit : Compte d'achat (classe 6)
            if config.compte_achat_id:
                ecriture_debit = ComptaEcritures(
                    journal_id=journal.id,
                    compte_comptable_id=config.compte_achat_id,
                    debit=commande.montant_total,
                    credit=Decimal('0'),
                    ordre=1,
                    libelle=f"Achat - {commande.fournisseur.nom if commande.fournisseur else 'Divers'}"
                )
                session.add(ecriture_debit)
            
            # Écriture de crédit : Compte de paiement
            compte = session.query(ComptaComptes).get(depense.compte_id)
            
            if compte.numero.startswith('4'):  # Compte fournisseur - créance
                # Crédit au compte fournisseur (augmentation de la dette)
                ecriture_credit = ComptaEcritures(
                    journal_id=journal.id,
                    compte_comptable_id=depense.compte_id,
                    debit=Decimal('0'),
                    credit=commande.montant_total,
                    ordre=2,
                    libelle=f"Dette fournisseur - {commande.fournisseur.nom if commande.fournisseur else 'Divers'}"
                )
            else:  # Compte de caisse - paiement immédiat
                # Crédit au compte de caisse (sortie d'argent)
                ecriture_credit = ComptaEcritures(
                    journal_id=journal.id,
                    compte_comptable_id=depense.compte_id,
                    debit=Decimal('0'),
                    credit=commande.montant_total,
                    ordre=2,
                    libelle=f"Paiement achat - {commande.fournisseur.nom if commande.fournisseur else 'Divers'}"
                )
            
            session.add(ecriture_credit)
            
            print(f"Écriture comptable créée dans le journal ID: {journal.id}")
            
        except Exception as e:
            print(f"Erreur lors de la création de l'écriture comptable: {e}")
            # Ne pas faire échouer tout le processus si la comptabilité échoue
            pass
    
    # ================== INTÉGRATION STOCK ==================
    
    def create_mouvements_stock(self, session: Session, commande: AchatCommande):
        """Crée les mouvements de stock pour une commande validée"""
        for ligne in commande.lignes:
            # Créer le mouvement d'entrée
            movement = StockMovement(
                product_id=ligne.produit_id,
                warehouse_id=commande.entrepot_id,
                movement_type='ENTREE',
                quantity=ligne.quantite,
                unit_cost=ligne.prix_unitaire,
                total_cost=ligne.quantite * ligne.prix_unitaire,
                reference=commande.numero,
                description=f'Achat - Commande {commande.numero}',
                movement_date=datetime.now(),
                user_id=commande.utilisateur_id
            )
            session.add(movement)
            
            # Mettre à jour ou créer l'entrée stock produit-entrepôt
            stock_entry = session.query(StockProduitEntrepot).filter_by(
                product_id=ligne.produit_id,
                warehouse_id=commande.entrepot_id
            ).first()
            
            if stock_entry:
                # Mettre à jour la quantité existante
                old_quantity = stock_entry.quantity
                new_quantity = old_quantity + ligne.quantite
                
                # Mettre à jour le prix moyen pondéré
                if new_quantity > 0:
                    total_value = (old_quantity * stock_entry.unit_cost) + (ligne.quantite * ligne.prix_unitaire)
                    stock_entry.unit_cost = total_value / new_quantity
                
                stock_entry.quantity = new_quantity
                stock_entry.total_cost = new_quantity * stock_entry.unit_cost
                stock_entry.last_movement_date = datetime.now()
            else:
                # Créer une nouvelle entrée stock
                stock_entry = StockProduitEntrepot(
                    product_id=ligne.produit_id,
                    warehouse_id=commande.entrepot_id,
                    quantity=ligne.quantite,
                    reserved_quantity=Decimal('0'),
                    unit_cost=ligne.prix_unitaire,
                    total_cost=ligne.quantite * ligne.prix_unitaire,
                    min_stock_level=Decimal('10'),  # Valeur par défaut
                    last_movement_date=datetime.now()
                )
                session.add(stock_entry)
    
    def annuler_commande(self, session: Session, commande_id: int, motif: str = None):
        """Annule une commande"""
        commande = session.query(AchatCommande).get(commande_id)
        if not commande:
            raise ValueError("Commande introuvable")
        
        if commande.etat == EtatCommande.VALIDE:
            raise ValueError("Impossible d'annuler une commande déjà validée")
        
        commande.etat = EtatCommande.ANNULE
        session.commit()
    
    # ================== UTILITAIRES ==================
    
    def get_entrepots_disponibles(self, session: Session) -> List[StockWarehouse]:
        """Récupère la liste des entrepôts disponibles pour les achats"""
        return session.query(StockWarehouse).filter(
            StockWarehouse.is_active == True
        ).order_by(StockWarehouse.name).all()
    
    def get_produits_disponibles(self, session: Session, search: str = None) -> List[CoreProduct]:
        """Récupère la liste des produits disponibles pour les achats"""
        query = session.query(CoreProduct).filter(CoreProduct.is_active == True)
        
        if search:
            query = query.filter(
                or_(
                    CoreProduct.name.ilike(f"%{search}%"),
                    CoreProduct.code.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(CoreProduct.name).all()