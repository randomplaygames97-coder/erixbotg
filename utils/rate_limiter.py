"""Rate limiter in-memory semplice per mitigare spam."""

from __future__ import annotations

import time
from threading import Lock
from typing import Dict, Tuple


class InMemoryRateLimiter:
    """Rate limiter basato su timestamp ultimo hit per user+scope."""

    def __init__(self) -> None:
        self._hits: Dict[Tuple[int, str], float] = {}
        self._lock = Lock()

    def is_limited(self, user_id: int, scope: str, cooldown_seconds: float) -> bool:
        """Restituisce True se l'utente supera il limite per lo scope."""
        now = time.monotonic()
        key = (user_id, scope)

        with self._lock:
            last_hit = self._hits.get(key, 0.0)
            if now - last_hit < cooldown_seconds:
                return True

            self._hits[key] = now
            return False


rate_limiter = InMemoryRateLimiter()

