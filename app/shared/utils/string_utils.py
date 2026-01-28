import unicodedata


def normalize_location(location: str) -> str:
    """
    Normalize a location string by removing accents and converting to lowercase.
    """

    normalized = unicodedata.normalize("NFKD", location)
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower()
