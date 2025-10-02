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
from ayanna_erp.database.database_manager import DatabaseManager, Entreprise, User


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
            from ayanna_erp.core.session_manager import SessionManager
            session_enterprise_id = SessionManager.get_current_enterprise_id()
            enterprise_id = session_enterprise_id if session_enterprise_id else self._active_enterprise_id
            
        enterprise = self.get_current_enterprise(enterprise_id)
        
        # Extraire la ville de l'adresse si possible
        address = enterprise['address']
        city = ''
        if address:
            # Essayer de détecter la ville dans l'adresse (souvent après une virgule ou un tiret)
            parts = address.split(',')
            if len(parts) >= 2:
                city = parts[-1].strip()
            else:
                # Essayer avec un tiret
                parts = address.split('-')
                if len(parts) >= 2:
                    city = parts[-1].strip()
                else:
                    # Sinon, utiliser une valeur par défaut basée sur l'entreprise
                    city = 'Kinshasa, RDC'
        else:
            city = 'Kinshasa, RDC'
        
        # Gérer le logo (BLOB vers fichier temporaire)
        logo_path = 'assets/logo.png'  # Fallback par défaut
        
        # Vérifier s'il y a un logo BLOB dans l'entreprise
        if 'logo' in enterprise and enterprise['logo']:
            try:
                import os
                import tempfile
                
                # Créer un fichier temporaire pour le logo
                temp_dir = tempfile.gettempdir()
                logo_filename = f"logo_enterprise_{enterprise_id}.png"
                temp_logo_path = os.path.join(temp_dir, logo_filename)
                
                # Écrire le BLOB dans le fichier temporaire
                with open(temp_logo_path, 'wb') as f:
                    f.write(enterprise['logo'])
                
                logo_path = temp_logo_path
                print(f"✅ Logo temporaire créé: {temp_logo_path}")
                
            except Exception as e:
                print(f"⚠️ Erreur lors de la création du logo temporaire: {e}")
                # Garder le logo par défaut en cas d'erreur
        
        # Sinon, vérifier si l'ancien système utilise 'logo_path'
        elif 'logo_path' in enterprise and enterprise['logo_path']:
            logo_path = enterprise['logo_path']
        
        return {
            'name': enterprise['name'],
            'address': enterprise['address'],
            'city': city,
            'phone': enterprise['phone'],
            'email': enterprise['email'],
            'rccm': enterprise['rccm'],
            'logo_path': logo_path
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
        Créer une nouvelle entreprise avec utilisateur administrateur
        
        Args:
            data (dict): Données de l'entreprise
            
        Returns:
            dict: Informations de l'entreprise créée ou None
        """
        try:
            session = self.get_session()
            
            # Créer l'entreprise
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
            session.flush()  # Pour obtenir l'ID sans commiter
            
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
            
            print(f"🔄 Entreprise '{enterprise_name}' créée avec ID: {enterprise_id}")
            
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
                
                # Cacher les valeurs nécessaires avant le commit
                admin_user_id = admin_user.id
                admin_user_email = admin_user.email
                
                print(f"✅ Utilisateur admin créé avec succès:")
                print(f"   - ID: {admin_user_id}")
                print(f"   - Email: {admin_user_email}")
                print(f"   - Entreprise: {enterprise_name} (ID: {enterprise_id})")
                
            except Exception as user_error:
                print(f"❌ Erreur lors de la création de l'utilisateur admin: {user_error}")
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
                'logo_path': enterprise_logo,
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
    
    def refresh_cache(self):
        """Rafraîchir le cache de l'entreprise courante"""
        self._current_enterprise = None

    def get_connected_enterprise_id(self):
        """
        Retourne l'ID de l'entreprise connectée (en session)
        Returns:
            int: ID de l'entreprise connectée
        Raises:
            Exception: Si la récupération échoue
        """
        from ayanna_erp.core.session_manager import SessionManager
        enterprise_id = SessionManager.get_current_enterprise_id()
        if enterprise_id:
            return enterprise_id
        raise Exception("Impossible de récupérer l'ID de l'entreprise connectée")

    def get_connected_user_id(self):
        """
        Retourne l'ID de l'utilisateur connecté (en session)
        Returns:
            int: ID de l'utilisateur connecté
        Raises:
            Exception: Si la récupération échoue
        """
        from ayanna_erp.core.session_manager import SessionManager
        user = SessionManager.get_current_user()
        if user and hasattr(user, 'id'):
            return user.id
        raise Exception("Impossible de récupérer l'ID de l'utilisateur connecté")
