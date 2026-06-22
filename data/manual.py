from datetime import date, datetime


def get_override(config, key):
    """Returns (value, as_of_date, is_missing). Never raises."""
    entry = config.get("manual_overrides", {}).get(key)
    if entry is None:
        return None, None, True

    value = entry.get("value")
    as_of_str = entry.get("as_of")
    try:
        as_of = datetime.strptime(as_of_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        as_of = None

    return value, as_of, value is None


def staleness_level(as_of, freq, config):
    """Returns 'fresh' | 'stale' | 'unknown'. freq: 'daily' | 'weekly' | 'quarterly'."""
    if as_of is None:
        return "unknown"
    threshold = config.get("staleness_days", {}).get(freq, 9999)
    age_days = (date.today() - as_of).days
    return "stale" if age_days > threshold else "fresh"
