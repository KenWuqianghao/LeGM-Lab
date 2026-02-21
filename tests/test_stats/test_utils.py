"""Tests for stats utility functions."""

import re
from unittest.mock import patch

from legm.stats.utils import get_current_season, normalize_name


class TestGetCurrentSeason:
    """Tests for get_current_season."""

    def test_returns_season_string_format(self) -> None:
        """Should return a string matching the 'YYYY-YY' pattern."""
        season = get_current_season()
        assert re.match(r"^\d{4}-\d{2}$", season), f"Unexpected format: {season}"

    def test_october_starts_new_season(self) -> None:
        """In October, the season should start in the current year."""
        from datetime import datetime

        with patch("legm.stats.utils.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 10, 15)
            season = get_current_season()

        assert season == "2025-26"

    def test_february_uses_previous_year(self) -> None:
        """In February, the season should have started the previous year."""
        from datetime import datetime

        with patch("legm.stats.utils.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 19)
            season = get_current_season()

        assert season == "2025-26"

    def test_september_uses_previous_year(self) -> None:
        """In September (before October), the season started the previous year."""
        from datetime import datetime

        with patch("legm.stats.utils.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 9, 1)
            season = get_current_season()

        assert season == "2024-25"


class TestNormalizeName:
    """Tests for normalize_name."""

    def test_lowercases_input(self) -> None:
        """Should convert to lowercase."""
        assert normalize_name("LeBron James") == "lebron james"

    def test_strips_whitespace(self) -> None:
        """Should strip leading and trailing whitespace."""
        assert normalize_name("  Steph Curry  ") == "steph curry"

    def test_collapses_multiple_spaces(self) -> None:
        """Should collapse multiple internal spaces to a single space."""
        assert normalize_name("Kevin   Durant") == "kevin durant"
