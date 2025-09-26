"""
Gestionnaire de session utilisateur global pour Ayanna ERP
Permet de maintenir les informations de l'utilisateur connecté dans toute l'application
"""

class SessionManager:
    """Singleton pour gérer la session utilisateur globale"""
    
    _instance = None
    _current_user = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def set_current_user(cls, user):
        """
        Définir l'utilisateur actuellement connecté
        
        Args:
            user: Objet utilisateur avec au minimum les attributs id, name, enterprise_id
        """
        instance = cls()
        instance._current_user = user
        print(f"✅ Session créée pour: {user.name} (Entreprise ID: {getattr(user, 'enterprise_id', 'N/A')})")
    
    @classmethod
    def get_current_user(cls):
        """
        Récupérer l'utilisateur actuellement connecté
        
        Returns:
            Objet utilisateur ou None si pas connecté
        """
        instance = cls()
        return instance._current_user
    
    @classmethod
    def get_current_enterprise_id(cls):
        """
        Récupérer l'enterprise_id de l'utilisateur connecté
        
        Returns:
            int: ID de l'entreprise de l'utilisateur connecté ou None
        """
        instance = cls()
        if instance._current_user:
            return getattr(instance._current_user, 'enterprise_id', None)
        return None
    
    @classmethod
    def is_authenticated(cls):
        """
        Vérifier si un utilisateur est connecté
        
        Returns:
            bool: True si un utilisateur est connecté
        """
        instance = cls()
        return instance._current_user is not None
    
    @classmethod
    def clear_session(cls):
        """Effacer la session (déconnexion)"""
        instance = cls()
        if instance._current_user:
            print(f"✅ Session fermée pour: {instance._current_user.name}")
        instance._current_user = None
    
    @classmethod
    def get_session_info(cls):
        """
        Obtenir un résumé de la session actuelle
        
        Returns:
            dict: Informations sur la session
        """
        instance = cls()
        if instance._current_user:
            return {
                'user_id': getattr(instance._current_user, 'id', None),
                'user_name': getattr(instance._current_user, 'name', 'N/A'),
                'enterprise_id': getattr(instance._current_user, 'enterprise_id', None),
                'role': getattr(instance._current_user, 'role', 'N/A'),
                'email': getattr(instance._current_user, 'email', 'N/A'),
                'is_authenticated': True
            }
        else:
            return {
                'user_id': None,
                'user_name': None,
                'enterprise_id': None,
                'role': None,
                'email': None,
                'is_authenticated': False
            }

# Instance globale accessible partout
session_manager = SessionManager()