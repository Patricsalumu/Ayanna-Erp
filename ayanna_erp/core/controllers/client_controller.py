from sqlalchemy.orm import Session
from ayanna_erp.modules.boutique.model import ShopClient


class ClientController:

    def __init__(self, session: Session):
        self.session = session

    def get_infosclient(self, client_id: int):
        """
        Retourne les infos essentielles du client
        (nom complet + téléphone) pour WhatsApp et affichage
        """
        if not client_id:
            return None

        try:
            client = (
                self.session
                .query(ShopClient)
                .filter(
                    ShopClient.id == client_id,
                    ShopClient.is_active == True
                )
                .first()
            )

            if not client:
                return None

            nom_complet = client.nom
            if client.prenom:
                nom_complet = f"{client.nom} {client.prenom}"

            return {
                "id": client.id,
                "nom": nom_complet.strip(),
                "telephone": client.telephone
            }

        except Exception as e:
            print(f"Erreur get_infosclient({client_id}) :", e)
            return None
