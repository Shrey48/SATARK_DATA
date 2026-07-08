"""Simple in-memory inventory cache."""
from typing import Any, Dict, Optional


class InventoryCache:
    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        self._hit_count = 0
        self._miss_count = 0

    def has(self, key: str) -> bool:
        return self._lookup(key) is not None

    def get(self, key: str) -> Optional[Any]:
        value = self._lookup(key)
        if value is not None:
            self._hit_count += 1
        else:
            self._miss_count += 1
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def invalidate(self, key: str) -> None:
        self._evict(key)

    def clear(self) -> None:
        self._store.clear()

    def _lookup(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def _evict(self, key: str) -> None:
        self._store.pop(key, None)

    def stats(self) -> dict:
        return {"hits": self._hit_count, "misses": self._miss_count}
