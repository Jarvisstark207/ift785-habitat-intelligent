"""Pattern Proxy - Cache proxy pour les adapters d'integration"""

from datetime import datetime
from typing import List, Optional

from domain.integrations.smart_home_adapter import SmartHomeAdapter


class CacheProxy(SmartHomeAdapter):
    """Proxy de cache pour les appels aux APIs tierces.

    Evite les appels repetes aux APIs externes en mettant en cache
    les reponses pendant un delai configurable (TTL).
    Les commandes de controle contournent toujours le cache.
    """

    def __init__(self, adapter: SmartHomeAdapter, ttl: int = 60) -> None:
        self._adapter = adapter
        self._ttl = ttl
        self._cache: dict = {}
        self._timestamps: dict = {}
        self._hit_count: int = 0
        self._miss_count: int = 0

    def _is_valid(self, key: str) -> bool:
        """Verifie si l'entree de cache est encore valide"""
        if key not in self._timestamps:
            return False
        elapsed = (datetime.now() - self._timestamps[key]).total_seconds()
        return elapsed < self._ttl

    def _get_cached(self, key: str):
        """Retourne la valeur en cache si valide, sinon None"""
        if self._is_valid(key):
            self._hit_count += 1
            return self._cache[key]
        self._miss_count += 1
        return None

    def _set_cache(self, key: str, value) -> None:
        """Stocke une valeur dans le cache"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()

    def get_status(self) -> dict:
        """Retourne le statut (mis en cache)"""
        cached = self._get_cached("status")
        if cached is not None:
            return cached
        result = self._adapter.get_status()
        self._set_cache("status", result)
        return result

    def get_devices(self) -> List[dict]:
        """Retourne la liste des appareils (mis en cache)"""
        cached = self._get_cached("devices")
        if cached is not None:
            return cached
        result = self._adapter.get_devices()
        self._set_cache("devices", result)
        return result

    def control_device(self, device_id: str, command: dict) -> dict:
        """Envoie une commande (toujours direct, invalide le cache)"""
        result = self._adapter.control_device(device_id, command)
        if result.get("success"):
            self._cache.pop("devices", None)
            self._cache.pop("status", None)
            self._timestamps.pop("devices", None)
            self._timestamps.pop("status", None)
        return result

    def get_adapter_name(self) -> str:
        return self._adapter.get_adapter_name()

    def invalidate(self, key: Optional[str] = None) -> None:
        """Invalide une entree ou tout le cache"""
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()

    def get_cache_stats(self) -> dict:
        """Retourne les statistiques du cache"""
        total = self._hit_count + self._miss_count
        ratio = self._hit_count / total if total > 0 else 0.0
        return {
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_ratio": round(ratio, 2),
            "cached_keys": list(self._cache.keys()),
            "ttl": self._ttl,
        }
