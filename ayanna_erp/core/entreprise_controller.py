"""
Contrôleur pour la gestion des entreprises
Fournit les fonctions CRUD et les informations d'entreprise pour toute l'application
"""

import sys
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from PyQt6.QtCore import QObject, pyqtSignal

# Import du gestionnaire de base de données et des modèles
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ayanna_erp.database.database_manager import DatabaseManager, Entreprise


class EntrepriseController(QObject):
    """Contrôleur pour la gestion des entreprises"""
    
    # Signaux pour la communication avec l'interface
    enterprise_updated = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self._current_enterprise = None
        
    def get_session(self):
        """Créer une nouvelle session de base de données"""
        return self.db_manager.get_session()
    
    def get_current_enterprise(self, enterprise_id=1):
        """
        Récupérer l'entreprise courante
        
        Args:
            enterprise_id (int): ID de l'entreprise (par défaut 1)
            
        Returns:
            dict: Informations de l'entreprise
        """
        try:
            if self._current_enterprise is None:
                session = self.get_session()
                enterprise = session.query(Entreprise).filter(Entreprise.id == enterprise_id).first()
                session.close()
                
                if enterprise:
                    self._current_enterprise = {
                        'id': enterprise.id,
                        'name': enterprise.name or 'AYANNA ERP',
                        'address': enterprise.address or '123 Avenue de la République',
                        'phone': enterprise.phone or '+243 123 456 789',
                        'email': enterprise.email or 'contact@ayanna-erp.com',
                        'rccm': enterprise.rccm or 'CD/KIN/RCCM/23-B-1234',
                        'id_nat': enterprise.id_nat or '',
                        'logo_path': enterprise.logo or 'assets/logo.png',
                        'slogan': enterprise.slogan or '',
                        'currency': enterprise.currency or 'USD',
                        'created_at': enterprise.created_at
                    }
                else:
                    # Créer une entreprise par défaut si aucune n'existe
                    self._current_enterprise = self.create_default_enterprise()
                    
            return self._current_enterprise
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la récupération de l'entreprise: {str(e)}")
            return self.get_default_enterprise_info()
    
    def get_default_enterprise_info(self):
        """Retourner les informations par défaut de l'entreprise"""
        return {
            'id': 1,
            'name': 'AYANNA ERP',
            'address': '123 Avenue de la République',
            'phone': '+243 123 456 789',
            'email': 'contact@ayanna-erp.com',
            'rccm': 'CD/KIN/RCCM/23-B-1234',
            'id_nat': '',
            'logo_path': 'assets/logo.png',
            'slogan': '',
            'currency': 'USD',
            'created_at': None
        }
    
    def create_default_enterprise(self):
        """Créer une entreprise par défaut dans la BDD"""
        try:
            session = self.get_session()
            
            default_info = self.get_default_enterprise_info()
            enterprise = Entreprise(
                name=default_info['name'],
                address=default_info['address'],
                phone=default_info['phone'],
                email=default_info['email'],
                rccm=default_info['rccm'],
                id_nat=default_info['id_nat'],
                logo=default_info['logo_path'],
                slogan=default_info['slogan'],
                currency=default_info['currency']
            )
            
            session.add(enterprise)
            session.commit()
            
            # Récupérer l'ID généré
            default_info['id'] = enterprise.id
            default_info['created_at'] = enterprise.created_at
            
            session.close()
            return default_info
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la création de l'entreprise par défaut: {str(e)}")
            return self.get_default_enterprise_info()
    
    def update_enterprise(self, enterprise_id, data):
        """
        Mettre à jour les informations de l'entreprise
        
        Args:
            enterprise_id (int): ID de l'entreprise
            data (dict): Données à mettre à jour
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            session = self.get_session()
            enterprise = session.query(Entreprise).filter(Entreprise.id == enterprise_id).first()
            
            if not enterprise:
                self.error_occurred.emit("Entreprise non trouvée")
                session.close()
                return False
            
            # Mettre à jour les champs fournis
            for key, value in data.items():
                if hasattr(enterprise, key):
                    setattr(enterprise, key, value)
            
            session.commit()
            session.close()
            
            # Invalider le cache
            self._current_enterprise = None
            
            self.enterprise_updated.emit(self.get_current_enterprise(enterprise_id))
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la mise à jour de l'entreprise: {str(e)}")
            return False
    
    def get_company_info_for_pdf(self, enterprise_id=1):
        """
        Récupérer les informations de l'entreprise formatées pour les PDF
        
        Args:
            enterprise_id (int): ID de l'entreprise
            
        Returns:
            dict: Informations formatées pour PDF
        """
        enterprise = self.get_current_enterprise(enterprise_id)
        
        return {
            'name': enterprise['name'],
            'address': enterprise['address'],
            'city': '',  # Peut être extrait de l'adresse si nécessaire
            'phone': enterprise['phone'],
            'email': enterprise['email'],
            'rccm': enterprise['rccm'],
            'logo_path': enterprise['logo_path']
        }
    
    def get_currency(self, enterprise_id=1):
        """
        Récupérer la devise de l'entreprise
        
        Args:
            enterprise_id (int): ID de l'entreprise
            
        Returns:
            str: Code de la devise (USD, EUR, CDF, etc.)
        """
        enterprise = self.get_current_enterprise(enterprise_id)
        return enterprise.get('currency', 'USD')
    
    def get_currency_symbol(self, enterprise_id=1):
        """
        Récupérer le symbole de la devise
        
        Args:
            enterprise_id (int): ID de l'entreprise
            
        Returns:
            str: Symbole de la devise
        """
        currency = self.get_currency(enterprise_id)
        
        # Mapping des devises vers leurs symboles
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'CDF': 'FC',
            'CAD': 'C$',
            'GBP': '£',
            'JPY': '¥',
            'CHF': 'CHF',
            'CNY': '¥',
            'RUB': '₽',
            'ZAR': 'R'
        }
        
        return currency_symbols.get(currency, currency)
    
    def format_amount(self, amount, enterprise_id=1, show_symbol=True):
        """
        Formater un montant avec la devise de l'entreprise
        
        Args:
            amount (float): Montant à formater
            enterprise_id (int): ID de l'entreprise
            show_symbol (bool): Afficher le symbole de devise
            
        Returns:
            str: Montant formaté
        """
        try:
            if show_symbol:
                symbol = self.get_currency_symbol(enterprise_id)
                return f"{amount:.2f} {symbol}"
            else:
                return f"{amount:.2f}"
        except:
            return f"{amount:.2f} €"  # Fallback
    
    def get_all_enterprises(self):
        """
        Récupérer toutes les entreprises
        
        Returns:
            list: Liste des entreprises
        """
        try:
            session = self.get_session()
            enterprises = session.query(Entreprise).order_by(desc(Entreprise.created_at)).all()
            session.close()
            
            result = []
            for enterprise in enterprises:
                result.append({
                    'id': enterprise.id,
                    'name': enterprise.name,
                    'address': enterprise.address,
                    'phone': enterprise.phone,
                    'email': enterprise.email,
                    'rccm': enterprise.rccm,
                    'currency': enterprise.currency,
                    'created_at': enterprise.created_at
                })
            
            return result
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la récupération des entreprises: {str(e)}")
            return []
    
    def create_enterprise(self, data):
        """
        Créer une nouvelle entreprise
        
        Args:
            data (dict): Données de l'entreprise
            
        Returns:
            dict: Informations de l'entreprise créée ou None
        """
        try:
            session = self.get_session()
            
            enterprise = Entreprise(
                name=data.get('name', ''),
                address=data.get('address', ''),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                rccm=data.get('rccm', ''),
                id_nat=data.get('id_nat', ''),
                logo=data.get('logo_path', ''),
                slogan=data.get('slogan', ''),
                currency=data.get('currency', 'USD')
            )
            
            session.add(enterprise)
            session.commit()
            
            result = {
                'id': enterprise.id,
                'name': enterprise.name,
                'address': enterprise.address,
                'phone': enterprise.phone,
                'email': enterprise.email,
                'rccm': enterprise.rccm,
                'id_nat': enterprise.id_nat,
                'logo_path': enterprise.logo,
                'slogan': enterprise.slogan,
                'currency': enterprise.currency,
                'created_at': enterprise.created_at
            }
            
            session.close()
            return result
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la création de l'entreprise: {str(e)}")
            return None
    
    def delete_enterprise(self, enterprise_id):
        """
        Supprimer une entreprise
        
        Args:
            enterprise_id (int): ID de l'entreprise
            
        Returns:
            bool: True si la suppression a réussi
        """
        try:
            if enterprise_id == 1:
                self.error_occurred.emit("Impossible de supprimer l'entreprise principale")
                return False
            
            session = self.get_session()
            enterprise = session.query(Entreprise).filter(Entreprise.id == enterprise_id).first()
            
            if not enterprise:
                self.error_occurred.emit("Entreprise non trouvée")
                session.close()
                return False
            
            session.delete(enterprise)
            session.commit()
            session.close()
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la suppression de l'entreprise: {str(e)}")
            return False
    
    def refresh_cache(self):
        """Rafraîchir le cache de l'entreprise courante"""
        self._current_enterprise = None
