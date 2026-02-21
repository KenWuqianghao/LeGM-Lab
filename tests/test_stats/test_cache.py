"""Tests for TTLCache — in-memory cache with per-key expiration."""

import time
from unittest.mock import patch

from legm.stats.cache import TTLCache


class TestTTLCache:
    """Tests for TTLCache set/get/clear behaviour."""

    def test_set_and_get_returns_value(self) -> None:
        """A value stored with set() should be retrievable via get()."""
        cache = TTLCache(default_ttl=60)
        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

    def test_get_missing_key_returns_none(self) -> None:
        """get() on a key that was never set should return None."""
        cache = TTLCache(default_ttl=60)

        assert cache.get("nonexistent") is None

    def test_expired_entry_returns_none(self) -> None:
        """An entry past its TTL should return None on get()."""
        cache = TTLCache(default_ttl=1)

        now = time.time()
        with patch("legm.stats.cache.time.time", return_value=now):
            cache.set("key", "value")

        # Simulate time advancing past the TTL
        with patch("legm.stats.cache.time.time", return_value=now + 2):
            assert cache.get("key") is None

    def test_expired_entry_is_removed_from_store(self) -> None:
        """Accessing an expired entry should lazily remove it from the store."""
        cache = TTLCache(default_ttl=1)

        now = time.time()
        with patch("legm.stats.cache.time.time", return_value=now):
            cache.set("key", "value")

        with patch("legm.stats.cache.time.time", return_value=now + 2):
            cache.get("key")  # triggers lazy cleanup

        assert "key" not in cache._store

    def test_not_expired_entry_still_accessible(self) -> None:
        """An entry within its TTL should still be returned."""
        cache = TTLCache(default_ttl=60)

        now = time.time()
        with patch("legm.stats.cache.time.time", return_value=now):
            cache.set("key", "value")

        # Still within the 60-second TTL
        with patch("legm.stats.cache.time.time", return_value=now + 30):
            assert cache.get("key") == "value"

    def test_custom_per_key_ttl(self) -> None:
        """A per-key TTL override should be respected over the default."""
        cache = TTLCache(default_ttl=3600)

        now = time.time()
        with patch("legm.stats.cache.time.time", return_value=now):
            cache.set("short_lived", "data", ttl=5)

        # After 6 seconds the custom TTL should have expired
        with patch("legm.stats.cache.time.time", return_value=now + 6):
            assert cache.get("short_lived") is None

    def test_clear_empties_cache(self) -> None:
        """clear() should remove all entries from the cache."""
        cache = TTLCache(default_ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        cache.clear()

        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.get("c") is None
        assert len(cache._store) == 0

    def test_overwrite_existing_key(self) -> None:
        """Setting the same key twice should overwrite the previous value."""
        cache = TTLCache(default_ttl=60)
        cache.set("key", "old")
        cache.set("key", "new")

        assert cache.get("key") == "new"

    def test_stores_various_types(self) -> None:
        """Cache should work with dicts, lists, and other Python objects."""
        cache = TTLCache(default_ttl=60)
        cache.set("dict_key", {"nested": True})
        cache.set("list_key", [1, 2, 3])
        cache.set("int_key", 42)

        assert cache.get("dict_key") == {"nested": True}
        assert cache.get("list_key") == [1, 2, 3]
        assert cache.get("int_key") == 42
