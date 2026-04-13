"""
Collecteur de metriques applicatives — thread-safe.

Comptabilise : requetes totales, erreurs, latences (p50/p95).
Utilise par GET /api/metrics.
"""

import threading
import time
from typing import Dict, List


class MetricsCollector:
    """Collecte et expose les metriques operationnelles de l'application."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests_total: int = 0
        self._errors_total: int = 0
        self._latencies: List[float] = []  # en secondes
        self._endpoint_counts: Dict[str, int] = {}
        self._start_time: float = time.time()

    def record_request(
        self,
        endpoint: str = "",
        duration: float = 0.0,
        success: bool = True,
    ) -> None:
        """Enregistre une requete avec sa duree et son statut."""
        with self._lock:
            self._requests_total += 1
            if not success:
                self._errors_total += 1
            if duration > 0:
                self._latencies.append(duration)
                # Garde seulement les 1000 dernieres mesures
                if len(self._latencies) > 1000:
                    self._latencies = self._latencies[-1000:]
            if endpoint:
                self._endpoint_counts[endpoint] = (
                    self._endpoint_counts.get(endpoint, 0) + 1
                )

    def _percentile(self, p: float) -> float:
        """Calcule le percentile p (0-100) des latences."""
        if not self._latencies:
            return 0.0
        sorted_lat = sorted(self._latencies)
        idx = int(len(sorted_lat) * p / 100)
        idx = min(idx, len(sorted_lat) - 1)
        return round(sorted_lat[idx] * 1000, 2)  # en ms

    def get_metrics(self) -> dict:
        """Retourne toutes les metriques sous forme de dict."""
        with self._lock:
            total = self._requests_total
            errors = self._errors_total
            error_rate = round(errors / total, 4) if total > 0 else 0.0
            uptime = round(time.time() - self._start_time, 1)
            return {
                "requests_total": total,
                "errors_total": errors,
                "error_rate": error_rate,
                "latency_p50_ms": self._percentile(50),
                "latency_p95_ms": self._percentile(95),
                "uptime_seconds": uptime,
                "endpoints": dict(self._endpoint_counts),
            }

    def reset(self) -> None:
        """Remet les compteurs a zero (utile pour les tests)."""
        with self._lock:
            self._requests_total = 0
            self._errors_total = 0
            self._latencies = []
            self._endpoint_counts = {}
            self._start_time = time.time()


# Instance globale partagee
_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Retourne le collecteur global."""
    return _metrics
