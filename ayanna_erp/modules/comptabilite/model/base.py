"""
Modèle de base pour tous les autres modèles
"""
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

from ayanna_erp.database.base import Base

class BaseModel(Base):
    """Modèle de base avec colonnes communes"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_creation = Column(DateTime, default=func.now(), nullable=False)
    date_modification = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if hasattr(value, 'isoformat'):  # DateTime
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
