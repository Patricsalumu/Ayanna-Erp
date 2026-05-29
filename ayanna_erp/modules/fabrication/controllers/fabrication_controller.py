from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import (
    FabricationRule, FabricationRuleItem, Production, ProductionItem, ProductionLoss
)
from ayanna_erp.modules.core.models import CoreProduct
from ayanna_erp.modules.stock.models import StockProduitEntrepot, StockMovement, StockWarehouse
from decimal import Decimal
from datetime import datetime
from typing import List
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaJournaux, ComptaEcritures, ComptaConfig


class FabricationController:
    def __init__(self):
        self.db = DatabaseManager()

    def create_rule(self, session, product_id: int, output_quantity: float, estimated_duration_minutes: int = 0, notes: str = None, created_by: int = None) -> FabricationRule:
        rule = FabricationRule(
            product_id=product_id,
            output_quantity=Decimal(str(output_quantity)),
            estimated_duration_minutes=estimated_duration_minutes,
            notes=notes,
            created_by=created_by
        )
        session.add(rule)
        session.commit()
        return rule

    def add_rule_item(self, session, rule_id: int, raw_material_id: int, quantity_required: float, wastage_percent: float = 0.0) -> FabricationRuleItem:
        item = FabricationRuleItem(
            fabrication_rule_id=rule_id,
            raw_material_id=raw_material_id,
            quantity_required=Decimal(str(quantity_required)),
            wastage_percent=Decimal(str(wastage_percent))
        )
        session.add(item)
        session.commit()
        return item

    def create_production(self, session, fabrication_rule_id: int, planned_quantity: float, warehouse_id: int, operator_name: str = None, created_by: int = None, notes: str = None) -> Production:
        # load rule
        rule = session.query(FabricationRule).filter_by(id=fabrication_rule_id).first()
        if not rule:
            raise Exception("Règle de fabrication introuvable")

        # Ensure sufficient stock - checked on validate, allow draft creation
        prod = Production(
            production_code=f"PROD-{int(datetime.utcnow().timestamp())}",
            fabrication_rule_id=fabrication_rule_id,
            product_id=rule.product_id,
            warehouse_id=warehouse_id,
            planned_quantity=Decimal(str(planned_quantity)),
            produced_quantity=Decimal('0.0'),
            status='draft',
            operator_name=operator_name,
            notes=notes,
            created_by=created_by
        )
        session.add(prod)
        session.commit()
        return prod

    def validate_production(self, session, production_id: int, produced_quantity: float, consumed_quantities: dict, validated_by: int = None):
        """
        Validate a production: consume raw materials, add finished goods, create stock movements
        consumed_quantities: dict raw_material_id -> consumed_quantity (Decimal/float)
        """
        prod = session.query(Production).filter_by(id=production_id).first()
        if not prod:
            raise Exception("Production introuvable")
        if prod.status == 'completed':
            raise Exception("Production déjà validée")

        # Load rule items
        rule = session.query(FabricationRule).filter_by(id=prod.fabrication_rule_id).first()
        items = rule.items if rule else []

        # Check stock availability for each raw material
        for item in items:
            required_per_unit = Decimal(str(item.quantity_required))
            required_total = required_per_unit * Decimal(str(prod.planned_quantity)) / Decimal(str(rule.output_quantity or 1))
            consumed = Decimal(str(consumed_quantities.get(item.raw_material_id, required_total)))

            # get warehouse stock entry
            stock_entry = session.query(StockProduitEntrepot).filter_by(product_id=item.raw_material_id, warehouse_id=prod.warehouse_id).first()
            qty_available = Decimal('0.0')
            if stock_entry:
                qty_available = Decimal(str(stock_entry.quantity))

            if qty_available < consumed:
                raise Exception(f"Stock insuffisant pour le produit {item.raw_material_id}: requis {consumed}, disponible {qty_available}")

        # All checks passed - perform consumption and movements
        # Decrease raw materials
        for item in items:
            required_per_unit = Decimal(str(item.quantity_required))
            required_total = required_per_unit * Decimal(str(prod.planned_quantity)) / Decimal(str(rule.output_quantity or 1))
            consumed = Decimal(str(consumed_quantities.get(item.raw_material_id, required_total)))

            stock_entry = session.query(StockProduitEntrepot).filter_by(product_id=item.raw_material_id, warehouse_id=prod.warehouse_id).first()
            if not stock_entry:
                raise Exception(f"Aucun stock trouvé pour raw material {item.raw_material_id} dans l'entrepôt {prod.warehouse_id}")

            # Subtract quantity
            stock_entry.quantity = Decimal(str(stock_entry.quantity)) - consumed
            stock_entry.last_movement_date = datetime.utcnow()

            # StockMovement sortie
            mv = StockMovement(
                product_id=item.raw_material_id,
                warehouse_id=prod.warehouse_id,
                product_warehouse_id=stock_entry.id,
                movement_type='SORTIE',
                quantity= -abs(consumed),
                unit_cost=stock_entry.unit_cost,
                total_cost= (stock_entry.unit_cost or 0) * float(consumed),
                reference=prod.production_code,
                description=f"Consommation production {prod.production_code}",
                user_id=validated_by,
                user_name=str(validated_by) if validated_by else None,
                movement_date=datetime.utcnow(),
                batch_number=None,
                expiry_date=None
            )
            session.add(mv)

            # Create ProductionItem record
            pitem = ProductionItem(
                production_id=prod.id,
                raw_material_id=item.raw_material_id,
                planned_quantity=required_total,
                consumed_quantity=consumed,
                variance_quantity=consumed - required_total
            )
            session.add(pitem)

        # Add produced finished goods into stock
        # Find or create stock entry for finished product
        from decimal import Decimal as D
        produced_q = Decimal(str(produced_quantity))
        fin_stock = session.query(StockProduitEntrepot).filter_by(product_id=prod.product_id, warehouse_id=prod.warehouse_id).first()
        if not fin_stock:
            # create new stock entry
            fin_stock = StockProduitEntrepot(
                product_id=prod.product_id,
                warehouse_id=prod.warehouse_id,
                quantity=produced_q,
                reserved_quantity=Decimal('0.0'),
                unit_cost=Decimal('0.0'),
                total_cost=Decimal('0.0'),
                min_stock_level=Decimal('0.0'),
                last_movement_date=datetime.utcnow()
            )
            session.add(fin_stock)
        else:
            fin_stock.quantity = Decimal(str(fin_stock.quantity)) + produced_q
            fin_stock.last_movement_date = datetime.utcnow()

        # StockMovement entree pour produit fini
        mv_in = StockMovement(
            product_id=prod.product_id,
            warehouse_id=prod.warehouse_id,
            product_warehouse_id=fin_stock.id,
            movement_type='ENTREE',
            quantity=abs(produced_q),
            unit_cost=fin_stock.unit_cost,
            total_cost=(fin_stock.unit_cost or 0) * float(produced_q),
            reference=prod.production_code,
            description=f"Production validée {prod.production_code}",
            user_id=validated_by,
            user_name=str(validated_by) if validated_by else None,
            movement_date=datetime.utcnow()
        )
        session.add(mv_in)

        # Update production
        prod.produced_quantity = produced_q
        prod.status = 'completed'
        prod.validated_by = validated_by
        prod.validated_at = datetime.utcnow()
        prod.end_time = datetime.utcnow()

        session.commit()

        # Générer écritures comptables
        try:
            # Calculer coût total matières consommées
            total_materials_cost = Decimal('0.0')
            material_costs = []  # tuples (raw_material_id, amount)
            for item in items:
                consumed = Decimal(str(consumed_quantities.get(item.raw_material_id, item.quantity_required)))
                stock_entry = session.query(StockProduitEntrepot).filter_by(product_id=item.raw_material_id, warehouse_id=prod.warehouse_id).first()
                unit_cost = Decimal(str(stock_entry.unit_cost or 0)) if stock_entry else Decimal('0.0')
                amount = unit_cost * consumed
                total_materials_cost += amount
                material_costs.append((item.raw_material_id, amount))

            # Déterminer compte stock produit fini
            compta_ctrl = ComptabiliteController()
            # récupérer la configuration pour l'entrepôt / pos si disponible
            config = session.query(ComptaConfig).filter_by(enterprise_id=prod.created_by if prod.created_by else 1, pos_id=prod.warehouse_id).first()
            # fallback config by enterprise only
            if not config:
                config = session.query(ComptaConfig).filter_by(enterprise_id=prod.created_by if prod.created_by else 1).first()

            # compte stock produit fini: prefer product.stock_account_id else config.compte_stock_id
            prod_obj = session.query(CoreProduct).filter_by(id=prod.product_id).first()
            compte_stock_prod = None
            if prod_obj and getattr(prod_obj, 'stock_account_id', None):
                compte_stock_prod = prod_obj.stock_account_id
            elif config:
                compte_stock_prod = config.compte_stock_id

            # créer journal comptable
            journal = ComptaJournaux(
                date_operation=datetime.utcnow(),
                libelle=f"Production validée {prod.production_code}",
                montant=total_materials_cost,
                type_operation="Production",
                reference=prod.production_code,
                description=f"Production {prod.production_code} - {prod.operator_name or ''}",
                enterprise_id=(prod.created_by or 1),
                user_id=(prod.validated_by or 0),
            )
            session.add(journal)
            session.flush()

            ordre = 1
            # Débit : stock produit fini
            if compte_stock_prod:
                e_debit = ComptaEcritures(
                    journal_id=journal.id,
                    compte_comptable_id=compte_stock_prod,
                    debit=total_materials_cost,
                    credit=Decimal('0'),
                    ordre=ordre,
                    libelle=f"Stock produit fini - {prod_obj.name if prod_obj else prod.product_id}"
                )
                session.add(e_debit)
                ordre += 1

            # Crédit : comptes stock matières premières (prend leur stock_account_id ou config.compte_stock_id)
            for raw_id, amount in material_costs:
                compte_raw = None
                raw_obj = session.query(CoreProduct).filter_by(id=raw_id).first()
                if raw_obj and getattr(raw_obj, 'stock_account_id', None):
                    compte_raw = raw_obj.stock_account_id
                elif config:
                    compte_raw = config.compte_stock_id

                if compte_raw:
                    e_credit = ComptaEcritures(
                        journal_id=journal.id,
                        compte_comptable_id=compte_raw,
                        debit=Decimal('0'),
                        credit=amount,
                        ordre=ordre,
                        libelle=f"Consommation MP - {raw_obj.name if raw_obj else raw_id}"
                    )
                    session.add(e_credit)
                    ordre += 1

            session.commit()
            print(f"✅ Écritures comptables créées pour la production {prod.production_code} (journal {journal.id})")
        except Exception as e:
            session.rollback()
            print(f"⚠️ Erreur création écritures comptables production: {e}")

        return prod
