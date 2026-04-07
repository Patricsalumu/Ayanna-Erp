"""
Controller to manage salles and tables (CRUD)
"""
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.restaurant.models.restaurant import RestauSalle, RestauTable
from datetime import datetime
from types import SimpleNamespace


class SalleController:
    def __init__(self, entreprise_id=1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id

    def create_salle(self, name):
        session = self.db.get_session()
        try:
            salle = RestauSalle(entreprise_id=self.entreprise_id, name=name)
            session.add(salle)
            session.commit()
            # rafraîchir et détacher l'objet pour éviter les objets liés à une session fermée
            session.refresh(salle)
            data = {k: v for k, v in salle.__dict__.items() if not k.startswith('_')}
            ns = SimpleNamespace(**data)
            session.expunge(salle)
            return ns
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def create_table(self, salle_id, number, pos_x=0, pos_y=0, width=80, height=80, shape='rectangle'):
        session = self.db.get_session()
        try:
            table = RestauTable(
                salle_id=salle_id,
                number=number,
                pos_x=pos_x,
                pos_y=pos_y,
                width=width,
                height=height,
                shape=shape
            )
            session.add(table)
            session.commit()
            session.refresh(table)
            data = {k: v for k, v in table.__dict__.items() if not k.startswith('_')}
            ns = SimpleNamespace(**data)
            session.expunge(table)
            return ns
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def list_salles(self):
        session = self.db.get_session()
        try:
            rows = session.query(RestauSalle).filter_by(entreprise_id=self.entreprise_id).all()
            result = []
            for r in rows:
                data = {k: v for k, v in r.__dict__.items() if not k.startswith('_')}
                result.append(SimpleNamespace(**data))
            return result
        finally:
            self.db.close_session()

    def list_tables_for_salle(self, salle_id):
        session = self.db.get_session()
        try:
            rows = session.query(RestauTable).filter_by(salle_id=salle_id).all()
            result = []
            for r in rows:
                data = {k: v for k, v in r.__dict__.items() if not k.startswith('_')}
                result.append(SimpleNamespace(**data))
            return result
        finally:
            self.db.close_session()

    def get_table(self, table_id):
        session = self.db.get_session()
        try:
            r = session.query(RestauTable).filter_by(id=table_id).first()
            if not r:
                return None
            data = {k: v for k, v in r.__dict__.items() if not k.startswith('_')}
            return SimpleNamespace(**data)
        finally:
            self.db.close_session()

    def update_table(self, table_id, pos_x=None, pos_y=None, width=None, height=None, number=None, shape=None):
        """Mettre à jour une table existante (position, dimensions, etc.)"""
        session = self.db.get_session()
        try:
            table = session.query(RestauTable).filter_by(id=table_id).first()
            if not table:
                return None
            if pos_x is not None:
                table.pos_x = int(pos_x)
            if pos_y is not None:
                table.pos_y = int(pos_y)
            if width is not None:
                table.width = int(width)
            if height is not None:
                table.height = int(height)
            if number is not None:
                table.number = str(number)
            if shape is not None:
                table.shape = shape
            session.commit()
            session.refresh(table)
            data = {k: v for k, v in table.__dict__.items() if not k.startswith('_')}
            ns = SimpleNamespace(**data)
            session.expunge(table)
            return ns
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def delete_table(self, table_id):
        """Supprimer une table par son ID"""
        session = self.db.get_session()
        try:
            table = session.query(RestauTable).filter_by(id=table_id).first()
            if not table:
                return False
            session.delete(table)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()
