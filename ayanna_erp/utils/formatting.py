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


def format_amount_for_pdf(amount, currency=None):
    """Format amount for PDF exports to match spec: no thousands separator,
    lowercase alphabetic currency (e.g. "1000 fc").

    - If amount is an integer value, display without decimals ("1000").
    - Otherwise, keep up to 2 decimals but strip trailing zeros ("123.5" or "123.45").
    - currency can be a symbol ("FC", "$") or a code ("CDF"). If alphabetic, the output will be lowercased.

    Returns a string like '1000 fc' or '123.5 $'. If currency is None, returns only the numeric part.
    """
    try:
        if amount is None:
            return "-"
        amt = float(amount)
        # If integer amount, display without decimals but with thousand separator
        if abs(amt - int(amt)) < 1e-9:
            s = f"{int(amt):,}".replace(',', ' ')
        else:
            # Show two decimals but remove trailing zeros, keep thousand separators
            # Use formatting with grouping then strip zeros
            s_full = f"{amt:,.2f}".replace(',', ' ')
            # Remove trailing .00 or trailing zeros
            if s_full.endswith('.00'):
                s = s_full[:-3]
            else:
                # strip trailing zeros after decimal point
                s = s_full.rstrip('0').rstrip('.')

        cur_fmt = ''
        if currency:
            try:
                if any(ch.isalpha() for ch in str(currency)):
                    cur_fmt = str(currency).lower()
                else:
                    cur_fmt = str(currency)
            except Exception:
                cur_fmt = str(currency)

        return f"{s} {cur_fmt}".strip()
    except Exception:
        try:
            return f"{amount} {currency or ''}".strip()
        except Exception:
            return str(amount)
