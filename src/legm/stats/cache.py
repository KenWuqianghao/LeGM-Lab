"""Simple in-memory TTL cache for NBA stats data."""

import time
from typing import Any, TypeVar

T = TypeVar("T")


class TTLCache:
    """In-memory cache with per-key time-to-live expiration.

    Entries are stored as ``(expiry_timestamp, value)`` tuples. Expired
    entries are cleaned up lazily on ``get`` — no background thread is
    needed.
    """

    def __init__(self, default_ttl: int = 3600) -> None:
        self.default_ttl = default_ttl
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """Return the cached value if present and not expired, else ``None``."""
        entry = self._store.get(key)
        if entry is None:
            return None

        expiry, value = entry
        if time.time() > expiry:
            # Lazy cleanup of expired entry
            del self._store[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store *value* under *key* with an optional per-key TTL override."""
        effective_ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + effective_ttl
        self._store[key] = (expiry, value)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._store.clear()
