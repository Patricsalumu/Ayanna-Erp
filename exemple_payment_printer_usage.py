"""
Exemple d'utilisation du PaymentPrintManager avec enterprise_id
"""

from ayanna_erp.modules.salle_fete.utils.payment_printer import PaymentPrintManager

# =============================================
# EXEMPLE 1: Création avec enterprise_id spécifique
# =============================================

# Pour une entreprise spécifique (recommandé)
printer = PaymentPrintManager(enterprise_id=1)

# Maintenant toutes les informations d'entreprise utilisées 
# dans l'impression viennent de l'entreprise ID 1 :
# - Nom, adresse, téléphone, email, RCCM
# - Logo de l'entreprise
# - Devise et symbole de devise
# - Formatage des montants

# =============================================
# EXEMPLE 2: Utilisation dans le module salle_fete
# =============================================

class PaiementIndex:
    def __init__(self, main_controller, current_user):
        # Récupérer l'enterprise_id de l'utilisateur connecté
        enterprise_id = getattr(current_user, 'enterprise_id', None) if current_user else None
        
        # Créer le printer avec l'entreprise de l'utilisateur
        self.payment_printer = PaymentPrintManager(enterprise_id=enterprise_id)
        
        # Maintenant tous les documents imprimés utiliseront 
        # automatiquement les informations de l'entreprise
        # de l'utilisateur connecté

# =============================================
# EXEMPLE 3: Changer d'entreprise dynamiquement
# =============================================

# Créer avec une entreprise
printer = PaymentPrintManager(enterprise_id=1)

# Plus tard, changer vers une autre entreprise
printer.set_enterprise(2)

# Maintenant le printer utilise l'entreprise ID 2
# pour tous les documents suivants

# =============================================
# EXEMPLE 4: Vérification de l'entreprise active
# =============================================

printer = PaymentPrintManager(enterprise_id=3)
current_enterprise = printer.get_current_enterprise_id()
print(f"Printer configuré pour l'entreprise: {current_enterprise}")

# =============================================
# AVANTAGES DE CETTE APPROCHE:
# =============================================
"""
✅ CONTRÔLE PRÉCIS: Vous spécifiez exactement quelle entreprise utiliser
✅ MULTI-ENTREPRISES: Chaque instance peut travailler avec une entreprise différente  
✅ FLEXIBILITÉ: Possibilité de changer d'entreprise après création
✅ SÉCURITÉ: Évite les confusions entre entreprises
✅ COMPATIBILITÉ: Fonctionne avec l'ancien code (sans enterprise_id = utilise l'active)

AVANT (problématique):
  printer = PaymentPrintManager()  # Utilise toujours l'entreprise active
  
APRÈS (solution):
  printer = PaymentPrintManager(enterprise_id=user.enterprise_id)  # Précis et contrôlé
"""