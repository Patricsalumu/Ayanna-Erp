from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from ayanna_erp.database.base import Base


class Licence(Base):
    """Table des licences

    Stocke les licences activées localement.
    """
    # Use plural `licences` to match server schema and new local table
    __tablename__ = 'licences'
    __table_args__ = {'extend_existing': True}

    # Use TEXT primary key to match the actual `licences` table (server uses UUIDs)
    id = Column(String(64), primary_key=True)
    cle = Column(String(255), unique=True, nullable=False)  # stocke le hash
    type = Column(String(50), nullable=False)  # Essai, Mensuel, Annuel
    date_activation = Column(DateTime, nullable=False, default=func.current_timestamp())
    date_expiration = Column(DateTime, nullable=False)
    signature = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    entreprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def is_valid(self):
        from datetime import datetime
        now = datetime.utcnow()
        return bool(self.active and self.date_expiration >= now)
