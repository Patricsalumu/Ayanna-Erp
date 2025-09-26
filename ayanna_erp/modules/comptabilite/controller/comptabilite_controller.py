"""
Contrôleur central du module Comptabilité

Gère les requêtes SQLAlchemy, calculs de soldes, transferts, et fournit les données aux widgets.
"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.comptabilite.model.comptabilite import (
    ComptaClasses, ComptaComptes, ComptaJournaux, ComptaEcritures, ComptaConfig
)
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

# Alias pour compatibilité avec l'ancien code
CompteComptable = ComptaComptes
ClasseComptable = ComptaClasses
EcritureComptable = ComptaEcritures
JournalComptable = ComptaJournaux
CompteConfig = ComptaConfig
import datetime


class ComptabiliteController:
    """Contrôleur principal pour la gestion de la comptabilité"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.entreprise_controller.get_currency_symbol()
        except:
            return "€"  # Fallback
    
    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        try:
            return self.entreprise_controller.format_amount(amount)
        except:
            return f"{amount:.2f} €"  # Fallback
    
    def get_comptes_vente(self, entreprise_id=None):
        """
        Récupère la liste des comptes comptables de vente (classe 7)
        pour utilisation dans les formulaires de services et produits
        Filtre par entreprise si entreprise_id est fourni
        """
        try:
            # Base query: Récupérer les comptes de classe 7 (Produits/Ventes)
            query = self.session.query(ComptaComptes).join(
                ComptaClasses, ComptaComptes.classe_comptable_id == ComptaClasses.id
            ).filter(
                ComptaComptes.numero.like('7%')  # Comptes de classe 7
            )
            
            # Filtrer par entreprise si spécifié
            if entreprise_id:
                query = query.filter(ComptaClasses.enterprise_id == entreprise_id)
            
            comptes = query.order_by(ComptaComptes.numero).all()
            
            return comptes
        except Exception as e:
            print(f"Erreur lors de la récupération des comptes de vente: {e}")
            return []

    def get_compte_by_id(self, compte_id):
        """
        Récupère un compte comptable par son ID
        """
        try:
            compte = self.session.query(ComptaComptes).filter(
                ComptaComptes.id == compte_id
            ).first()
            return compte
        except Exception as e:
            print(f"Erreur lors de la récupération du compte ID {compte_id}: {e}")
            return None

    def get_bilan_comptable(self, entreprise_id, date_debut, date_fin):
        """
        Retourne un bilan comptable structuré pour une entreprise donnée.
        Structure :
        {
            "actifs": [{"compte": "101", "nom": "Banque", "solde": 20000}, ...],
            "passifs": [{"compte": "201", "nom": "Capital", "solde": 50000}, ...],
            "total_actifs": 35000,
            "total_passifs": 58000
        }
        """
        from sqlalchemy import func
        # Import d�j� fait en haut du fichier
        import datetime
        # Inclure toute la journée de la date de fin si c'est un objet date
        if isinstance(date_fin, datetime.date) and not isinstance(date_fin, datetime.datetime):
            date_fin = datetime.datetime.combine(date_fin, datetime.time.max)

        # Récupérer tous les comptes actifs/passifs de l'entreprise
        comptes = (
            self.session.query(ComptaComptes, ComptaClasses)
            .join(ComptaClasses, ComptaComptes.classe_comptable_id == ComptaClasses.id)
            .filter(ComptaClasses.enterprise_id == entreprise_id)
            .filter(ComptaClasses.type.in_(["actif", "passif"]))
            .all()
        )

        actifs = []
        passifs = []
        total_actifs = 0.0
        total_passifs = 0.0

        for compte, classe in comptes:
            # Agréger les écritures sur la période et l'entreprise
            res = (
                self.session.query(
                    func.sum(ComptaEcritures.debit).label("total_debit"),
                    func.sum(ComptaEcritures.credit).label("total_credit")
                )
                .join(ComptaJournaux, ComptaEcritures.journal_id == ComptaJournaux.id)
                .filter(ComptaEcritures.compte_comptable_id == compte.id)
                .filter(ComptaJournaux.enterprise_id == entreprise_id)
                .filter(ComptaJournaux.date_operation >= date_debut)
                .filter(ComptaJournaux.date_operation <= date_fin)
                .first()
            )
            total_debit = float(res.total_debit or 0)
            total_credit = float(res.total_credit or 0)
            if classe.type == "actif":
                solde = total_debit - total_credit
                actifs.append({"compte": compte.numero, "nom": compte.nom, "solde": solde})
                total_actifs += solde
            elif classe.type == "passif":
                solde = total_credit - total_debit
                passifs.append({"compte": compte.numero, "nom": compte.nom, "solde": solde})
                total_passifs += solde

        # Ajout du résultat net dans le passif
        resultat = self.get_compte_resultat(entreprise_id, date_debut, date_fin)
        resultat_net = resultat.get("resultat_net", 0)
        passifs.append({"compte": "Résultat Net", "nom": "Résultat de l'exercice", "solde": resultat_net})
        total_passifs += resultat_net

        return {
            "actifs": actifs,
            "passifs": passifs,
            "total_actifs": total_actifs,
            "total_passifs": total_passifs
        }
    def export_detail_compte_pdf(self, data, file_path, entreprise_id=None):
        """Export PDF des détails d'un compte avec style uniforme, logo BLOB, infos école, titre et tableau aligné à gauche."""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import Table, TableStyle
        import datetime
        import os
        from sqlalchemy import select

        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Récupérer les informations de l'entreprise dynamiquement
        try:
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            entreprise_controller = EntrepriseController()
            # Utiliser l'entreprise_id passé en paramètre ou celui de l'instance
            if not entreprise_id:
                entreprise_id = getattr(self, 'entreprise_id', 1)
            entreprise_info = entreprise_controller.get_current_enterprise(entreprise_id)
        except Exception as e:
            print(f"Erreur lors de la récupération des infos entreprise: {e}")
            # Fallback vers les valeurs par défaut
            entreprise_info = {
                'name': 'AYANNA ERP',
                'address': '123 Avenue de la République',
                'phone': '+243 123 456 789',
                'email': 'contact@ayanna-erp.com',
                'rccm': 'CD/KIN/RCCM/23-B-1234'
            }

        # Mention spéciale en haut
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawCentredString(width/2, height-1.2*cm, f"Généré par {entreprise_info['name']} - {now}")
        c.setFillColorRGB(0, 0, 0)

        # Bloc logo + infos école
        logo_x = 1*cm
        logo_y = height-2.5*cm
        logo_w = 1.5*cm
        logo_h = 1.5*cm
        info_x = logo_x + logo_w + 0.5*cm
        info_y = logo_y + logo_h - 0.2*cm
        
        # Utiliser les informations récupérées dynamiquement
        school_name = entreprise_info['name']
        school_address = entreprise_info['address']
        school_phone = entreprise_info['phone']
        school_email = entreprise_info['email']
        logo_path = os.path.join(os.path.dirname(__file__), "../../images/favicon.ico")
        
        # Gestion du logo depuis la base de données
        if entreprise_info.get('logo'):
            try:
                logo_path = os.path.join(os.path.dirname(__file__), f"../../images/logo_{entreprise_id}.png")
                with open(logo_path, "wb") as f:
                    f.write(entreprise_info['logo'])
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du logo: {e}")
        
        if os.path.exists(logo_path):
            c.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto')
        c.setFont("Helvetica-Bold", 12)
        c.drawString(info_x, logo_y+logo_h-0.2*cm, school_name)
        c.setFont("Helvetica", 9)
        c.drawString(info_x, logo_y+logo_h-0.8*cm, school_address)
        c.drawString(info_x, logo_y+logo_h-1.4*cm, f"Tél : {school_phone}")
        c.drawString(info_x, logo_y+logo_h-2.0*cm, f"Email : {school_email}")

        # Récupérer le nom du compte (si possible)
        nom_compte = ""
        if data and "compte_nom" in data[0]:
            nom_compte = data[0]["compte_nom"]
        elif data and "nom" in data[0]:
            nom_compte = data[0]["nom"]
        # Titre centré + nom du compte
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(width/2, height-4*cm, "DÉTAIL DES ÉCRITURES DU COMPTE")
        if nom_compte:
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(width/2, height-4.7*cm, f"Compte : {nom_compte}")
        
        # Récupérer la devise de l'entreprise
        devise = entreprise_info.get('currency', 'USD')
        
        # Tableau
        table_data = [["Date", "Libellé", "Débit", "Crédit"]]
        total_debit = 0.0
        total_credit = 0.0
        for row in data:
            # Récupère la valeur affichée dans le tableau, nettoie et convertit en float
            debit_str = str(row.get("debit", "0"))
            credit_str = str(row.get("credit", "0"))
            try:
                debit_val = float(debit_str.replace(" ","").replace(devise,"").replace(",",""))
                credit_val = float(credit_str.replace(" ","").replace(devise,"").replace(",",""))
            except ValueError:
                raise ValueError(f"Valeur non convertible en float : {debit_str} ou {credit_str}")
            total_debit += debit_val
            total_credit += credit_val
            # Correction : afficher le nom du journal si disponible
            libelle = row.get("journal", "") or row.get("libelle", "")
            table_data.append([
                row.get("date", ""),
                libelle,
                debit_str,
                credit_str,
            ])
        solde = total_debit - total_credit
        # Couleurs personnalisées pour l'en-tête
        app_bg = colors.HexColor("#2C3E50")  # Bleu foncé
        app_fg = colors.HexColor("#ECF0F1")  # Blanc/gris clair
        table = Table(table_data, colWidths=[3*cm, 8*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), app_bg),
            ("TEXTCOLOR", (0,0), (-1,0), app_fg),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        table.wrapOn(c, width-2*cm, height)
        table_height = table._height
        table.drawOn(c, 1*cm, height-5*cm-table_height)


        # Ajout des totaux en bas du PDF
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        y_totaux = height-5*cm-table_height-1*cm
        c.drawString(1*cm, y_totaux, f"Total Débit : {total_debit:,.2f} {devise}")
        c.drawString(6*cm, y_totaux, f"Total Crédit : {total_credit:,.2f} {devise}")
        c.drawString(11*cm, y_totaux, f"Solde : {solde:,.2f} {devise}")
        c.setFillColorRGB(0, 0, 0)

        c.showPage()
        c.save()
    # --- Gestion de la configuration des comptes (caisse, frais, client) ---
    def get_compte_config(self, enterprise_id, pos_id=None):
        """Récupère la configuration des comptes pour une entreprise et un point de vente (ou None si pas encore configuré)"""
        query = self.session.query(CompteConfig).filter_by(enterprise_id=enterprise_id)
        if pos_id:
            query = query.filter_by(pos_id=pos_id)
        return query.first()

    def set_compte_config(self, enterprise_id, pos_id, compte_caisse_id=None, compte_banque_id=None, 
                         compte_client_id=None, compte_fournisseur_id=None, 
                         compte_tva_id=None, compte_achat_id=None, compte_remise_id=None):
        """Crée ou met à jour la configuration des comptes pour une entreprise et un point de vente"""
        config = self.session.query(CompteConfig).filter_by(enterprise_id=enterprise_id, pos_id=pos_id).first()
        if config:
            # Mettre à jour les champs fournis
            if compte_caisse_id is not None:
                config.compte_caisse_id = compte_caisse_id
            if compte_banque_id is not None:
                config.compte_banque_id = compte_banque_id
            if compte_client_id is not None:
                config.compte_client_id = compte_client_id
            if compte_fournisseur_id is not None:
                config.compte_fournisseur_id = compte_fournisseur_id
            if compte_tva_id is not None:
                config.compte_tva_id = compte_tva_id
            if compte_achat_id is not None:
                config.compte_achat_id = compte_achat_id
            if compte_remise_id is not None:
                config.compte_remise_id = compte_remise_id
        else:
            config = CompteConfig(
                enterprise_id=enterprise_id,
                pos_id=pos_id,
                compte_caisse_id=compte_caisse_id,
                compte_banque_id=compte_banque_id,
                compte_client_id=compte_client_id,
                compte_fournisseur_id=compte_fournisseur_id,
                compte_tva_id=compte_tva_id,
                compte_achat_id=compte_achat_id,
                compte_remise_id=compte_remise_id
            )
            self.session.add(config)
        self.session.commit()
        return config

    def get_pos_points(self, enterprise_id):
        """Récupère la liste des points de vente pour une entreprise"""
        from ayanna_erp.database.database_manager import POSPoint
        return self.session.query(POSPoint).filter_by(enterprise_id=enterprise_id).all()

    def get_comptes_par_classe(self, enterprise_id, classe_code):
        """Récupère les comptes d'une classe donnée (ex: '4' pour clients, '5' pour caisse/banque, etc.)"""
        return (self.session.query(CompteComptable)
                .join(ClasseComptable)
                .filter(ClasseComptable.enterprise_id == enterprise_id)
                .filter(ClasseComptable.code.like(f'{classe_code}%'))
                .filter(CompteComptable.actif == True)
                .all())

    def get_comptes_caisse_banque(self, entreprise_id):
        """
        Retourne la liste des comptes de classe 5 (caisse, banque) actifs pour l'entreprise.
        """
        # Import remplac� par les nouveaux mod�les
        # Classe 5 = caisse, banque, etc. (code commence par '5')
        classes = self.session.query(ClasseComptable).filter(
            ClasseComptable.enterprise_id == entreprise_id,
            ClasseComptable.actif == True
        ).all()
        comptes = []
        for cl in classes:
            comptes += [c for c in cl.comptes if c.actif]
        return comptes

    def get_solde_compte(self, compte_id):
        """
        Calcule le solde d'un compte (total débit - total crédit)
        """
        # Import remplac� par les nouveaux mod�les
        ecritures = self.session.query(EcritureComptable).filter_by(compte_comptable_id=compte_id).all()
        total_debit = sum(float(e.debit or 0) for e in ecritures)
        total_credit = sum(float(e.credit or 0) for e in ecritures)
        return total_debit - total_credit


    def transfert_journal(self, entreprise_id, compte_debit_id, compte_credit_id, montant, libelle):
        """
        Effectue un transfert de fonds entre deux comptes.
        - On ne peut créditer un compte caisse (classe 5) que dans la limite de son solde.
        """
        # Import remplac� par les nouveaux mod�les
        from datetime import datetime
        try:
            
            compte_credit = self.session.query(CompteComptable).get(compte_credit_id)
            classe_credit = self.session.query(ClasseComptable).get(compte_credit.classe_comptable_id)
            
            # Vérification du solde uniquement pour les comptes caisse (classe 5)
            if classe_credit and classe_credit.code == "5":
                solde_credit = self.get_solde_compte(compte_credit_id)
                if montant > solde_credit:
                    return False, "Le solde du compte caisse à créditer est insuffisant."

            # Créer le journal
            journal = JournalComptable(
                date_operation=datetime.now(),
                libelle=libelle,
                montant=montant,
                type_operation="transfert",
                enterprise_id=entreprise_id
            )
            self.session.add(journal)
            self.session.flush()  # Pour obtenir l'ID du journal

            # Écriture débit
            ecriture_debit = EcritureComptable(
                journal_id=journal.id,
                compte_comptable_id=compte_debit_id,
                debit=montant,
                credit=0,
                ordre=1
            )
            # Écriture crédit
            ecriture_credit = EcritureComptable(
                journal_id=journal.id,
                compte_comptable_id=compte_credit_id,
                debit=0,
                credit=montant,
                ordre=2
            )
            self.session.add(ecriture_debit)
            self.session.add(ecriture_credit)
            self.session.commit()
            return True, "Transfert effectué avec succès."
        except Exception as e:
            self.session.rollback()
            return False, f"Erreur lors du transfert : {e}"

    # À compléter : méthodes pour journal, grand livre, balance, bilan, etc.

    def get_journaux_comptables(self, entreprise_id):
        """
        Retourne la liste des journaux comptables pour une entreprise donnée.
        Args:
            entreprise_id (int): ID de l'entreprise
        Returns:
            list: Liste des objets JournalComptable
        """
        # Import remplac� par les nouveaux mod�les
        journaux = self.session.query(JournalComptable).filter_by(enterprise_id=entreprise_id).order_by(JournalComptable.date_operation.desc()).all()
        return journaux

    def get_ecritures_du_journal(self, journal_id):
        print(f"[DEBUG] Appel get_ecritures_du_journal avec journal_id={journal_id}")
        """
        Retourne les deux écritures comptables (débit/crédit) associées à un journal donné.
        Args:
            journal_id (int): ID du journal comptable
        Returns:
            list: Liste des objets EcritureComptable (en général 2 lignes)
        """
        # Import remplac� par les nouveaux mod�les
        ecritures = self.session.query(EcritureComptable).filter_by(journal_id=journal_id).order_by(EcritureComptable.ordre.asc()).all()
        print(f"[DEBUG] get_ecritures_du_journal retourne {len(ecritures)} écritures")
        return ecritures
    """
    Classe centrale pour la logique métier et l'accès aux données comptables.
    """
 # Grand Livre
    def get_grand_livre(self, entreprise_id):
        """
        Retourne une liste de dicts pour l'entreprise donnée.
        """
        # Import remplac� par les nouveaux mod�les
        comptes = self.session.query(CompteComptable).join(ClasseComptable).filter(ClasseComptable.enterprise_id == entreprise_id).all()
        result = []
        for compte in comptes:
            ecritures = self.session.query(EcritureComptable).filter(EcritureComptable.compte_comptable_id == compte.id).all()
            total_debit = sum(e.debit for e in ecritures)
            total_credit = sum(e.credit for e in ecritures)
            solde = total_debit - total_credit
            result.append({
                "numero": compte.numero,
                "nom": compte.nom,
                "total_debit": total_debit,
                "total_credit": total_credit,
                "solde": solde,
                "id": compte.id
            })
        return result

    def get_ecritures_compte(self, compte_id, entreprise_id):
        """
        Retourne la liste des écritures d’un compte pour l'entreprise donnée.
        """
        # Import remplac� par les nouveaux mod�les
        ecritures = (
            self.session.query(EcritureComptable, JournalComptable)
            .join(JournalComptable, EcritureComptable.journal_id == JournalComptable.id)
            .filter(EcritureComptable.compte_comptable_id == compte_id)
            .filter(JournalComptable.enterprise_id == entreprise_id)
            .order_by(JournalComptable.date_operation)
            .all()
        )
        result = []
        for ecriture, journal in ecritures:
            result.append({
                "date": journal.date_operation.strftime("%d/%m/%Y"),
                "journal": getattr(journal, 'nom', ''),
                "journal_id": ecriture.journal_id,
                "libelle": getattr(ecriture, 'libelle', ''),
                "debit": ecriture.debit,
                "credit": ecriture.credit
            })               
        return result

    def export_grand_livre_pdf(self, data, file_path):
        """Génère un PDF formaté du grand livre complet avec charte graphique uniforme"""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import Table, TableStyle
        import datetime
        import os

        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Récupérer les informations de l'entreprise dynamiquement
        try:
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            entreprise_controller = EntrepriseController()
            entreprise_id = getattr(self, 'entreprise_id', 1)
            entreprise_info = entreprise_controller.get_current_enterprise(entreprise_id)
        except Exception as e:
            print(f"Erreur lors de la récupération des infos entreprise: {e}")
            # Fallback vers les valeurs par défaut
            entreprise_info = {
                'name': 'AYANNA ERP',
                'address': '123 Avenue de la République',
                'phone': '+243 123 456 789',
                'email': 'contact@ayanna-erp.com',
                'rccm': 'CD/KIN/RCCM/23-B-1234'
            }

        # En-tête
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawCentredString(width/2, height-1.2*cm, f"Généré par {entreprise_info['name']} - {now}")
        c.setFillColorRGB(0, 0, 0)

        # Logo + infos école (optionnel)
        logo_path = os.path.join(os.path.dirname(__file__), "../../images/favicon.ico")
        # Gestion du logo depuis la base de données
        if entreprise_info.get('logo'):
            try:
                logo_path = os.path.join(os.path.dirname(__file__), f"../../images/logo_{entreprise_id}.png")
                with open(logo_path, "wb") as f:
                    f.write(entreprise_info['logo'])
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du logo: {e}")
        
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 1*cm, height-2.5*cm, width=1.5*cm, height=1.5*cm, mask='auto')
        c.setFont("Helvetica-Bold", 12)
        c.drawString(3*cm, height-2*cm, entreprise_info['name'])
        c.setFont("Helvetica", 9)
        c.drawString(3*cm, height-2.6*cm, entreprise_info['address'])
        c.drawString(3*cm, height-3.2*cm, f"Tél: {entreprise_info['phone']}")
        c.drawString(3*cm, height-3.8*cm, f"Email: {entreprise_info['email']}")
        c.drawString(3*cm, height-4.4*cm, f"RCCM: {entreprise_info['rccm']}")

        # Titre centré
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(width/2, height-5.5*cm, "GRAND LIVRE COMPTABLE")

        # Table
        table_data = [["Numéro", "Libellé", "Total Débit", "Total Crédit", "Solde"]]
        for row in data:
            table_data.append([
                row["numero"],
                row["nom"],
                self._format_pdf_currency(row["total_debit"]),
                self._format_pdf_currency(row["total_credit"]),
                self._format_pdf_currency(row["solde"]),
            ])
        table = Table(table_data, colWidths=[3*cm, 6*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("ALIGN", (2,1), (-1,-1), "RIGHT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        table.wrapOn(c, width-2*cm, height)
        table_height = table._height
        table.drawOn(c, 1*cm, height-4.5*cm-table_height)

        c.showPage()
        c.save()

    

    def _format_pdf_currency(self, value):
        try:
            # Convertir en float si c'est une chaîne
            if isinstance(value, str):
                # Retirer les espaces et remplacer les virgules par des points
                value = value.replace(" ", "").replace(",", ".")
                value = float(value)
            elif value is None:
                value = 0.0
            
            currency_symbol = self.get_currency_symbol()
            return f"{value:,.2f} {currency_symbol}".replace(",", " ").replace(".00", "")
        except Exception as e:
            print(f"Erreur format currency: {e}")
            # Fallback avec conversion sécurisée
            try:
                if isinstance(value, str):
                    value = float(value.replace(" ", "").replace(",", "."))
                elif value is None:
                    value = 0.0
                return f"{value:,.2f} €".replace(",", " ").replace(".00", "")
            except:
                return f"0.00 €"




    def export_compte_resultat_pdf(self, data, file_path):
        """Génère un PDF formaté du compte de résultat avec charte graphique uniforme"""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import Table, TableStyle
        import datetime
        import os

        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Récupérer les informations de l'entreprise dynamiquement
        try:
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            entreprise_controller = EntrepriseController()
            entreprise_id = getattr(self, 'entreprise_id', 1)
            entreprise_info = entreprise_controller.get_current_enterprise(entreprise_id)
        except Exception as e:
            print(f"Erreur lors de la récupération des infos entreprise: {e}")
            # Fallback vers les valeurs par défaut
            entreprise_info = {
                'name': 'AYANNA ERP',
                'address': '123 Avenue de la République',
                'phone': '+243 123 456 789',
                'email': 'contact@ayanna-erp.com',
                'rccm': 'CD/KIN/RCCM/23-B-1234'
            }

        # En-tête
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawCentredString(width/2, height-1.2*cm, f"Généré par {entreprise_info['name']} - {now}")
        c.setFillColorRGB(0, 0, 0)

        # Logo + infos entreprise
        logo_path = os.path.join(os.path.dirname(__file__), "../../images/favicon.ico")
        # Gestion du logo depuis la base de données
        if entreprise_info.get('logo'):
            try:
                logo_path = os.path.join(os.path.dirname(__file__), f"../../images/logo_{entreprise_id}.png")
                with open(logo_path, "wb") as f:
                    f.write(entreprise_info['logo'])
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du logo: {e}")
        
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 1*cm, height-2.5*cm, width=1.5*cm, height=1.5*cm, mask='auto')
        c.setFont("Helvetica-Bold", 12)
        c.drawString(3*cm, height-2*cm, entreprise_info['name'])
        c.setFont("Helvetica", 9)
        c.drawString(3*cm, height-2.6*cm, entreprise_info['address'])
        c.drawString(3*cm, height-3.2*cm, f"Tél: {entreprise_info['phone']}")
        c.drawString(3*cm, height-3.8*cm, f"Email: {entreprise_info['email']}")
        c.drawString(3*cm, height-4.4*cm, f"RCCM: {entreprise_info['rccm']}")

        # Titre centré
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(width/2, height-5.5*cm, "COMPTE DE RÉSULTAT")

        # Charges
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*cm, height-6.5*cm, "Charges (Classe 6)")
        table_data = [["Compte", "Libellé", "Total"]]
        for row in data["charges"]:
            table_data.append([
                row["compte"],
                row["nom"],
                self._format_pdf_currency(row["total"]),
            ])
        table = Table(table_data, colWidths=[3*cm, 8*cm, 4*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("ALIGN", (2,1), (-1,-1), "RIGHT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        table.wrapOn(c, width-2*cm, height)
        table_height = table._height
        table.drawOn(c, 1*cm, height-5*cm-table_height)

        # Produits
        y = height-5*cm-table_height-1*cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*cm, y, "Produits (Classe 7)")
        table_data2 = [["Compte", "Libellé", "Total"]]
        for row in data["produits"]:
            table_data2.append([
                row["compte"],
                row["nom"],
                self._format_pdf_currency(row["total"]),
            ])
        table2 = Table(table_data2, colWidths=[3*cm, 8*cm, 4*cm])
        table2.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("ALIGN", (2,1), (-1,-1), "RIGHT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        table2.wrapOn(c, width-2*cm, height)
        table2_height = table2._height
        table2.drawOn(c, 1*cm, y-0.5*cm-table2_height)

        # Résultat net
        y_final = y-0.5*cm-table2_height-1*cm
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(1*cm, y_final, f"Résultat Net : {self._format_pdf_currency(data['resultat_net'])}")
        c.setFillColorRGB(0, 0, 0)

        c.showPage()
        c.save()

    
    # Comptes Comptables
    def get_comptes(self, entreprise_id):
        """Retourne tous les comptes comptables avec leur classe"""
        # Import remplac� par les nouveaux mod�les
        # Import remplac� par les nouveaux mod�les
        comptes = self.session.query(CompteComptable).join(ClasseComptable).filter(ClasseComptable.enterprise_id == entreprise_id).all()
        result = []
        for compte in comptes:
            classe = self.session.query(ClasseComptable).filter(ClasseComptable.id == compte.classe_comptable_id).first()
            result.append({
                "id": compte.id,
                "numero": compte.numero,
                "nom": compte.nom,
                "libelle": compte.libelle,
                "classe": classe.nom if classe else "",
            })
        return result

    def get_compte_resultat(self, entreprise_id, date_debut, date_fin):
        from sqlalchemy import func
        # Import remplac� par les nouveaux mod�les

        # Charges (classe 6, type 'charge')
        charges_query = (
            self.session.query(
                CompteComptable.numero.label("compte"),
                CompteComptable.nom.label("nom"),
                func.sum(EcritureComptable.debit).label("total")
            )
            .join(ClasseComptable, CompteComptable.classe_comptable_id == ClasseComptable.id)
            .join(EcritureComptable, EcritureComptable.compte_comptable_id == CompteComptable.id)
            .join(JournalComptable, EcritureComptable.journal_id == JournalComptable.id)
            .filter(ClasseComptable.enterprise_id == entreprise_id)
            .filter(ClasseComptable.type == "charge")
            .filter(JournalComptable.enterprise_id == entreprise_id)
            .filter(JournalComptable.date_operation >= date_debut)
            .filter(JournalComptable.date_operation <= date_fin)
            .group_by(CompteComptable.numero, CompteComptable.nom)
        )
        charges = [
            {"compte": row.compte, "nom": row.nom, "total": float(row.total or 0)}
            for row in charges_query
        ]
        # ...debug supprimé...

        # Produits (classe 7, type 'produit')
        produits_query = (
            self.session.query(
                CompteComptable.numero.label("compte"),
                CompteComptable.nom.label("nom"),
                func.sum(EcritureComptable.credit).label("total")
            )
            .join(ClasseComptable, CompteComptable.classe_comptable_id == ClasseComptable.id)
            .join(EcritureComptable, EcritureComptable.compte_comptable_id == CompteComptable.id)
            .join(JournalComptable, EcritureComptable.journal_id == JournalComptable.id)
            .filter(ClasseComptable.enterprise_id == entreprise_id)
            .filter(ClasseComptable.type == "produit")
            .filter(JournalComptable.enterprise_id == entreprise_id)
            .filter(JournalComptable.date_operation >= date_debut)
            .filter(JournalComptable.date_operation <= date_fin)
            .group_by(CompteComptable.numero, CompteComptable.nom)
        )
        produits = [
            {"compte": row.compte, "nom": row.nom, "total": float(row.total or 0)}
            for row in produits_query
        ]
        # ...debug supprimé...

        total_charges = sum(c["total"] for c in charges)
        total_produits = sum(p["total"] for p in produits)
        resultat_net = total_produits - total_charges
        # ...debug supprimé...

        return {
            "charges": charges,
            "produits": produits,
            "resultat_net": resultat_net
        }

    def add_compte(self, data):
        """Ajoute un compte"""
        # Import remplac� par les nouveaux mod�les
        compte = CompteComptable(
            numero=data["numero"],
            nom=data["nom"],
            libelle=data["libelle"],
            classe_comptable_id=data["classe_comptable_id"]
        )
        self.session.add(compte)
        self.session.commit()
        return compte.id

    def update_compte(self, compte_id, data):
        """Modifie un compte"""
        # Import remplac� par les nouveaux mod�les
        compte = self.session.query(CompteComptable).filter(CompteComptable.id == compte_id).first()
        if not compte:
            raise Exception("Compte introuvable")
        compte.numero = data["numero"]
        compte.nom = data["nom"]
        compte.classe_comptable_id = data["classe_comptable_id"]
        self.session.commit()

    def delete_compte(self, compte_id):
        """Supprime un compte"""
        # Import remplac� par les nouveaux mod�les
        compte = self.session.query(CompteComptable).filter(CompteComptable.id == compte_id).first()
        if not compte:
            raise Exception("Compte introuvable")
        self.session.delete(compte)
        self.session.commit()

    def export_comptes_pdf(self, data, file_path):
        """Export PDF du plan comptable avec charte graphique uniforme"""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import Table, TableStyle
        import datetime
        import os

        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Récupérer les informations de l'entreprise dynamiquement
        try:
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            entreprise_controller = EntrepriseController()
            entreprise_id = getattr(self, 'entreprise_id', 1)
            entreprise_info = entreprise_controller.get_current_enterprise(entreprise_id)
        except Exception as e:
            print(f"Erreur lors de la récupération des infos entreprise: {e}")
            # Fallback vers les valeurs par défaut
            entreprise_info = {
                'name': 'AYANNA ERP',
                'address': '123 Avenue de la République',
                'phone': '+243 123 456 789',
                'email': 'contact@ayanna-erp.com',
                'rccm': 'CD/KIN/RCCM/23-B-1234'
            }

        # En-tête
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawCentredString(width/2, height-1.2*cm, f"Généré par {entreprise_info['name']} - {now}")
        c.setFillColorRGB(0, 0, 0)

        # Logo + infos entreprise
        logo_path = os.path.join(os.path.dirname(__file__), "../../images/favicon.ico")
        # Gestion du logo depuis la base de données
        if entreprise_info.get('logo'):
            try:
                logo_path = os.path.join(os.path.dirname(__file__), f"../../images/logo_{entreprise_id}.png")
                with open(logo_path, "wb") as f:
                    f.write(entreprise_info['logo'])
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du logo: {e}")
        
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 1*cm, height-2.5*cm, width=1.5*cm, height=1.5*cm, mask='auto')
        c.setFont("Helvetica-Bold", 12)
        c.drawString(3*cm, height-2*cm, entreprise_info['name'])
        c.setFont("Helvetica", 9)
        c.drawString(3*cm, height-2.6*cm, entreprise_info['address'])
        c.drawString(3*cm, height-3.2*cm, f"Tél: {entreprise_info['phone']}")
        c.drawString(3*cm, height-3.8*cm, f"Email: {entreprise_info['email']}")
        c.drawString(3*cm, height-4.4*cm, f"RCCM: {entreprise_info['rccm']}")

        # Titre centré
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(width/2, height-5.5*cm, "PLAN COMPTABLE")

        # Table
        table_data = [["Numéro", "Libellé", "Classe"]]
        for row in data:
            table_data.append([
                row["numero"],
                row["nom"],
                row["classe"],
            ])
        table = Table(table_data, colWidths=[3*cm, 8*cm, 4*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("ALIGN", (2,1), (-1,-1), "LEFT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        table.wrapOn(c, width-2*cm, height)
        table_height = table._height
        table.drawOn(c, 1*cm, height-6.5*cm-table_height)

        c.showPage()
        c.save()

    # Classes Comptables
    def get_classes(self, entreprise_id):
        """Retourne toutes les classes comptables"""
        # Import remplacé par les nouveaux modèles
        classes = self.session.query(ClasseComptable).filter(ClasseComptable.enterprise_id == entreprise_id).all()
        if not classes:
            # Création automatique des classes OHADA (1 à 8) + classe spéciale 44 pour les taxes
            ohada_classes = [
                {"code": "1", "nom": "COMPTES DE RESSOURCES DURABLES", "document": "bilan", "type": "passif", "libelle": "Comptes de ressources durables"},
                {"code": "2", "nom": "COMPTES D'ACTIF IMMOBILISE", "document": "bilan", "type": "actif", "libelle": "Comptes d'actif immobilisé"},
                {"code": "3", "nom": "COMPTES DE STOCKS", "document": "bilan", "type": "actif", "libelle": "Comptes de stocks"},
                {"code": "4", "nom": "COMPTES DE TIERS", "document": "bilan", "type": "mixte", "libelle": "Comptes de tiers"},
                {"code": "5", "nom": "COMPTES DE TRESORERIE", "document": "bilan", "type": "actif", "libelle": "Comptes de trésorerie"},
                {"code": "6", "nom": "COMPTES DE CHARGES", "document": "resultat", "type": "charge", "libelle": "Comptes de charges"},
                {"code": "7", "nom": "COMPTES DE PRODUITS", "document": "resultat", "type": "produit", "libelle": "Comptes de produits"},
                {"code": "8", "nom": "COMPTES DES AUTRES CHARGES ET DES AUTRES PRODUITS", "document": "resultat", "type": "mixte", "libelle": "Autres charges et produits"},
                {"code": "44", "nom": "ÉTAT ET AUTRES COLLECTIVITÉS PUBLIQUES", "document": "bilan", "type": "mixte", "libelle": "État et autres collectivités publiques - Taxes et impôts"}
            ]
            for cl in ohada_classes:
                new_classe = ClasseComptable(
                    code=cl["code"],
                    nom=cl["nom"],
                    document=cl["document"],
                    type=cl["type"],
                    libelle=cl["libelle"],
                    enterprise_id=entreprise_id,  # Correction: enterprise_id au lieu d'entreprise_id
                    actif=1
                )
                self.session.add(new_classe)
            self.session.commit()
            classes = self.session.query(ClasseComptable).filter(ClasseComptable.enterprise_id == entreprise_id).all()
        result = []
        for c in classes:
            result.append({
                "numero": c.code,
                "nom": c.nom,
                "libelle": c.libelle,
                "id": c.id
            })
        return result

    def export_classes_pdf(self, data, file_path):
        """Export PDF des classes avec charte graphique uniforme"""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import Table, TableStyle
        import datetime
        import os

        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Récupérer les informations de l'entreprise dynamiquement
        try:
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            entreprise_controller = EntrepriseController()
            entreprise_id = getattr(self, 'entreprise_id', 1)
            entreprise_info = entreprise_controller.get_current_enterprise(entreprise_id)
        except Exception as e:
            print(f"Erreur lors de la récupération des infos entreprise: {e}")
            # Fallback vers les valeurs par défaut
            entreprise_info = {
                'name': 'AYANNA ERP',
                'address': '123 Avenue de la République',
                'phone': '+243 123 456 789',
                'email': 'contact@ayanna-erp.com',
                'rccm': 'CD/KIN/RCCM/23-B-1234'
            }

        # En-tête
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawCentredString(width/2, height-1.2*cm, f"Généré par {entreprise_info['name']} - {now}")
        c.setFillColorRGB(0, 0, 0)

        # Logo + infos entreprise
        logo_path = os.path.join(os.path.dirname(__file__), "../../images/favicon.ico")
        # Gestion du logo depuis la base de données
        if entreprise_info.get('logo'):
            try:
                logo_path = os.path.join(os.path.dirname(__file__), f"../../images/logo_{entreprise_id}.png")
                with open(logo_path, "wb") as f:
                    f.write(entreprise_info['logo'])
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du logo: {e}")
        
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 1*cm, height-2.5*cm, width=1.5*cm, height=1.5*cm, mask='auto')
        c.setFont("Helvetica-Bold", 12)
        c.drawString(3*cm, height-2*cm, entreprise_info['name'])
        c.setFont("Helvetica", 9)
        c.drawString(3*cm, height-2.6*cm, entreprise_info['address'])
        c.drawString(3*cm, height-3.2*cm, f"Tél: {entreprise_info['phone']}")
        c.drawString(3*cm, height-3.8*cm, f"Email: {entreprise_info['email']}")
        c.drawString(3*cm, height-4.4*cm, f"RCCM: {entreprise_info['rccm']}")

        # Titre centré
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(width/2, height-5.5*cm, "CLASSES COMPTABLES")

        # Table
        table_data = [["Numéro", "Libellé"]]
        for row in data:
            table_data.append([
                row["numero"],
                row["nom"],
            ])
        table = Table(table_data, colWidths=[4*cm, 10*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("ALIGN", (0,1), (-1,-1), "LEFT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        table.wrapOn(c, width-2*cm, height)
        table_height = table._height
        table.drawOn(c, 1*cm, height-6.5*cm-table_height)

        c.showPage()
        c.save()




