"""
Store en mémoire pour les appels loggés par @log_call.
Permet de rendre les logs visibles dans l'UI (/admin/logs).
"""

import threading
from datetime import datetime
from typing import List


_lock = threading.Lock()
_entries: List[dict] = []
MAX_ENTRIES = 500


def record(endpoint: str, duration: float, success: bool, error: str = None):
    """Enregistre un appel décoré par @log_call."""
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoint": endpoint,
        "duration_ms": round(duration * 1000, 1),
        "success": success,
        "error": error or "",
    }
    with _lock:
        _entries.append(entry)
        if len(_entries) > MAX_ENTRIES:
            del _entries[:-MAX_ENTRIES]


def get_entries() -> List[dict]:
    """Retourne une copie des entrées (plus récentes en premier)."""
    with _lock:
        return list(reversed(_entries))


def clear():
    """Vide le store (utile pour les tests)."""
    with _lock:
        _entries.clear()
