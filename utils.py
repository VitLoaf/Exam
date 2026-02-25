import datetime

def validate_date(date_str: str) -> bool:
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_amount(amount_str: str) -> bool:
    try:
        value = float(amount_str)
        return value > 0
    except (ValueError, TypeError):
        return False

def validate_id(id_str: str) -> bool:
    try:
        value = int(id_str)
        return value > 0
    except (ValueError, TypeError):
        return False