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
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.database.database_manager import DatabaseManager, Entreprise, User
from ayanna_erp.core.utils.image_utils import ImageUtils
from ayanna_erp.core.session_manager import SessionManager


class EntrepriseController(QObject):
    """Contrôleur pour la gestion des entreprises"""
    
    # Signaux pour la communication avec l'interface
    enterprise_updated = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self._enterprise_cache = {}  # Cache pour plusieurs entreprises {enterprise_id: enterprise_data}
        self._active_enterprise_id = 1  # ID de l'entreprise active par défaut
        
    def get_session(self):
        """Créer une nouvelle session de base de données"""
        return self.db_manager.get_session()
    
    def set_active_enterprise(self, enterprise_id):
        """
        Définir l'entreprise active
        
        Args:
            enterprise_id (int): ID de l'entreprise à activer
            
        Returns:
            bool: True si l'entreprise a été activée avec succès
        """
        try:
            # Vérifier que l'entreprise existe
            enterprise = self.get_current_enterprise(enterprise_id)
            if enterprise:
                self._active_enterprise_id = enterprise_id
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de l'activation de l'entreprise: {str(e)}")
            return False
    
    def get_active_enterprise_id(self):
        """
        Récupérer l'ID de l'entreprise active
        
        Returns:
            int: ID de l'entreprise active
        """
        return self._active_enterprise_id
    
    def get_active_enterprise(self):
        """
        Récupérer les informations de l'entreprise active
        
        Returns:
            dict: Informations de l'entreprise active
        """
        return self.get_current_enterprise()
    
    def get_current_enterprise(self, enterprise_id=None):
        """
        Récupérer l'entreprise courante
        
        Args:
            enterprise_id (int, optional): ID de l'entreprise. Si None, utilise l'entreprise de l'utilisateur en session
            
        Returns:
            dict: Informations de l'entreprise
        """
        try:
            # Si aucun ID n'est fourni, utiliser l'entreprise de l'utilisateur en session
            if enterprise_id is None:
                session_enterprise_id = SessionManager.get_current_enterprise_id()
                enterprise_id = session_enterprise_id if session_enterprise_id else self._active_enterprise_id
            
            # Vérifier si l'entreprise est déjà en cache
            if enterprise_id not in self._enterprise_cache:
                session = self.get_session()
                enterprise = session.query(Entreprise).filter(Entreprise.id == enterprise_id).first()
                session.close()
                
                if enterprise:
                    self._enterprise_cache[enterprise_id] = {
                        'id': enterprise.id,
                        'name': enterprise.name or 'AYANNA ERP',
                        'address': enterprise.address or '123 Avenue de la République',
                        'phone': enterprise.phone or '+243 123 456 789',
                        'email': enterprise.email or 'contact@ayanna-erp.com',
                        'rccm': enterprise.rccm or 'CD/KIN/RCCM/23-B-1234',
                        'id_nat': enterprise.id_nat or '',
                        'logo': enterprise.logo,  # BLOB data
                        'slogan': enterprise.slogan or '',
                        'currency': enterprise.currency or 'USD',
                        'created_at': enterprise.created_at
                    }
                else:
                    # Créer une entreprise par défaut si aucune n'existe
                    if enterprise_id == 1:
                        self._enterprise_cache[enterprise_id] = self.create_default_enterprise()
                    else:
                        # Pour les autres IDs, retourner les infos par défaut sans créer
                        return self.get_default_enterprise_info()
                    
            return self._enterprise_cache[enterprise_id]
            
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
            'logo': None,  # Pas de logo par défaut
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
                logo=default_info['logo'],  # BLOB au lieu de logo_path
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
            
            # Invalider le cache pour cette entreprise spécifique
            if enterprise_id in self._enterprise_cache:
                del self._enterprise_cache[enterprise_id]
            
            self.enterprise_updated.emit(self.get_current_enterprise(enterprise_id))
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la mise à jour de l'entreprise: {str(e)}")
            return False
    
    def get_company_info_for_pdf(self, enterprise_id=None):
        """
        Récupérer les informations de l'entreprise formatées pour les PDF
        
        Args:
            enterprise_id (int, optional): ID de l'entreprise. Si None, utilise l'entreprise de l'utilisateur en session
            
        Returns:
            dict: Informations formatées pour PDF
        """
        # Si aucun ID n'est fourni, utiliser l'entreprise de l'utilisateur en session
        if enterprise_id is None:
            session_enterprise_id = SessionManager.get_current_enterprise_id()
            enterprise_id = session_enterprise_id if session_enterprise_id else self._active_enterprise_id
            
        enterprise = self.get_current_enterprise(enterprise_id)
        
        return {
            'name': enterprise['name'],
            'address': enterprise['address'],
            'city': '',  # Peut être extrait de l'adresse si nécessaire
            'phone': enterprise['phone'],
            'email': enterprise['email'],
            'rccm': enterprise['rccm'],
            'logo': enterprise['logo']  # BLOB data au lieu de logo_path
        }
    
    def get_currency(self, enterprise_id=None):
        """
        Récupérer la devise de l'entreprise
        
        Args:
            enterprise_id (int, optional): ID de l'entreprise. Si None, utilise l'entreprise de l'utilisateur en session
            
        Returns:
            str: Code de la devise (USD, EUR, CDF, etc.)
        """
        # Si aucun ID n'est fourni, utiliser l'entreprise de l'utilisateur en session
        if enterprise_id is None:
            session_enterprise_id = SessionManager.get_current_enterprise_id()
            enterprise_id = session_enterprise_id if session_enterprise_id else self._active_enterprise_id
            
        enterprise = self.get_current_enterprise(enterprise_id)
        return enterprise.get('currency', 'USD')
    
    def get_currency_symbol(self, enterprise_id=None):
        """
        Récupérer le symbole de la devise
        
        Args:
            enterprise_id (int, optional): ID de l'entreprise. Si None, utilise l'entreprise de l'utilisateur en session
            
        Returns:
            str: Symbole de la devise
        """
        # Si aucun ID n'est fourni, utiliser l'entreprise de l'utilisateur en session
        if enterprise_id is None:
            session_enterprise_id = SessionManager.get_current_enterprise_id()
            enterprise_id = session_enterprise_id if session_enterprise_id else self._active_enterprise_id
            
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
    
    def format_amount(self, amount, enterprise_id=None, show_symbol=True):
        """
        Formater un montant avec la devise de l'entreprise
        
        Args:
            amount (float): Montant à formater
            enterprise_id (int, optional): ID de l'entreprise. Si None, utilise l'entreprise de l'utilisateur en session
            show_symbol (bool): Afficher le symbole de devise
            
        Returns:
            str: Montant formaté
        """
        try:
            # Si aucun ID n'est fourni, utiliser l'entreprise de l'utilisateur en session
            if enterprise_id is None:
                session_enterprise_id = SessionManager.get_current_enterprise_id()
                enterprise_id = session_enterprise_id if session_enterprise_id else self._active_enterprise_id

            # Convertir en float puis arrondir à 2 décimales
            val = float(amount or 0)
            rounded = round(val, 2)

            # Si montant entier après arrondi, afficher sans décimales
            if rounded.is_integer():
                int_val = int(rounded)
                # formatage avec séparateur espace tous les 3 chiffres
                formatted = f"{int_val:,}".replace(",", " ")
            else:
                # Afficher avec 2 décimales, mais utiliser espace comme séparateur de milliers
                formatted = f"{rounded:,.2f}".replace(",", " ")

            if show_symbol:
                symbol = self.get_currency_symbol(enterprise_id)
                return f"{formatted} {symbol}"
            return formatted
        except Exception:
            try:
                return f"{int(round(float(amount or 0))):,}".replace(",", " ") + f" {self.get_currency_symbol()}"
            except Exception:
                return str(amount)
    
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
                logo=data.get('logo'),  # BLOB au lieu de logo_path
                slogan=data.get('slogan', ''),
                currency=data.get('currency', 'USD')
            )
            
            session.add(enterprise)
            session.flush()  # Pour obtenir l'ID sans commiter encore
            
            # Capturer TOUTES les valeurs nécessaires juste après le flush
            enterprise_id = enterprise.id
            enterprise_name = enterprise.name
            enterprise_address = enterprise.address
            enterprise_phone = enterprise.phone
            enterprise_email = enterprise.email
            enterprise_rccm = enterprise.rccm
            enterprise_id_nat = enterprise.id_nat
            enterprise_logo = enterprise.logo
            enterprise_slogan = enterprise.slogan
            enterprise_currency = enterprise.currency
            enterprise_created_at = enterprise.created_at
            
            print(f"🔄 Entreprise '{enterprise_name}' ajoutée avec ID: {enterprise_id}")
            
            # Créer automatiquement les POS pour tous les modules
            pos_created = self.db_manager.create_pos_for_new_enterprise(enterprise_id)
            if not pos_created:
                print("⚠️ Erreur lors de la création des POS pour l'entreprise")
                session.rollback()
                raise Exception("Erreur lors de la création des POS")
            else:
                print(f"✅ POS créés automatiquement pour l'entreprise {enterprise_name}")
            
            # Créer automatiquement un utilisateur admin associé à cette entreprise
            try:
                print(f"🔄 Création de l'utilisateur admin pour l'entreprise {enterprise_name}...")
                
                # Générer un email unique pour l'admin
                admin_email = data.get('email', 'admin@' + data.get('name', 'entreprise').lower().replace(' ', '') + '.com')
                
                # Vérifier si l'email existe déjà
                existing_user = session.query(User).filter(User.email == admin_email).first()
                if existing_user:
                    print(f"⚠️ Utilisateur avec email {admin_email} existe déjà, génération d'un email unique...")
                    admin_email = f"admin_{enterprise_id}@{data.get('name', 'entreprise').lower().replace(' ', '')}.local"
                
                admin_user = User(
                    name='Administrateur Système',
                    email=admin_email,
                    role='admin',
                    enterprise_id=enterprise_id
                )
                
                # Utiliser la méthode set_password du modèle
                admin_user.set_password('admin123')
                
                session.add(admin_user)
                session.flush()  # Pour obtenir l'ID sans commiter
                
                # Capturer les valeurs de l'utilisateur avant de continuer
                admin_user_id = admin_user.id
                admin_user_email = admin_user.email
                
                print(f"✅ Utilisateur admin créé avec succès:")
                print(f"   - ID: {admin_user_id}")
                print(f"   - Email: {admin_user_email}")
                print(f"   - Entreprise: {enterprise_name} (ID: {enterprise_id})")
                
            except Exception as user_error:
                print(f"❌ Erreur lors de la création de l'utilisateur admin: {user_error}")
                # Rollback et relancer l'exception pour être capturée par le bloc principal
                session.rollback()
                raise Exception(f"Erreur création utilisateur: {str(user_error)}")
            
            # Commiter toute la transaction (entreprise + POS + utilisateur)
            session.commit()
            
            result = {
                'id': enterprise_id,
                'name': enterprise_name,
                'address': enterprise_address,
                'phone': enterprise_phone,
                'email': enterprise_email,
                'rccm': enterprise_rccm,
                'id_nat': enterprise_id_nat,
                'logo': enterprise_logo,  # BLOB au lieu de logo_path
                'slogan': enterprise_slogan,
                'currency': enterprise_currency,
                'created_at': enterprise_created_at,
                'admin_user_id': admin_user_id,
                'admin_user_email': admin_user_email,
                'admin_credentials': {
                    'name': 'Administrateur Système',
                    'email': admin_user_email,
                    'password': 'admin123'
                },
                'pos_created': pos_created,
                'success': True
            }
            
            print(f"🎉 Entreprise et utilisateur créés avec succès:")
            print(f"   - Entreprise: {enterprise_name} (ID: {enterprise_id})")
            print(f"   - Admin: {admin_user_email} (ID: {admin_user_id})")
            print(f"   - POS créés: {'Oui' if pos_created else 'Non'}")
            
            session.close()
            return result
            
        except Exception as e:
            print(f"❌ ERREUR lors de la création de l'entreprise: {str(e)}")
            print(f"   Type d'erreur: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            
            if 'session' in locals():
                try:
                    session.rollback()
                    print("🔄 Transaction annulée (rollback)")
                except:
                    pass
                finally:
                    session.close()
                    print("🔒 Session fermée")
            
            error_message = f"Erreur lors de la création de l'entreprise: {str(e)}"
            self.error_occurred.emit(error_message)
            return {
                'success': False,
                'error': error_message,
                'details': str(e)
            }

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
    
    def refresh_cache(self, enterprise_id=None):
        """
        Rafraîchir le cache des entreprises
        
        Args:
            enterprise_id (int, optional): ID de l'entreprise à rafraîchir. Si None, vide tout le cache
        """
        if enterprise_id is None:
            # Vider tout le cache
            self._enterprise_cache.clear()
        else:
            # Vider le cache pour une entreprise spécifique
            if enterprise_id in self._enterprise_cache:
                del self._enterprise_cache[enterprise_id]
    
    def update_logo_from_file(self, enterprise_id, logo_file_path):
        """
        Mettre à jour le logo d'une entreprise à partir d'un fichier
        
        Args:
            enterprise_id (int): ID de l'entreprise
            logo_file_path (str): Chemin vers le fichier logo
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            # Valider le fichier image
            if not ImageUtils.validate_image_file(logo_file_path):
                self.error_occurred.emit("Le fichier sélectionné n'est pas une image valide")
                return False
            
            # Convertir le fichier en BLOB avec redimensionnement
            logo_blob = ImageUtils.file_to_blob(logo_file_path)
            if not logo_blob:
                self.error_occurred.emit("Impossible de lire le fichier image")
                return False
            
            # Redimensionner l'image pour optimiser l'espace
            logo_blob = ImageUtils.resize_image_blob(logo_blob, max_width=300, max_height=300)
            
            # Mettre à jour en base de données
            return self.update_enterprise(enterprise_id, {'logo': logo_blob})
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la mise à jour du logo: {str(e)}")
            return False
    
    def get_logo_pixmap(self, enterprise_id=None):
        """
        Récupérer le logo d'une entreprise en tant que QPixmap
        
        Args:
            enterprise_id (int): ID de l'entreprise
            
        Returns:
            QPixmap: Logo de l'entreprise ou None
        """
        try:
            enterprise = self.get_current_enterprise(enterprise_id)
            logo_blob = enterprise.get('logo')
            
            if not logo_blob:
                return None
            
            return ImageUtils.blob_to_pixmap(logo_blob)
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la récupération du logo: {str(e)}")
            return None
    
    def remove_logo(self, enterprise_id):
        """
        Supprimer le logo d'une entreprise
        
        Args:
            enterprise_id (int): ID de l'entreprise
            
        Returns:
            bool: True si la suppression a réussi
        """
        try:
            return self.update_enterprise(enterprise_id, {'logo': None})
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la suppression du logo: {str(e)}")
            return False
    
    def get_logo_info(self, enterprise_id=None):
        """
        Obtenir des informations sur le logo d'une entreprise
        
        Args:
            enterprise_id (int): ID de l'entreprise
            
        Returns:
            dict: Informations sur le logo ou None
        """
        try:
            enterprise = self.get_current_enterprise(enterprise_id)
            logo_blob = enterprise.get('logo')
            
            if not logo_blob:
                return None
            
            return ImageUtils.get_image_info(logo_blob)
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la récupération des informations du logo: {str(e)}")
            return None
    
    def get_enterprise_summary(self):
        """
        Obtenir un résumé du système d'entreprises
        
        Returns:
            dict: Informations sur les entreprises en cache et l'entreprise active
        """
        return {
            'active_enterprise_id': self._active_enterprise_id,
            'cached_enterprises': list(self._enterprise_cache.keys()),
            'cache_count': len(self._enterprise_cache),
            'active_enterprise_name': self.get_active_enterprise().get('name', 'N/A')
        }