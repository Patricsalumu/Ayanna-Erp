from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ayanna_erp.database.base import Base


class ProductBatch(Base):
    __tablename__ = 'product_batches'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('stock_warehouses.id'))
    batch_number = Column(String(100))
    manufacture_date = Column(DateTime)
    expiration_date = Column(DateTime)
    quantity = Column(Numeric(15,3), default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer)

    product = relationship('CoreProduct')
    warehouse = relationship('StockWarehouse')


class FabricationRule(Base):
    __tablename__ = 'fabrication_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)
    output_quantity = Column(Numeric(15,3), default=1.0)
    estimated_duration_minutes = Column(Integer, default=0)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer)

    product = relationship('CoreProduct')
    items = relationship('FabricationRuleItem', back_populates='rule', cascade='all, delete-orphan')


class FabricationRuleItem(Base):
    __tablename__ = 'fabrication_rule_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fabrication_rule_id = Column(Integer, ForeignKey('fabrication_rules.id'), nullable=False)
    raw_material_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)
    quantity_required = Column(Numeric(15,3), default=0.0)
    wastage_percent = Column(Numeric(5,2), default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    rule = relationship('FabricationRule', back_populates='items')
    raw_material = relationship('CoreProduct')


class Production(Base):
    __tablename__ = 'productions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    production_code = Column(String(100), unique=True)
    fabrication_rule_id = Column(Integer, ForeignKey('fabrication_rules.id'))
    product_id = Column(Integer, ForeignKey('core_products.id'))
    warehouse_id = Column(Integer, ForeignKey('stock_warehouses.id'))
    planned_quantity = Column(Numeric(15,3), default=0.0)
    produced_quantity = Column(Numeric(15,3), default=0.0)
    expected_loss_quantity = Column(Numeric(15,3), default=0.0)
    actual_loss_quantity = Column(Numeric(15,3), default=0.0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    estimated_duration_minutes = Column(Integer, default=0)
    actual_duration_minutes = Column(Integer, default=0)
    production_quality = Column(String(50))  # excellent, good, average, poor, failed
    status = Column(String(30), default='draft')  # draft, in_progress, completed, cancelled
    operator_name = Column(String(200))
    notes = Column(Text)
    created_by = Column(Integer)
    validated_by = Column(Integer)
    validated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    rule = relationship('FabricationRule')
    product = relationship('CoreProduct')
    warehouse = relationship('StockWarehouse')
    items = relationship('ProductionItem', back_populates='production', cascade='all, delete-orphan')
    losses = relationship('ProductionLoss', back_populates='production', cascade='all, delete-orphan')


class ProductionItem(Base):
    __tablename__ = 'production_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    production_id = Column(Integer, ForeignKey('productions.id'), nullable=False)
    raw_material_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)
    planned_quantity = Column(Numeric(15,3), default=0.0)
    consumed_quantity = Column(Numeric(15,3), default=0.0)
    variance_quantity = Column(Numeric(15,3), default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    production = relationship('Production', back_populates='items')
    raw_material = relationship('CoreProduct')


class ProductionLoss(Base):
    __tablename__ = 'production_losses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    production_id = Column(Integer, ForeignKey('productions.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('core_products.id'))
    quantity_loss = Column(Numeric(15,3), default=0.0)
    loss_type = Column(String(50))  # normal_loss, abnormal_loss, damaged, wastage, expired
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    production = relationship('Production', back_populates='losses')
    product = relationship('CoreProduct')
