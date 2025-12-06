"""
Contrôleur pour la gestion des entrées et sorties de caisse du module Salle de Fête
Gère les dépenses avec integration comptable automatique
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ayanna_erp.modules.salle_fete.model.salle_fete import EventExpense, get_database_manager


class EntreSortieController(QObject):
    """Contrôleur pour la gestion des entrées et sorties de caisse"""
    
    # Signaux pour la communication avec la vue
    expense_added = pyqtSignal(object)
    expense_updated = pyqtSignal(object)
    expense_deleted = pyqtSignal(int)
    expense_cancelled = pyqtSignal(object)
    expenses_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id

    def _local_now(self):
        """Retourne la date/heure locale (naïve) de la machine."""
        from datetime import datetime
        return datetime.now()
        
    def set_pos_id(self, pos_id):
        """Définir l'ID du point de vente"""
        self.pos_id = pos_id
        
    def create_expense(self, expense_data):
        """
        Créer une nouvelle dépense avec intégration comptable
        
        Args:
            expense_data (dict): Données de la dépense
                - libelle: Libellé de la dépense
                - montant: Montant de la dépense
                - compte_id: ID du compte de charges (débit)
                - categorie: Catégorie de la dépense
                - fournisseur: Nom du fournisseur (optionnel)
                - facture: Numéro de facture (optionnel)
                - description: Description détaillée
                - reservation_id: ID de la réservation (optionnel)
                
        Returns:
            EventExpense: La dépense créée ou None
        """
        try:
            from ayanna_erp.modules.comptabilite.model.comptabilite import (
                ComptaConfig,
                ComptaEcritures as EcritureComptable, 
                ComptaJournaux as JournalComptable, 
                ComptaComptes as CompteComptable
            )
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
                
            # Créer la dépense
            expense = EventExpense(
                pos_id=self.pos_id,
                reservation_id=expense_data.get('reservation_id'),  # Optionnel
                expense_type=expense_data.get('categorie', 'Dépense générale'),
                description=expense_data.get('libelle'),
                amount=expense_data.get('montant'),
                expense_date=self._local_now(),
                supplier=expense_data.get('fournisseur'),
                invoice_number=expense_data.get('facture'),
                payment_method='Espèces',  # Toujours espèces pour commencer
                account_id=expense_data.get('compte_id'),
                created_by=1,  # TODO: Récupérer l'ID de l'utilisateur connecté
                created_at=self._local_now()
            )
            
            session.add(expense)
            session.flush()  # Pour obtenir l'ID
            
            print(f"Dépense créée: {expense.description} - {expense.amount}€")
            
            # === INTEGRATION COMPTABLE ===
            # Récupérer la configuration comptable pour ce POS
            config = session.query(ComptaConfig).filter_by(pos_id=self.pos_id).first()
            if not config:
                print("Configuration comptable manquante pour ce point de vente")
            else:
                # Créer la ligne de journal comptable
                libelle = f"Dépense: {expense.description}"
                journal = JournalComptable(
                    enterprise_id=1,  # TODO: Récupérer l'ID de l'entreprise du POS
                    libelle=libelle,
                    montant=expense.amount,
                    type_operation="sortie",  # 'sortie' pour une dépense
                    reference=f"EXP-{expense.id}",
                    description=f"Dépense ID: {expense.id} - {expense.expense_type}",
                    user_id=1,  # TODO: Récupérer l'ID de l'utilisateur connecté
                    date_operation=self._local_now()
                )
                session.add(journal)
                session.flush()  # Pour avoir l'id du journal

                # Nouveau comportement déterministe :
                # - Le compte sélectionné dans le combo 'compte_id' est toujours considéré comme le compte
                #   de charge (débit).
                # - Le compte financier sélectionné dans 'compte_financier_id' est utilisé comme contrepartie (crédit).
                #   Si absent, on utilise le compte caisse configuré dans ComptaConfig en fallback.
                compte_selected = session.query(CompteComptable).filter(CompteComptable.id == expense_data.get('compte_id')).first()
                if not compte_selected:
                    raise Exception("Le compte sélectionné n'existe pas ou n'est pas actif.")

                compte_financier_id = expense_data.get('compte_financier_id')
                compte_financier = None
                if compte_financier_id:
                    compte_financier = session.query(CompteComptable).filter(CompteComptable.id == compte_financier_id).first()

                # Débit : compte_selected
                ecriture_debit = EcritureComptable(
                    journal_id=journal.id,
                    compte_comptable_id=compte_selected.id,
                    debit=expense.amount,
                    credit=0,
                    ordre=1,
                    libelle=f"Dépense - {expense.description}"
                )
                session.add(ecriture_debit)

                # Crédit : compte_financier if provided else config.compte_caisse_id else fallback to compte_selected
                credit_account = None
                if compte_financier:
                    credit_account = compte_financier
                elif config and getattr(config, 'compte_caisse_id', None):
                    credit_account = session.query(CompteComptable).filter(CompteComptable.id == config.compte_caisse_id).first()
                else:
                    credit_account = compte_selected

                # Vérifier le solde du compte financier pour empêcher un solde négatif
                try:
                    from sqlalchemy import func

                    balance_expr = (func.coalesce(func.sum(EcritureComptable.debit), 0) - func.coalesce(func.sum(EcritureComptable.credit), 0))
                    current_balance = session.query(balance_expr).filter(EcritureComptable.compte_comptable_id == credit_account.id).scalar() or 0
                    current_balance = float(current_balance)
                    montant_a_payer = float(expense.amount or 0)
                except Exception:
                    # En cas d'erreur lors du calcul, on laisse passer (ne pas bloquer l'opération)
                    current_balance = None
                    montant_a_payer = float(expense.amount or 0)

                if current_balance is not None and current_balance < montant_a_payer:
                    # Solde insuffisant — annuler et informer la vue avec message explicite
                    session.rollback()
                    compte_num = getattr(credit_account, 'numero', None) or getattr(credit_account, 'id', 'N/A')
                    compte_name = getattr(credit_account, 'name', None) or getattr(credit_account, 'libelle', '')
                    err = (
                        f"Dépense refusée — fonds insuffisants sur le compte financier.\n"
                        f"Compte: {compte_num}{(' - ' + compte_name) if compte_name else ''}\n"
                        f"Solde actuel: {current_balance:.2f} € — Montant demandé: {montant_a_payer:.2f} €.\n"
                        f"Actions possibles: approvisionner le compte, sélectionner un autre compte financier, ou contacter l'administrateur.\n"
                        f"Référence dépense: EXP-{expense.id}"
                    )
                    print(err)
                    self.error_occurred.emit(err)
                    return None

                ecriture_credit = EcritureComptable(
                    journal_id=journal.id,
                    compte_comptable_id=credit_account.id,
                    debit=0,
                    credit=expense.amount,
                    ordre=2,
                    libelle=f"Sortie - {expense.description}"
                )
                session.add(ecriture_credit)
                print(f"Écritures comptables créées: Débit {compte_selected.numero} / Crédit {credit_account.numero}")
                
            session.commit()
            session.refresh(expense)
            
            print(f"Dépense enregistrée avec succès: {expense.description}")
            self.expense_added.emit(expense)
            return expense
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la création de la dépense: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_expenses_by_date(self, target_date):
        """Récupérer les dépenses pour une date donnée"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            if isinstance(target_date, datetime):
                target_date = target_date.date()
                
            # Définir les bornes de la journée
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            expenses = session.query(EventExpense).filter(
                EventExpense.pos_id == self.pos_id,
                EventExpense.expense_date.between(start_datetime, end_datetime)
            ).order_by(EventExpense.expense_date.desc()).all()
            
            return expenses
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des dépenses: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
    
    def get_all_expenses(self, date_from=None, date_to=None):
        """
        Récupérer toutes les dépenses avec filtres optionnels
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Filtrage principal par pos_id
            query = session.query(EventExpense).filter(
                EventExpense.pos_id == self.pos_id
            )
            
            # Filtres optionnels
            if date_from:
                query = query.filter(EventExpense.expense_date >= date_from)
            if date_to:
                query = query.filter(EventExpense.expense_date <= date_to)
                
            expenses = query.order_by(EventExpense.expense_date.desc()).all()
            
            self.expenses_loaded.emit(expenses)
            return expenses
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des dépenses: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()

    def load_account_journal(self, account_id, date_from=None, date_to=None):
        """
        Charger les écritures comptables liées à un compte (id) sur une plage de dates.
        Retourne une liste d'entrées mappées pour l'interface: debit -> Entrée, credit -> Sortie
        Chaque entrée est un dict contenant : id, datetime, type, libelle, categorie, montant_entree, montant_sortie, utilisateur, description
        """
        try:
            from ayanna_erp.modules.comptabilite.model.comptabilite import (
                ComptaEcritures as EcritureComptable,
                ComptaJournaux as JournalComptable,
                ComptaComptes as CompteComptable
            )

            db_manager = get_database_manager()
            session = db_manager.get_session()

            # Construire bornes temporelles si fournies
            start_dt = None
            end_dt = None
            if date_from:
                if isinstance(date_from, datetime):
                    start_dt = date_from
                else:
                    start_dt = datetime.combine(date_from, datetime.min.time())
            if date_to:
                if isinstance(date_to, datetime):
                    end_dt = date_to
                else:
                    end_dt = datetime.combine(date_to, datetime.max.time())

            # Requête des écritures pour ce compte
            query = session.query(EcritureComptable).filter(
                EcritureComptable.compte_comptable_id == account_id
            )

            # Joindre sur le journal si on veut filtrer par date_operation
            query = query.join(JournalComptable, EcritureComptable.journal_id == JournalComptable.id)

            if start_dt:
                query = query.filter(JournalComptable.date_operation >= start_dt)
            if end_dt:
                query = query.filter(JournalComptable.date_operation <= end_dt)

            query = query.order_by(JournalComptable.date_operation.desc(), EcritureComptable.ordre)

            lines = query.all()

            results = []
            for line in lines:
                # Charger le journal parent pour obtenir la date et la référence
                journal = session.query(JournalComptable).filter(JournalComptable.id == line.journal_id).first()
                dt = getattr(journal, 'date_operation', None) or getattr(line, 'created_at', None) or datetime.now()

                montant_entree = float(line.debit or 0)
                montant_sortie = float(line.credit or 0)

                entry = {
                    'id': f'EC_{line.id}',
                    'datetime': dt,
                    'type': 'Entrée' if montant_entree > 0 else ('Sortie' if montant_sortie > 0 else 'Neutre'),
                    'libelle': line.libelle or (journal.libelle if journal else ''),
                    'categorie': getattr(journal, 'type_operation', '') if journal else '',
                    'montant_entree': montant_entree,
                    'montant_sortie': montant_sortie,
                    'utilisateur': getattr(journal, 'user_id', None) if journal else None,
                    'description': getattr(journal, 'description', '') if journal else ''
                }
                results.append(entry)

            return results

        except Exception as e:
            print(f"Erreur lors du chargement des écritures comptables pour le compte {account_id}: {e}")
            return []

        finally:
            db_manager.close_session()
            
    def update_expense(self, expense_id, expense_data):
        """Mettre à jour une dépense existante"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            expense = session.query(EventExpense).filter(
                EventExpense.id == expense_id,
                EventExpense.pos_id == self.pos_id
            ).first()
            
            if not expense:
                error_msg = f"Dépense {expense_id} non trouvée"
                self.error_occurred.emit(error_msg)
                return False
                
            # Mettre à jour les champs
            expense.expense_type = expense_data.get('categorie', expense.expense_type)
            expense.description = expense_data.get('libelle', expense.description)
            expense.amount = expense_data.get('montant', expense.amount)
            expense.supplier = expense_data.get('fournisseur', expense.supplier)
            expense.invoice_number = expense_data.get('facture', expense.invoice_number)
            expense.account_id = expense_data.get('compte_id', expense.account_id)
            
            session.commit()
            session.refresh(expense)
            
            print(f"Dépense {expense_id} mise à jour avec succès")
            self.expense_updated.emit(expense)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la mise à jour de la dépense: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def delete_expense(self, expense_id):
        """Supprimer une dépense"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            expense = session.query(EventExpense).filter(
                EventExpense.id == expense_id,
                EventExpense.pos_id == self.pos_id
            ).first()
            
            if not expense:
                error_msg = f"Dépense {expense_id} non trouvée"
                self.error_occurred.emit(error_msg)
                return False
                
            # Refuser la suppression si le libellé commence par 'Règlement fournisseur'
            try:
                exp_lib = (expense.description or "").strip().lower()
                if exp_lib.startswith('règlement fournisseur') or exp_lib.startswith('reglement fournisseur'):
                    err = "Suppression refusée  : Un 'Règlement fournisseur' ne peut pas être supprimé."
                    self.error_occurred.emit(err)
                    return False
            except Exception:
                pass

            # TODO: Supprimer aussi les écritures comptables liées
            session.delete(expense)
            session.commit()
            
            print(f"Dépense supprimée: {expense.description}")
            self.expense_deleted.emit(expense_id)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la suppression: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()

    def cancel_expense(self, expense_id, user_id=1, reason=None):
        """Supprimer une dépense et le journal comptable associé (et ses écritures).

        Comportement :
        - Recherche la dépense `EventExpense` par `expense_id`.
        - Recherche le journal comptable ayant la référence `EXP-<expense_id>`.
        - Supprime les écritures (`compta_ecritures`) liées au journal puis supprime le journal.
        - Supprime la dépense métier (`event_expenses`).

        Retourne True si suppression réussie, False sinon.
        """

        try:
            # Vérifier que l'utilisateur est super admin
            db_manager = get_database_manager()
            session = db_manager.get_session()
            from ayanna_erp.database.database_manager import User
            try:
                user_obj = session.query(User).filter(User.id == int(user_id)).first()
            except Exception:
                user_obj = None
            if not user_obj or getattr(user_obj, 'role', '') != 'super_admin':
                err = "Suppression interdite : seul un utilisateur avec le rôle 'super_admin' peut supprimer définitivement des dépenses."
                self.error_occurred.emit(err)
                try:
                    session.close()
                except Exception:
                    pass
                return False

            from ayanna_erp.modules.comptabilite.model.comptabilite import (
                ComptaEcritures as EcritureComptable,
                ComptaJournaux as JournalComptable,
            )

            # Récupérer la dépense
            expense = session.query(EventExpense).filter(
                EventExpense.id == expense_id,
                EventExpense.pos_id == self.pos_id
            ).first()

            if not expense:
                msg = f"Dépense #{expense_id} introuvable pour le POS {self.pos_id}."
                self.error_occurred.emit(msg)
                return False

            # Rechercher le journal comptable lié (par convention de référence)
            ref = f"EXP-{expense.id}"
            orig_journal = session.query(JournalComptable).filter(JournalComptable.reference == ref).first()

            # Refuser la suppression si le libellé du journal ou de la dépense commence par 'Règlement fournisseur'
            try:
                if orig_journal:
                    jlib = (getattr(orig_journal, 'libelle', '') or '').strip().lower()
                    if jlib.startswith('règlement fournisseur') or jlib.startswith('reglement fournisseur'):
                        err = "Suppression refusée : les opérations comptables commençant par 'Règlement fournisseur' ne peuvent pas être supprimées."
                        self.error_occurred.emit(err)
                        return False
                delib = (expense.description or '').strip().lower()
                if delib.startswith('règlement fournisseur') or delib.startswith('reglement fournisseur'):
                    err = "Suppression refusée : les dépenses dont le libellé commence par 'Règlement fournisseur' ne peuvent pas être supprimées."
                    self.error_occurred.emit(err)
                    return False
            except Exception:
                pass

            # Supprimer les écritures liées puis le journal
            if orig_journal:
                # Ne pas supprimer les journaux de type 'Entrée'
                try:
                    jtype = (getattr(orig_journal, 'type_operation', '') or '').strip().lower()
                    if 'entree' in jtype or 'entrée' in jtype:
                        err = "Suppression refusée : les journaux de type 'Entrée' ne peuvent pas être supprimés via cette opération."
                        self.error_occurred.emit(err)
                        return False
                except Exception:
                    pass

                try:
                    # Supprimer les écritures comptables liées
                    session.query(EcritureComptable).filter(EcritureComptable.journal_id == orig_journal.id).delete(synchronize_session=False)
                    # Supprimer le journal
                    session.delete(orig_journal)
                except Exception as e:
                    session.rollback()
                    msg = f"Erreur lors de la suppression des écritures/journal liés à la dépense #{expense.id}: {e}"
                    print(msg)
                    self.error_occurred.emit(msg)
                    return False

            # Supprimer la dépense métier
            try:
                session.delete(expense)
            except Exception as e:
                session.rollback()
                msg = f"Erreur lors de la suppression de la dépense #{expense.id}: {e}"
                print(msg)
                self.error_occurred.emit(msg)
                return False

            session.commit()

            # Émettre signal et message utilisateur
            try:
                self.expense_deleted.emit(expense_id)
            except Exception:
                pass
            success_msg = f"Dépense #{expense_id} et écritures/journal associés supprimés avec succès."
            print(success_msg)
            self.error_occurred.emit(success_msg)
            return True

        except Exception as e:
            try:
                session.rollback()
            except Exception:
                pass
            msg = f"Erreur lors de la suppression de la dépense: {e}"
            print(msg)
            self.error_occurred.emit(msg)
            return False

        finally:
            try:
                db_manager.close_session()
            except Exception:
                pass

    def cancel_accounting_entry(self, ecriture_id, user_id=1, reason=None):
        """
        Annuler une écriture comptable en créant un journal d'annulation
        et en inversant toutes les écritures du journal original.
        """
        try:
            from ayanna_erp.modules.comptabilite.model.comptabilite import (
                ComptaEcritures as EcritureComptable,
                ComptaJournaux as JournalComptable,
            )

            db_manager = get_database_manager()
            session = db_manager.get_session()

            # Récupérer l'écriture et le journal original
            orig_line = session.query(EcritureComptable).filter(EcritureComptable.id == int(ecriture_id)).first()
            if not orig_line:
                self.error_occurred.emit(f"Écriture {ecriture_id} introuvable")
                return False

            orig_journal = session.query(JournalComptable).filter(JournalComptable.id == orig_line.journal_id).first()

            if not orig_journal:
                self.error_occurred.emit(f"Journal lié à l'écriture {ecriture_id} introuvable")
                return False

            # Créer un journal d'annulation
            libelle = f"Annulation - {orig_journal.libelle or ''}".strip()
            journal_rev = JournalComptable(
                enterprise_id=getattr(orig_journal, 'enterprise_id', 1),
                libelle=libelle,
                montant=abs(orig_journal.montant) if getattr(orig_journal, 'montant', None) is not None else abs(float(orig_line.debit or 0) - float(orig_line.credit or 0)),
                type_operation="annulation",
                reference=f"REV-{orig_journal.reference or orig_journal.id}-{ecriture_id}",
                description=f"Annulation écriture ID {ecriture_id} - {reason or ''}",
                user_id=user_id,
                date_operation=self._local_now()
            )
            session.add(journal_rev)
            session.flush()

            # Inverser toutes les écritures du journal original
            original_lines = session.query(EcritureComptable).filter(EcritureComptable.journal_id == orig_journal.id).order_by(EcritureComptable.ordre).all()
            # Renuméroter séquentiellement les écritures inverses
            for idx, line in enumerate(original_lines, start=1):
                rev_line = EcritureComptable(
                    journal_id=journal_rev.id,
                    compte_comptable_id=line.compte_comptable_id,
                    debit=(float(line.credit or 0)),
                    credit=(float(line.debit or 0)),
                    ordre=idx,
                    libelle=f"Annulation - {line.libelle or ''}".strip()
                )
                session.add(rev_line)

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            self.error_occurred.emit(f"Erreur annulation écriture comptable: {e}")
            return False

        finally:
            db_manager.close_session()
    
    def delete_accounting_entry(self, ecriture_id, user_id=1, reason=None):
        """Supprimer une écriture comptable et son journal associé (écritures liées).

        Recherche l'écriture, identifie le journal parent et supprime toutes les écritures de ce journal
        puis supprime le journal.
        """
        try:
            from ayanna_erp.modules.comptabilite.model.comptabilite import (
                ComptaEcritures as EcritureComptable,
                ComptaJournaux as JournalComptable,
            )

            db_manager = get_database_manager()
            session = db_manager.get_session()

            # Vérifier que l'utilisateur est super admin
            from ayanna_erp.database.database_manager import User
            try:
                user_obj = session.query(User).filter(User.id == int(user_id)).first()
            except Exception:
                user_obj = None
            if not user_obj or getattr(user_obj, 'role', '') != 'super_admin':
                err = "Suppression interdite : seul un utilisateur avec le rôle 'super_admin' peut supprimer définitivement des écritures/journaux."
                self.error_occurred.emit(err)
                try:
                    session.close()
                except Exception:
                    pass
                return False

            orig_line = session.query(EcritureComptable).filter(EcritureComptable.id == int(ecriture_id)).first()
            if not orig_line:
                self.error_occurred.emit(f"Écriture {ecriture_id} introuvable")
                return False

            orig_journal = session.query(JournalComptable).filter(JournalComptable.id == orig_line.journal_id).first()
            if not orig_journal:
                self.error_occurred.emit(f"Journal lié à l'écriture {ecriture_id} introuvable")
                return False

            # Refuser la suppression si le libellé du journal commence par 'Règlement fournisseur'
            try:
                jlib = (getattr(orig_journal, 'libelle', '') or '').strip().lower()
                if jlib.startswith('règlement fournisseur') or jlib.startswith('reglement fournisseur'):
                    err = "Suppression refusée : les journaux dont le libellé commence par 'Règlement fournisseur' ne peuvent pas être supprimés."
                    self.error_occurred.emit(err)
                    return False
            except Exception:
                pass

            # Ne pas supprimer les journaux de type 'Entrée'
            try:
                jtype = (getattr(orig_journal, 'type_operation', '') or '').strip().lower()
                if 'entree' in jtype or 'entrée' in jtype:
                    err = "Suppression refusée : les journaux de type 'Entrée' ne peuvent pas être supprimés via cette opération."
                    self.error_occurred.emit(err)
                    return False
            except Exception:
                pass

            try:
                # Supprimer les écritures liées
                session.query(EcritureComptable).filter(EcritureComptable.journal_id == orig_journal.id).delete(synchronize_session=False)
                # Supprimer le journal
                session.delete(orig_journal)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                self.error_occurred.emit(f"Erreur lors de la suppression du journal/écritures: {e}")
                return False

        except Exception as e:
            try:
                session.rollback()
            except Exception:
                pass
            self.error_occurred.emit(f"Erreur suppression écriture comptable: {e}")
            return False

        finally:
            try:
                db_manager.close_session()
            except Exception:
                pass
            
    def get_expenses_statistics(self, start_date=None, end_date=None):
        """
        Récupérer les statistiques des dépenses
        
        Args:
            start_date (datetime): Date de début (optionnelle)
            end_date (datetime): Date de fin (optionnelle)
            
        Returns:
            dict: Statistiques des dépenses
        """
        try:
            from sqlalchemy import func
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Query de base
            expenses_query = session.query(EventExpense).filter(
                EventExpense.pos_id == self.pos_id
            )
            
            if start_date:
                expenses_query = expenses_query.filter(EventExpense.expense_date >= start_date)
            
            if end_date:
                expenses_query = expenses_query.filter(EventExpense.expense_date <= end_date)
            
            # Calculer les statistiques
            total_expenses = expenses_query.with_entities(func.sum(EventExpense.amount)).scalar() or 0
            expense_count = expenses_query.count()
            
            # Grouper par catégorie
            categories = expenses_query.with_entities(
                EventExpense.expense_type,
                func.sum(EventExpense.amount),
                func.count(EventExpense.id)
            ).group_by(EventExpense.expense_type).all()
            
            categories_stats = []
            for category, amount, count in categories:
                categories_stats.append({
                    'category': category,
                    'total_amount': float(amount),
                    'expense_count': count,
                    'percentage': (float(amount) / total_expenses * 100) if total_expenses > 0 else 0
                })
            
            session.close()
            
            return {
                'total_expenses': float(total_expenses),
                'expense_count': expense_count,
                'average_expense': float(total_expenses) / expense_count if expense_count > 0 else 0,
                'categories': categories_stats
            }
            
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {str(e)}")
            self.error_occurred.emit(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {
                'total_expenses': 0,
                'expense_count': 0,
                'average_expense': 0,
                'categories': []
            }
    
    def get_expenses_by_date_and_pos(self, target_date, pos_id):
        """
        Récupérer les dépenses pour une date et un POS donnés
        
        Args:
            target_date (date): La date cible
            pos_id (int): L'ID du point de vente
            
        Returns:
            list: Liste des dépenses
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            if isinstance(target_date, datetime):
                target_date = target_date.date()
                
            # Définir les bornes de la journée
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            expenses = session.query(EventExpense).filter(
                EventExpense.pos_id == pos_id,
                EventExpense.expense_date.between(start_datetime, end_datetime)
            ).order_by(EventExpense.expense_date.desc()).all()
            
            # Ajouter des informations supplémentaires
            for expense in expenses:
                expense.libelle = expense.description
                expense.categorie = expense.expense_type
                expense.montant = expense.amount
                expense.date_creation = expense.expense_date
                expense.utilisateur_nom = "Utilisateur"  # TODO: récupérer le vrai nom d'utilisateur
            
            return expenses
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des dépenses: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
