import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher


class LocationUtils:
    """
    Utility class for normalizing and comparing location strings.
    """

    LOCATION_PATTERNS = [
        r"\b(area|estate|phase|extension|ext|street|st|road|rd|avenue|ave|close|crescent|cres)\b",
        r"\b(phase\s*\d+|ext\s*\d+)\b",
        r"\blga\b",
    ]

    SEPARATORS: set[str] = {",", "-", "/", "\\", "|", ";"}

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the normalizer.

        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider locations as matching
        """
        self.similarity_threshold = similarity_threshold

    def normalize(self, location: str) -> str:
        """
        Normalize a location string to a canonical form.

        Args:
            location (str): Raw location string

        Returns:
            str: Normalized location string
        """
        if not location:
            return ""

        normalized = location.lower().strip()

        normalized = self._remove_accents(normalized)

        normalized = re.sub(r"\s+", " ", normalized)

        normalized = re.sub(r'["\']', "", normalized)

        primary_location = self._extract_primary_location(normalized)

        primary_location = self._remove_location_patterns(primary_location)

        primary_location = re.sub(r"^[,\-\s]+|[,\-\s]+$", "", primary_location)

        primary_location = primary_location.strip()

        return primary_location

    def similarity(self, loc1: str, loc2: str) -> float:
        """
        Calculate similarity between two location strings.

        Args:
            loc1 (str): First location string
            loc2 (str): Second location string

        Returns:
            (float): Similarity score between 0 and 1
        """
        norm1 = self.normalize(loc1)
        norm2 = self.normalize(loc2)

        if not norm1 or not norm2:
            return 0.0

        base_similarity = SequenceMatcher(None, norm1, norm2).ratio()

        if norm1 in norm2 or norm2 in norm1:
            base_similarity = max(base_similarity, 0.9)

        tokens1 = set(norm1.split())
        tokens2 = set(norm2.split())

        if tokens1 and tokens2:
            token_overlap = len(tokens1 & tokens2) / min(len(tokens1), len(tokens2))
            base_similarity = max(base_similarity, token_overlap * 0.95)

        return base_similarity

    def are_same_location(self, loc1: str, loc2: str) -> bool:
        """
        Determine if two location strings refer to the same location.

        Args:
            loc1 (str): First location string
            loc2 (str): Second location string

        Returns:
            True if locations are considered the same
        """
        return self.similarity(loc1, loc2) >= self.similarity_threshold

    def get_canonical_form(self, locations: list[str]) -> tuple[str, list[str]]:
        """
        Given a list of similar locations, return the canonical form
        and group them.

        Args:
            locations (list[str]): List of location strings

        Returns:
            Tuple of (canonical_form, list_of_similar_locations)
        """
        if not locations:
            return "", []

        normalized = [(loc, self.normalize(loc)) for loc in locations]

        norm_counts = Counter(norm for _, norm in normalized)
        canonical_normalized = norm_counts.most_common(1)[0][0]

        canonical_originals = [loc for loc, norm in normalized if norm == canonical_normalized]
        canonical_form = max(canonical_originals, key=len) if canonical_originals else locations[0]

        return canonical_form, locations

    def _remove_accents(self, text: str) -> str:
        nfd = unicodedata.normalize("NFD", text)
        return "".join(char for char in nfd if unicodedata.category(char) != "Mn")

    def _extract_primary_location(self, location: str) -> str:
        """
        Extract the primary location from a composite location string.
        E.g., "Sangotedo, Ajah" -> "sangotedo"
        """

        for sep in self.SEPARATORS:
            if sep in location:
                parts = [p.strip() for p in location.split(sep) if p.strip()]
                if parts:
                    return parts[0]

        return location

    def _remove_location_patterns(self, location: str) -> str:
        for pattern in self.LOCATION_PATTERNS:
            location = re.sub(pattern, "", location, flags=re.IGNORECASE)

        location = re.sub(r"\b\d+\b", "", location)

        return location.strip()
