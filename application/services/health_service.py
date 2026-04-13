"""
Service de sante — verifie l'etat de tous les composants critiques.

Utilise par GET /api/health (200 si sain, 503 si degrade)
         et GET /api/readiness.
"""

from typing import Dict, Any

from domain.resilience.circuit_breaker import (
    CircuitBreakerState,
    get_all_circuit_breakers,
)
from app.core.metrics import get_metrics_collector


class HealthService:
    """Agrege l'etat des circuit breakers, de la DB et des metriques."""

    def check_health(self) -> Dict[str, Any]:
        """Retourne le statut de sante global et par service.

        Retourne 'healthy' si aucun circuit n'est OPEN,
        'degraded' sinon.
        """
        services: Dict[str, Any] = {}
        has_open_circuit = False

        # --- Circuit Breakers ---
        circuit_breakers = get_all_circuit_breakers()
        cb_statuses: Dict[str, Any] = {}
        for name, cb in circuit_breakers.items():
            state = cb.state
            is_open = state == CircuitBreakerState.OPEN
            if is_open:
                has_open_circuit = True
            cb_statuses[name] = {
                "state": state.value,
                "healthy": not is_open,
                "failure_count": cb._failure_count,
            }
        services["circuit_breakers"] = cb_statuses

        # --- Base de donnees ---
        db_healthy = self._check_database()
        services["database"] = {
            "state": "up" if db_healthy else "down",
            "healthy": db_healthy,
        }
        if not db_healthy:
            has_open_circuit = True

        # --- API ---
        services["api"] = {"state": "up", "healthy": True}

        overall = "healthy" if not has_open_circuit else "degraded"
        return {
            "status": overall,
            "services": services,
        }

    def check_readiness(self) -> Dict[str, Any]:
        """Indicateur pret/non-pret pour les load balancers."""
        health = self.check_health()
        ready = health["status"] == "healthy"
        return {"ready": ready, "status": health["status"]}

    def get_metrics_summary(self) -> dict:
        """Retourne les metriques operationnelles enrichies des CB."""
        collector = get_metrics_collector()
        metrics = collector.get_metrics()

        # Ajouter l'etat des circuit breakers
        circuit_breakers = get_all_circuit_breakers()
        cb_info = []
        for name, cb in circuit_breakers.items():
            cb_info.append({
                "name": name,
                "state": cb.state.value,
                "failure_count": cb._failure_count,
                "total_calls": cb._total_calls,
            })
        metrics["circuit_breakers"] = cb_info
        metrics["open_circuits"] = sum(
            1 for cb in circuit_breakers.values()
            if cb.state == CircuitBreakerState.OPEN
        )
        return metrics

    def _check_database(self) -> bool:
        """Verifie la connexion a la base de donnees."""
        try:
            import sqlite3
            import config
            conn = sqlite3.connect(config.DB_NAME, timeout=2)
            conn.execute("SELECT 1")
            conn.close()
            return True
        except Exception:
            return False
