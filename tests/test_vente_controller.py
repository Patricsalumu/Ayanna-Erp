import pytest
from types import SimpleNamespace
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController


class MockResult:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class MockSession:
    def __init__(self, behavior=None):
        # behavior: dict mapping keywords -> return value for fetchone
        self.behavior = behavior or {}
        self._added = []

    def execute(self, query, params=None):
        s = str(query)
        # simple keyword checks to return appropriate rows
        if 'FROM compta_config' in s:
            return MockResult(self.behavior.get('compta_config'))
        if 'FROM stock_produits_entrepot spe' in s:
            return MockResult(self.behavior.get('spe_quantity'))
        if "SELECT id FROM stock_warehouses" in s:
            return MockResult(self.behavior.get('warehouse_row'))
        if 'SELECT last_insert_rowid()' in s:
            return MockResult((1,))
        # default empty
        return MockResult(None)

    def flush(self):
        pass

    def commit(self):
        self._committed = True

    def rollback(self):
        self._rolled_back = True

    def close(self):
        pass

    # minimal query emulation used in add_payment
    class _Q:
        def __init__(self, first_obj):
            self._first = first_obj

        def filter_by(self, **kwargs):
            return self

        def first(self):
            return self._first

    def query(self, model):
        # return an object whose first() yields a pre-built panier if provided
        return MockSession._Q(self.behavior.get('panier'))

    def add(self, obj):
        self._added.append(obj)

    def refresh(self, obj):
        pass


class FakeDB:
    def __init__(self, session):
        self._session = session

    def session_scope(self):
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            yield self._session

        return _ctx()

    def get_session(self):
        return self._session


def make_panier(prod_qty=1, prod_price=10.0, payments=None):
    ligne = SimpleNamespace(product_id=1, quantity=prod_qty, price=prod_price, total=prod_qty * prod_price)
    panier = SimpleNamespace(
        id=123,
        produits=[ligne],
        payments=payments or [],
        total_final=prod_qty * prod_price,
        status='en_cours',
        payment_method='Crédit',
        subtotal=prod_qty * prod_price,
        remise_amount=0.0,
        user_id=1,
    )
    return panier


def test_add_payment_finalize_success():
    panier = make_panier()
    session = MockSession({'panier': panier, 'spe_quantity': (10,)})
    db = FakeDB(session)
    ctrl = VenteController()
    ctrl.db = db

    # patch finalize_sale to return success
    def fake_finalize(panier_id, amount_received=0.0, payment_method=None, user_id=None):
        return True, 'ok'

    ctrl.finalize_sale = fake_finalize

    res = ctrl.add_payment(panier.id, amount=10.0, payment_method='Espèces', user_id=1)
    assert res.payment_status in ('PAYÉE', 'PARTIELLEMENT PAYÉE', 'NON PAYÉE')


def test_add_payment_finalize_failure_raises():
    panier = make_panier()
    session = MockSession({'panier': panier, 'spe_quantity': (10,)})
    db = FakeDB(session)
    ctrl = VenteController()
    ctrl.db = db

    def fake_finalize(panier_id, amount_received=0.0, payment_method=None, user_id=None):
        return False, 'probleme config'

    ctrl.finalize_sale = fake_finalize

    with pytest.raises(ValueError) as ei:
        ctrl.add_payment(panier.id, amount=10.0, payment_method='Espèces', user_id=1)
    assert 'Échec finalisation vente' in str(ei.value)


def test_finalize_sale_insufficient_stock():
    # simulate spe_quantity less than needed
    panier = make_panier(prod_qty=5)
    # spe_quantity returns a single-column row with quantity 2
    session = MockSession({'panier': panier, 'spe_quantity': (2,)})
    db = FakeDB(session)
    ctrl = VenteController()
    ctrl.db = db

    ok, msg = ctrl.finalize_sale(panier.id, amount_received=0.0, payment_method='Crédit', user_id=1)
    assert not ok
    assert 'Stock insuffisant' in msg


def test_finalize_sale_missing_compta_config():
    panier = make_panier(prod_qty=1)
    # spe_quantity sufficient
    session = MockSession({'panier': panier, 'spe_quantity': (10,), 'compta_config': None})
    db = FakeDB(session)
    ctrl = VenteController()
    ctrl.db = db

    ok, msg = ctrl.finalize_sale(panier.id, amount_received=0.0, payment_method='Crédit', user_id=1)
    assert not ok
    assert 'Configuration comptable introuvable' in msg
