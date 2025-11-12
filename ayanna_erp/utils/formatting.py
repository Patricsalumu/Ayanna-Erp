from ayanna_erp.database.database_manager import get_database_manager, Entreprise


def format_amount(amount):
    """Format amount as integer with space as thousands separator (e.g. 1 500 000).

    Returns string.
    """
    try:
        v = int(round(float(amount)))
        return f"{v:,}".replace(',', ' ')
    except Exception:
        try:
            return str(int(amount))
        except Exception:
            return str(amount)


def get_currency(entreprise_id=None):
    """Return currency symbol/code for entreprise id; fallback 'F'."""
    try:
        if entreprise_id is None:
            return 'F'
        db = get_database_manager()
        session = db.get_session()
        ent = session.query(Entreprise).filter_by(id=entreprise_id).first()
        session.close()
        if ent and getattr(ent, 'currency', None):
            return getattr(ent, 'currency')
    except Exception:
        pass
    return 'F'
