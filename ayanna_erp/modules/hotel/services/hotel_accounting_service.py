"""
HotelAccountingService – passerelle entre le module Hôtel et la Comptabilité.

Règles SYSCOHADA appliquées :
  RÉSERVATION  : Débit  Clients (4)   / Crédit  Produits hôtel (7)
  PAIEMENT     : Débit  Caisse   (5)   / Crédit  Clients (4)
  PROLONGEMENT : Débit  Clients (4)   / Crédit  Produits hôtel (7)   (delta nuits)
  CHECKOUT (moins que prévu) :
                 Débit  Produits hôtel (7) / Crédit  Clients (4)   (avoir)
  ANNULATION   : Débit  Produits hôtel (7) / Crédit  Clients (4)
  REMBOURSEMENT: Débit  Clients (4)   / Crédit  Caisse   (5)

Toutes les écritures sont loguées silencieusement : une erreur comptable
ne doit JAMAIS bloquer une opération hôtelière.
"""
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)


class HotelAccountingService:
    """Passe les écritures comptables liées aux opérations de l'hôtel."""

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------

    def _get_ctrl(self):
        """Instancie ComptabiliteController avec l'utilisateur de session."""
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
        return ComptabiliteController()

    def _get_enterprise_id(self) -> int:
        from ayanna_erp.core.session_manager import SessionManager
        eid = SessionManager.get_current_enterprise_id()
        return eid if eid else 1

    def _get_hotel_pos_id(self, enterprise_id: int) -> Optional[int]:
        """Retourne l'ID du POS Hôtel pour l'entreprise."""
        try:
            from ayanna_erp.database.database_manager import get_database_manager, POSPoint, Module
            db = get_database_manager()
            with db.session_scope() as session:
                row = (
                    session.query(POSPoint)
                    .join(Module, POSPoint.module_id == Module.id)
                    .filter(
                        POSPoint.enterprise_id == enterprise_id,
                        Module.name.ilike('%hotel%'),
                    )
                    .first()
                )
                return row.id if row else None
        except Exception as e:
            log.warning("_get_hotel_pos_id error: %s", e)
            return None

    def _get_config(self):
        """Retourne (ctrl, config, enterprise_id) ou (None, None, None) en cas d'échec."""
        try:
            enterprise_id = self._get_enterprise_id()
            pos_id = self._get_hotel_pos_id(enterprise_id)
            if not pos_id:
                log.info("Comptabilité hôtel : aucun POS Hôtel configuré (enterprise_id=%s).", enterprise_id)
                return None, None, None
            ctrl = self._get_ctrl()
            config = ctrl.get_compte_config(enterprise_id, pos_id)
            if not config:
                log.info("Comptabilité hôtel : aucune configuration comptable pour le POS %s.", pos_id)
                return None, None, None
            return ctrl, config, enterprise_id
        except Exception as e:
            log.warning("_get_config error: %s", e)
            return None, None, None

    def _get_user_id(self, user_id=None) -> Optional[int]:
        """Retourne user_id fourni ou celui de la session."""
        if user_id:
            return user_id
        try:
            from ayanna_erp.core.session_manager import SessionManager
            u = SessionManager.get_current_user()
            if u:
                return getattr(u, 'id', None) or (u.get('id') if isinstance(u, dict) else None)
        except Exception:
            pass
        return 1  # fallback admin

    def _passer(self, ctrl, enterprise_id: int, compte_debit_id: int,
                compte_credit_id: int, montant: float, libelle: str,
                reference: str, user_id=None, type_op: str = "od") -> bool:
        """Passe une écriture via transfert_journal. Retourne True si OK."""
        if montant <= 0:
            return True  # rien à passer
        uid = self._get_user_id(user_id)
        try:
            ok, msg = ctrl.transfert_journal(
                entreprise_id=enterprise_id,
                compte_debit_id=compte_debit_id,
                compte_credit_id=compte_credit_id,
                montant=montant,
                libelle=libelle,
                user_id=uid,
                type_operation=type_op,
                reference=reference,
            )
            if not ok:
                log.warning("Écriture comptable refusée [%s] : %s", reference, msg)
            return ok
        except Exception as e:
            log.exception("Erreur écriture comptable [%s] : %s", reference, e)
            return False

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def on_reservation(self, reservation_code: str, montant: float,
                       client_name: str, user_id=None) -> None:
        """
        Réservation créée :
          D/ Clients   –  C/ Produits hôtel
        """
        try:
            ctrl, cfg, eid = self._get_config()
            if not ctrl:
                return
            if not cfg.compte_client_id or not cfg.compte_vente_id:
                log.info("Comptabilité hôtel : comptes client/vente non configurés.")
                return
            libelle = (
                f"Réservation hôtel {reservation_code} – {client_name}"
            )
            self._passer(ctrl, eid,
                         compte_debit_id=cfg.compte_client_id,
                         compte_credit_id=cfg.compte_vente_id,
                         montant=montant,
                         libelle=libelle,
                         reference=reservation_code,
                         user_id=user_id,
                         type_op="vente")
        except Exception as e:
            log.exception("on_reservation accounting error: %s", e)

    def on_paiement(self, reservation_code: str, montant: float,
                    method: str, client_name: str, user_id=None,
                    compte_id: Optional[int] = None) -> None:
        """
        Paiement encaissé :
          D/ Caisse du mode de paiement (ou compte_caisse_id config)  –  C/ Clients
        Méthode 'credit' → aucune écriture (dette, non encaissé).
        """
        try:
            if method == 'credit' or montant <= 0:
                return
            ctrl, cfg, eid = self._get_config()
            if not ctrl:
                return
            if not cfg.compte_client_id:
                log.info("Comptabilité hôtel : compte client non configuré.")
                return
            # Compte à débiter : celui du mode de paiement en priorité,
            # sinon le compte caisse de la configuration POS.
            compte_debit = compte_id or cfg.compte_caisse_id
            if not compte_debit:
                log.info("Comptabilité hôtel : aucun compte caisse disponible pour le paiement.")
                return
            method_label = {
                'cash': 'Espèces', 'airtelmoney': 'Airtel Money',
                'orangemoney': 'Orange Money', 'mpesa': 'M-Pesa',
                'equitybcdc': 'Equity BCDC', 'tmb': 'TMB',
                'rawbank': 'Rawbank', 'smico': 'Smico',
            }.get(method, method)
            libelle = (
                f"Paiement {method_label} – {reservation_code} – {client_name}"
            )
            self._passer(ctrl, eid,
                         compte_debit_id=compte_debit,
                         compte_credit_id=cfg.compte_client_id,
                         montant=montant,
                         libelle=libelle,
                         reference=reservation_code,
                         user_id=user_id,
                         type_op="caisse")
        except Exception as e:
            log.exception("on_paiement accounting error: %s", e)

    def on_prolongement(self, reservation_code: str, montant_delta: float,
                        client_name: str, user_id=None) -> None:
        """
        Prolongement du séjour (nuits supplémentaires) :
          D/ Clients   –  C/ Produits hôtel
        """
        try:
            if montant_delta <= 0:
                return
            ctrl, cfg, eid = self._get_config()
            if not ctrl:
                return
            if not cfg.compte_client_id or not cfg.compte_vente_id:
                return
            libelle = (
                f"Prolongement séjour {reservation_code} – {client_name} "
                f"(+{montant_delta:,.0f})"
            )
            self._passer(ctrl, eid,
                         compte_debit_id=cfg.compte_client_id,
                         compte_credit_id=cfg.compte_vente_id,
                         montant=montant_delta,
                         libelle=libelle,
                         reference=reservation_code,
                         user_id=user_id,
                         type_op="vente")
        except Exception as e:
            log.exception("on_prolongement accounting error: %s", e)

    def on_checkout_avoir(self, reservation_code: str, montant_avoir: float,
                          client_name: str, user_id=None) -> None:
        """
        Checkout avec moins de jours que prévu → avoir sur le produit :
          D/ Produits hôtel   –  C/ Clients
        """
        try:
            if montant_avoir <= 0:
                return
            ctrl, cfg, eid = self._get_config()
            if not ctrl:
                return
            if not cfg.compte_vente_id or not cfg.compte_client_id:
                return
            libelle = (
                f"Avoir checkout {reservation_code} – {client_name} "
                f"(réduction {montant_avoir:,.0f})"
            )
            self._passer(ctrl, eid,
                         compte_debit_id=cfg.compte_vente_id,
                         compte_credit_id=cfg.compte_client_id,
                         montant=montant_avoir,
                         libelle=libelle,
                         reference=reservation_code,
                         user_id=user_id,
                         type_op="od")
        except Exception as e:
            log.exception("on_checkout_avoir accounting error: %s", e)

    def on_annulation(self, reservation_code: str, montant: float,
                      client_name: str, user_id=None) -> None:
        """
        Annulation de réservation :
          D/ Produits hôtel   –  C/ Clients
        """
        try:
            if montant <= 0:
                return
            ctrl, cfg, eid = self._get_config()
            if not ctrl:
                return
            if not cfg.compte_vente_id or not cfg.compte_client_id:
                return
            libelle = (
                f"Annulation réservation {reservation_code} – {client_name}"
            )
            self._passer(ctrl, eid,
                         compte_debit_id=cfg.compte_vente_id,
                         compte_credit_id=cfg.compte_client_id,
                         montant=montant,
                         libelle=libelle,
                         reference=reservation_code,
                         user_id=user_id,
                         type_op="od")
        except Exception as e:
            log.exception("on_annulation accounting error: %s", e)

    def on_remboursement(self, reservation_code: str, montant: float,
                         client_name: str, user_id=None) -> None:
        """
        Remboursement suite à annulation (client avait déjà payé) :
          D/ Clients   –  C/ Caisse
        """
        try:
            if montant <= 0:
                return
            ctrl, cfg, eid = self._get_config()
            if not ctrl:
                return
            if not cfg.compte_client_id or not cfg.compte_caisse_id:
                return
            libelle = (
                f"Remboursement annulation {reservation_code} – {client_name}"
            )
            self._passer(ctrl, eid,
                         compte_debit_id=cfg.compte_client_id,
                         compte_credit_id=cfg.compte_caisse_id,
                         montant=montant,
                         libelle=libelle,
                         reference=reservation_code,
                         user_id=user_id,
                         type_op="caisse")
        except Exception as e:
            log.exception("on_remboursement accounting error: %s", e)


# Singleton léger — instancié une seule fois
_hotel_acc = HotelAccountingService()


def get_hotel_accounting_service() -> HotelAccountingService:
    return _hotel_acc
