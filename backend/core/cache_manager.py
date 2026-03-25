import json
import hashlib
from pathlib import Path
from typing import Any, Optional


CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class CacheManager:
    """
    Simple file-based cache manager.

    Responsibilities:
    - Store and retrieve cached objects by key
    - Avoid repeated API / LLM calls
    """

    def _key_to_filename(self, key: str) -> Path:
        """
        Convert a cache key into a safe filename using hashing.
        """
        hashed = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{hashed}.json"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached data if it exists.
        """
        path = self._key_to_filename(key)

        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Store data in cache.
        """
        path = self._key_to_filename(key)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
        except Exception:
            pass

    def exists(self, key: str) -> bool:
        """
        Check if cache entry exists.
        """
        return self._key_to_filename(key).exists()

    def clear(self) -> None:
        """
        Clear all cached entries.
        """
        for file in CACHE_DIR.glob("*.json"):
            try:
                file.unlink()
            except Exception:
                pass
