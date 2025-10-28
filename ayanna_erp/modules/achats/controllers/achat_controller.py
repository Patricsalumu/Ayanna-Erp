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
from ayanna_erp.modules.salle_fete.model import EventExpense
from ayanna_erp.modules.core.models import CoreProduct
from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot, StockMovement
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes, ComptaEcritures, ComptaJournaux, ComptaConfig
from ayanna_erp.core.entreprise_controller import EntrepriseController


class AchatController:
    """Contrôleur principal pour la gestion des achats"""
    
    def __init__(self, pos_id: int = None, entreprise_id: int = None):
        self.db_manager = DatabaseManager()
        self.pos_id = pos_id
        
        # Récupérer l'ID de l'entreprise de l'utilisateur connecté
        from ayanna_erp.core.session_manager import SessionManager
        if entreprise_id:
            self.entreprise_id = entreprise_id
        else:
            # Récupérer l'entreprise de l'utilisateur connecté
            connected_enterprise_id = SessionManager.get_current_enterprise_id()
            self.entreprise_id = connected_enterprise_id
    
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
        
        #Creation d'ecriture comptable de commande
        self.create_ecriture_comptable_commande(session, commande)
        
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
                description=f"Achat Marchandise - commande {commande.numero}",
                reference=reference,
                date_paiement=datetime.now()
            )
            session.add(depense)
            session.flush()  # Pour obtenir l'ID
            
            # # Créer l'enregistrement de dépense dans event_expense
            # event_expense = EventExpense(
            #     amount=montant,
            #     pos_id = 1, #TODO a implementer
            #     expense_type = 'Achat',
            #     payment_method=mode_paiement,
            #     description =f"Achat Marchandise - commande {commande.numero}",
            #     account_id = 1,
            #     expense_date=datetime.now()
            # )
            # session.add(event_expense)
            
            # Créer l'écriture comptable
            self.create_ecriture_comptable_achat(session, commande, depense)
            
            # Si le paiement couvre le montant total, valider la commande
            # Calculer le nouveau total payé et mettre à jour le statut de paiement
            nouveau_montant_paye = montant_deja_paye + montant
            try:
                # Mettre à jour le champ statut_paiement (s'il existe dans le modèle)
                if nouveau_montant_paye <= 0:
                    commande.statut_paiement = 'non_paye'
                elif nouveau_montant_paye >= commande.montant_total:
                    commande.statut_paiement = 'paye'
                    # Si les produits ont déjà été réceptionnés, on peut valider la commande
                    try:
                        if commande.etat == EtatCommande.RECEPTIONNE:
                            commande.etat = EtatCommande.VALIDE
                    except Exception:
                        # ignore if enum/field missing
                        pass
                else:
                    commande.statut_paiement = 'partiel'

            except Exception:
                # Si la colonne/statut n'existe pas, ignorer silencieusement
                pass
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Erreur lors du paiement: {e}")
            raise e
    
    
    ##Ecriture comptable creation commande
    def create_ecriture_comptable_commande(self, session: Session, 
                                        commande: AchatCommande):
        """Crée les écritures comptables pour une commande d'achat"""
        try:
            # Récupération de la configuration comptable
            config = session.query(ComptaConfig).filter_by(
                enterprise_id=self.entreprise_id
            ).first()

            if not config:
                print("⚠️ Configuration comptable manquante pour cette entreprise.")
                return

            # === JOURNAL 1 : Achat (stock / charge vs fournisseur) ===
            journal_commande = ComptaJournaux(
                date_operation=datetime.now(),
                libelle=f"Achat marchandises - Commande {commande.numero}",
                montant=commande.montant_total,
                type_operation="Commande",
                reference=commande.numero,
                description=f"Achat auprès de {commande.fournisseur.nom if commande.fournisseur else 'Fournisseur divers'}",
                enterprise_id=self.entreprise_id,
                user_id=commande.utilisateur_id
            )
            session.add(journal_commande)
            session.flush()

            # Débit : Stock (ou compte achat)
            ecriture_debit_achat = ComptaEcritures(
                journal_id=journal_commande.id,
                compte_comptable_id=config.compte_stock_id or config.compte_achat_id,
                debit=commande.montant_total,
                credit=Decimal('0'),
                ordre=1,
                libelle=f"Achat marchandises - {commande.fournisseur.nom if commande.fournisseur else 'Divers'}"
            )
            session.add(ecriture_debit_achat)

            # Crédit : Fournisseur
            ecriture_credit_achat = ComptaEcritures(
                journal_id=journal_commande.id,
                compte_comptable_id=config.compte_fournisseur_id,
                debit=Decimal('0'),
                credit=commande.montant_total,
                ordre=2,
                libelle=f"Dette fournisseur - {commande.fournisseur.nom if commande.fournisseur else 'Divers'}"
            )
            session.add(ecriture_credit_achat)
            try:
                ent_ctrl = EntrepriseController(entreprise_id=self.entreprise_id)
                montant_fmt = ent_ctrl.format_amount(commande.montant_total)
            except Exception:
                montant_fmt = str(commande.montant_total)
            print(f"✅ Journal d'achat créé (ID {journal_commande.id}) - {montant_fmt}")
            session.flush()
            print("✅ Toutes les écritures ont été enregistrées avec succès.")

        except Exception as e:
            print(f"❌ Erreur lors de la création des écritures comptables: {e}")
            import traceback
            traceback.print_exc()
            
            
    def create_ecriture_comptable_achat(self, session: Session, 
                                        commande: AchatCommande, depense: AchatDepense):
        """Crée les écritures comptables pour un achat et son paiement éventuel"""
        try:
            # Récupération de la configuration comptable
            config = session.query(ComptaConfig).filter_by(
                enterprise_id=self.entreprise_id
            ).first()

            if not config:
                print("⚠️ Configuration comptable manquante pour cette entreprise.")
                return

            # === JOURNAL 2 : Paiement (fournisseur vs caisse) ===
            if depense and depense.montant and depense.montant > 0:
                journal_paiement = ComptaJournaux(
                    date_operation=datetime.now(),
                    libelle=f"Règlement fournisseur - {commande.fournisseur.nom if commande.fournisseur else 'Divers'} - {commande.numero}",
                    montant=depense.montant,
                    type_operation="Sortie",
                    reference=f"PAY-{commande.numero}",
                    description=f"Paiement fournisseur pour commande {commande.numero}",
                    enterprise_id=self.entreprise_id,
                    user_id=commande.utilisateur_id
                )
                session.add(journal_paiement)
                session.flush()

                # Débit : Fournisseur (on diminue la dette)
                ecriture_debit_paiement = ComptaEcritures(
                    journal_id=journal_paiement.id,
                    compte_comptable_id=config.compte_fournisseur_id,
                    debit=depense.montant,
                    credit=Decimal('0'),
                    ordre=1,
                    libelle=f"Paiement fournisseur - {commande.fournisseur.nom if commande.fournisseur else 'Divers'}"
                )
                session.add(ecriture_debit_paiement)

                # Crédit : Caisse ou banque (sortie d’argent)
                compte_paiement_id = config.compte_caisse_id
                ecriture_credit_paiement = ComptaEcritures(
                    journal_id=journal_paiement.id,
                    compte_comptable_id=compte_paiement_id,
                    debit=Decimal('0'),
                    credit=depense.montant,
                    ordre=2,
                    libelle=f"Règlement fournisseur - {commande.fournisseur.nom if commande.fournisseur else 'Divers'} - Commande {commande.numero}"
                )
                session.add(ecriture_credit_paiement)

                try:
                    ent_ctrl = EntrepriseController(entreprise_id=self.entreprise_id)
                    montant_fmt = ent_ctrl.format_amount(depense.montant)
                except Exception:
                    montant_fmt = str(depense.montant)
                print(f"✅ Journal de paiement créé (ID {journal_paiement.id}) - {montant_fmt}")

            session.flush()
            print("✅ Toutes les écritures ont été enregistrées avec succès.")

        except Exception as e:
            print(f"❌ Erreur lors de la création des écritures comptables: {e}")
            import traceback
            traceback.print_exc()

        
    # ================== INTÉGRATION STOCK ==================
    
    def create_mouvements_stock(self, session: Session, commande: AchatCommande):
        """Crée les mouvements de stock pour une commande validée"""
        for ligne in commande.lignes:
            # Créer le mouvement d'entrée (achat)
            # Pour les achats (ENTREE) : warehouse_id = entrepôt de destination, destination_warehouse_id = NULL
            # Cela permet de distinguer achats (destination_warehouse_id=NULL) des transferts (destination_warehouse_id!=NULL)
            movement = StockMovement(
                product_id=ligne.produit_id,
                warehouse_id=commande.entrepot_id,   # Entrepôt de destination (obligatoire)
                destination_warehouse_id=None,      # NULL pour les achats (pas un transfert)
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
        """Annule une commande d'achat avec gestion complète des conséquences

        Actions effectuées :
        1. Si commande réceptionnée : crée mouvements de sortie pour réduire le stock
        2. Met à zéro toutes les dépenses (AchatDepense) liées à cette commande
        3. Crée écritures comptables d'annulation
        """
        from ayanna_erp.modules.stock.models import StockMovement
        from ayanna_erp.modules.achats.models.achats_models import AchatDepense

        commande = session.query(AchatCommande).get(commande_id)
        if not commande:
            raise ValueError("Commande introuvable")

        if commande.etat == EtatCommande.VALIDE:
            raise ValueError("Impossible d'annuler une commande déjà validée")

        # === 1. SI COMMANDE RÉCEPTIONNÉE : CRÉER MOUVEMENTS DE SORTIE ===
        if commande.etat == EtatCommande.RECEPTIONNE:
            # Créer mouvements de sortie pour annuler l'entrée en stock
            for ligne in commande.lignes:
                if ligne.quantite > 0:
                    # Trouver l'entrepôt de destination (entrepôt de la commande)
                    entrepot_id = commande.entrepot_id

                    mouvement_sortie = StockMovement(
                        product_id=ligne.produit_id,
                        warehouse_id=entrepot_id,
                        movement_type="SORTIE",
                        quantity=-ligne.quantite,  # Quantité négative pour sortie
                        unit_cost=ligne.prix_unitaire,
                        total_cost=-(ligne.prix_unitaire * ligne.quantite),
                        reference=f"ANN-{commande.numero}",
                        description=f"Annulation commande d'achat - {commande.numero}",
                        user_id=getattr(commande, 'utilisateur_id', None),
                        user_name=getattr(commande, 'utilisateur_nom', 'Système')
                    )
                    session.add(mouvement_sortie)
                    session.flush()  # Pour obtenir l'ID du mouvement

                    # METTRE À JOUR LA QUANTITÉ EN STOCK
                    produit_entrepot = session.query(StockProduitEntrepot).filter_by(
                        product_id=ligne.produit_id,
                        warehouse_id=entrepot_id
                    ).first()

                    if produit_entrepot:
                        # Réduire la quantité en stock
                        produit_entrepot.quantity = (produit_entrepot.quantity or Decimal('0')) - ligne.quantite
                        # Recalculer le coût total
                        produit_entrepot.total_cost = produit_entrepot.quantity * (produit_entrepot.unit_cost or Decimal('0'))
                        produit_entrepot.last_movement_date = datetime.now()
                        session.add(produit_entrepot)
                    else:
                        # Si l'entrée n'existe pas, la créer avec quantité négative (cas exceptionnel)
                        nouveau_produit_entrepot = StockProduitEntrepot(
                            product_id=ligne.produit_id,
                            warehouse_id=entrepot_id,
                            quantity=-ligne.quantite,
                            unit_cost=ligne.prix_unitaire,
                            total_cost=-(ligne.prix_unitaire * ligne.quantite),
                            last_movement_date=datetime.now()
                        )
                        session.add(nouveau_produit_entrepot)

        # === 2. METTRE À ZÉRO TOUTES LES DÉPENSES LIÉES ===
        depenses = session.query(AchatDepense).filter_by(bon_commande_id=commande_id).all()
        for depense in depenses:
            # Sauvegarder l'ancien montant pour les écritures comptables
            ancien_montant = depense.montant
            depense.montant = Decimal('0')  # Mettre à zéro
            depense.description = f"{depense.description or ''} [ANNULÉ - Ancien montant: {ancien_montant}]".strip()

            # Stocker l'ancien montant pour les écritures comptables
            depense._ancien_montant = ancien_montant

        # === 3. PASSER L'ÉTAT À ANNULÉ ===
        commande.etat = EtatCommande.ANNULE
        # Note: Le motif d'annulation pourrait être stocké dans un champ commentaires
        # si ajouté au modèle AchatCommande à l'avenir

        # === 4. CRÉER ÉCRITURES COMPTABLES D'ANNULATION ===
        try:
            config = session.query(ComptaConfig).filter_by(
                enterprise_id=self.entreprise_id
            ).first()

            if config:
                # === ANNULATION DES PAIEMENTS INDIVIDUELS ===
                for depense in depenses:
                    ancien_montant = getattr(depense, '_ancien_montant', depense.montant)
                    if ancien_montant > 0:  # Utiliser l'ancien montant avant mise à zéro
                        # Créer une écriture d'annulation pour chaque paiement
                        journal_annulation_paiement = ComptaJournaux(
                            date_operation=datetime.now(),
                            libelle=f"Annulation paiement - {depense.description or 'Paiement'} - Cmd {commande.numero}",
                            montant=ancien_montant,
                            type_operation="Annulation",
                            reference=f"ANN-PAY-{commande.numero}-{depense.id}",
                            description=f"Annulation du paiement de {ancien_montant} pour la commande {commande.numero}",
                            enterprise_id=self.entreprise_id,
                            user_id=commande.utilisateur_id
                        )
                        session.add(journal_annulation_paiement)
                        session.flush()

                        # Déterminer le compte de règlement selon le mode de paiement
                        compte_reglement_id = config.compte_caisse_id  # Par défaut caisse
                        if depense.mode_paiement and 'banque' in depense.mode_paiement.lower():
                            compte_reglement_id = config.compte_banque_id or config.compte_caisse_id

                        # Écriture d'annulation du paiement :
                        # Lors du paiement original : Débit Fournisseur, Crédit Caisse/Banque
                        # Lors de l'annulation : Débit Caisse/Banque, Crédit Fournisseur

                        # Débit : Caisse/Banque (on annule le crédit précédent)
                        ecriture_debit = ComptaEcritures(
                            journal_id=journal_annulation_paiement.id,
                            compte_comptable_id=compte_reglement_id,
                            debit=ancien_montant,
                            credit=Decimal('0'),
                            ordre=1,
                            libelle=f"Annulation règlement - {depense.description or 'Paiement'} - Cmd {commande.numero}"
                        )
                        session.add(ecriture_debit)

                        # Crédit : Fournisseur (on annule le débit précédent)
                        ecriture_credit = ComptaEcritures(
                            journal_id=journal_annulation_paiement.id,
                            compte_comptable_id=config.compte_fournisseur_id,
                            debit=Decimal('0'),
                            credit=ancien_montant,
                            ordre=2,
                            libelle=f"Annulation dette fournisseur - Cmd {commande.numero}"
                        )
                        session.add(ecriture_credit)
                        session.flush()

                # === ANNULATION DE LA COMMANDE ELLE-MÊME ===
                if commande.montant_total > 0:
                    journal_commande_annulation = ComptaJournaux(
                        date_operation=datetime.now(),
                        libelle=f"Annulation commande - {commande.numero}",
                        montant=commande.montant_total,
                        type_operation="Annulation",
                        reference=f"ANN-CMD-{commande.numero}",
                        description=f"Annulation commande d'achat {commande.numero}",
                        enterprise_id=self.entreprise_id,
                        user_id=commande.utilisateur_id
                    )
                    session.add(journal_commande_annulation)
                    session.flush()

                    # Débit : Fournisseur (on recrée la dette inverse)
                    ecriture_debit = ComptaEcritures(
                        journal_id=journal_commande_annulation.id,
                        compte_comptable_id=config.compte_fournisseur_id,
                        debit=commande.montant_total,
                        credit=Decimal('0'),
                        ordre=1,
                        libelle=f"Annulation dette fournisseur - Commande {commande.numero}"
                    )
                    session.add(ecriture_debit)

                    # Crédit : Stock/Achat (on annule l'actif créé précédemment)
                    ecriture_credit = ComptaEcritures(
                        journal_id=journal_commande_annulation.id,
                        compte_comptable_id=config.compte_stock_id or config.compte_achat_id,
                        debit=Decimal('0'),
                        credit=commande.montant_total,
                        ordre=2,
                        libelle=f"Annulation achat - Commande {commande.numero}"
                    )
                    session.add(ecriture_credit)
                    session.flush()

        except Exception as e:
            print(f"Erreur lors de la création des écritures d'annulation: {e}")
            # Ne pas échouer pour autant, continuer avec l'annulation

        session.commit()

    def reception_commande(self, session: Session, commande_id: int) -> bool:
        """Réceptionne une commande : crée les mouvements de stock si nécessaire et marque la commande comme validée.

        Comportement:
        - Si la commande n'existe pas -> ValueError
        - Si la commande est annulée -> ValueError
        - Si des mouvements d'entrée pour cette commande existent déjà (même référence) -> ne rien faire et retourner False
        - Sinon : crée les mouvements via create_mouvements_stock(), marque la commande comme VALIDE et commit
        """
        from ayanna_erp.modules.stock.models import StockMovement

        commande = session.query(AchatCommande).get(commande_id)
        if not commande:
            raise ValueError("Commande introuvable")

        if commande.etat == EtatCommande.ANNULE:
            raise ValueError("Impossible de réceptionner une commande annulée")

        # Vérifier si des mouvements d'entrée existent déjà pour cette référence
        existing = session.query(StockMovement).filter(
            StockMovement.reference == commande.numero,
            StockMovement.movement_type == 'ENTREE'
        ).first()

        if existing:
            # Déjà réceptionnée (mouvements déjà créés)
            return False

        # Créer mouvements de stock (ajoute les StockMovement et met à jour StockProduitEntrepot)
        self.create_mouvements_stock(session, commande)

        # Mettre à jour les coûts des produits dans CoreProduct
        for ligne in commande.lignes:
            self.update_product_cost(session, ligne.produit_id)

        # Après création des mouvements, déterminer le statut final :
        # - si la commande est déjà payée à 100% -> VALIDE
        # - sinon -> RECEPTIONNE
        try:
            try:
                total_paye = sum(d.montant for d in commande.depenses) if commande.depenses else Decimal('0')
            except Exception:
                total_paye = Decimal('0')

            if total_paye >= commande.montant_total:
                commande.etat = EtatCommande.VALIDE
            else:
                commande.etat = EtatCommande.RECEPTIONNE
        except Exception:
            # Fallback: set to RECEPTIONNE if something goes wrong
            try:
                commande.etat = EtatCommande.RECEPTIONNE
            except Exception:
                commande.etat = EtatCommande.VALIDE

        session.commit()
        return True
    
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
    
    def update_commande(self, session: Session, commande_id: int, lignes: List[Dict]) -> AchatCommande:
        """Met à jour une commande d'achat (lignes seulement, si en cours)"""
        commande = session.query(AchatCommande).get(commande_id)
        if not commande:
            raise ValueError("Commande introuvable")
        
        if commande.etat != EtatCommande.ENCOURS:
            raise ValueError("Cette commande ne peut plus être modifiée")
        
        # Note: On permet la modification même si la commande est payée partiellement ou totalement
        
        # Supprimer toutes les lignes existantes
        session.query(AchatCommandeLigne).filter_by(bon_commande_id=commande_id).delete()
        
        # Ajouter les nouvelles lignes
        for ligne_data in lignes:
            self.add_ligne_commande(session, commande_id, **ligne_data)
        
        # Recalculer le total
        self.recalculer_total_commande(session, commande_id)
        
        # Mettre à jour les écritures comptables : supprimer anciennes et recréer
        self.update_ecriture_comptable_commande(session, commande)
        
        # Mettre à jour les coûts des produits modifiés
        for ligne_data in lignes:
            self.update_product_cost(session, ligne_data['produit_id'])
        
        session.commit()
        session.refresh(commande)
        return commande
    
    def update_ecriture_comptable_commande(self, session: Session, commande: AchatCommande):
        """Met à jour les écritures comptables pour une commande modifiée"""
        # Supprimer les anciennes écritures
        journaux = session.query(ComptaJournaux).filter_by(
            reference=commande.numero,
            type_operation="Commande",
            enterprise_id=self.entreprise_id
        ).all()
        
        for journal in journaux:
            # Supprimer les écritures associées
            session.query(ComptaEcritures).filter_by(journal_id=journal.id).delete()
            # Supprimer le journal
            session.delete(journal)
        
        # Recréer les écritures avec les nouveaux montants
        self.create_ecriture_comptable_commande(session, commande)
    
    def update_product_cost(self, session: Session, product_id: int):
        """Met à jour le coût d'un produit dans CoreProduct basé sur le coût moyen pondéré des achats validés"""
        try:
            # Récupérer toutes les lignes de commandes validées pour ce produit
            lignes_validees = session.query(AchatCommandeLigne).join(AchatCommande).filter(
                AchatCommandeLigne.produit_id == product_id,
                AchatCommande.etat.in_([EtatCommande.VALIDE, EtatCommande.RECEPTIONNE])
            ).all()

            if lignes_validees:
                # Calculer le coût moyen pondéré
                total_quantity = sum(ligne.quantite for ligne in lignes_validees)
                total_cost = sum(ligne.quantite * ligne.prix_unitaire for ligne in lignes_validees)

                if total_quantity > 0:
                    average_cost = total_cost / total_quantity

                    # Mettre à jour le coût dans CoreProduct
                    product = session.query(CoreProduct).get(product_id)
                    if product:
                        product.cost = average_cost
                        session.commit()
                        print(f"✅ Coût du produit {product.name} mis à jour (moyenne pondérée): {average_cost}")
                else:
                    print(f"⚠️ Quantité totale nulle pour le produit {product_id}")
            else:
                print(f"ℹ️ Aucun achat validé trouvé pour le produit {product_id}")

        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du coût du produit {product_id}: {e}")
            session.rollback()