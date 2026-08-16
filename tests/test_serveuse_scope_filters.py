from types import SimpleNamespace

from ayanna_erp.modules.restaurant.views.boncommande_widget import BonCommandeWidget
from ayanna_erp.modules.boutique.view.commandes_index import CommandesIndexWidget


class DummyUser:
    def __init__(self, user_id, role, name, email=None):
        self.id = user_id
        self.role = role
        self.name = name
        self.email = email or f"{name}@test.local"


def test_boncommande_widget_filters_for_serveuse():
    widget = BonCommandeWidget.__new__(BonCommandeWidget)
    widget.current_user = DummyUser(7, "serveuse", "Julie")

    rows = [
        SimpleNamespace(id=1, serveuse_id=7, serveuse_name="Julie"),
        SimpleNamespace(id=2, serveuse_id=9, serveuse_name="Sonia"),
    ]

    filtered = widget._filter_rows_for_current_user(rows)
    assert [r.id for r in filtered] == [1]


def test_commandes_index_filters_for_serveuse():
    widget = CommandesIndexWidget.__new__(CommandesIndexWidget)
    widget.current_user = DummyUser(7, "serveuse", "Julie")

    commandes = [
        {"id": 1, "serveuse_name": "Julie", "user_name": ""},
        {"id": 2, "serveuse_name": "Sonia", "user_name": ""},
    ]

    filtered = widget._filter_commandes_for_current_user(commandes)
    assert [c["id"] for c in filtered] == [1]
