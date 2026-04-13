"""
Pattern Circuit Breaker - Resilience face aux pannes externes.

Trois etats :
  CLOSED   -> appels passent normalement
  OPEN     -> appels rejetes immediatement (fail fast)
  HALF_OPEN -> un appel test autorise apres recovery_timeout secondes
"""

import time
import threading
from enum import Enum
from typing import Any, Callable, Dict, Optional


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# Alias court utilise dans les tests
State = CircuitBreakerState


class CircuitOpenError(Exception):
    """Leve quand le circuit est OPEN et qu'un appel est tente."""

    def __init__(self, message: str = "Service indisponible - circuit ouvert") -> None:  # noqa: E501
        super().__init__(message)


class CircuitBreaker:
    """Circuit Breaker avec trois etats (CLOSED / OPEN / HALF_OPEN).

    Parametres:
        name             : identifiant du circuit (ex: "philips_hue")
        failure_threshold: nombre d'echecs consecutifs avant ouverture
        recovery_timeout : secondes avant tentative de reconnecter (HALF_OPEN)
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._success_count = 0
        self._total_calls = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Propriete state — transition automatique OPEN -> HALF_OPEN
    # ------------------------------------------------------------------

    @property
    def state(self) -> CircuitBreakerState:
        with self._lock:
            if (
                self._state == CircuitBreakerState.OPEN
                and self._last_failure_time is not None
                and time.time() - self._last_failure_time >= self.recovery_timeout  # noqa: E501
            ):
                self._state = CircuitBreakerState.HALF_OPEN
            return self._state

    # ------------------------------------------------------------------
    # Appel protege
    # ------------------------------------------------------------------

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute func en appliquant la logique du Circuit Breaker."""
        current_state = self.state  # peut basculer OPEN -> HALF_OPEN ici

        with self._lock:
            if current_state == CircuitBreakerState.OPEN:
                raise CircuitOpenError(
                    f"Circuit '{self.name}' ouvert - service indisponible"
                )
            self._total_calls += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except CircuitOpenError:
            raise
        except Exception:
            self._on_failure()
            raise

    # ------------------------------------------------------------------
    # Transitions internes
    # ------------------------------------------------------------------

    def _on_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._success_count += 1
            self._state = CircuitBreakerState.CLOSED

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitBreakerState.OPEN

    # ------------------------------------------------------------------
    # Methodes utilitaires
    # ------------------------------------------------------------------

    def force_open(self) -> None:
        """Force l'etat OPEN (utile pour les tests)."""
        with self._lock:
            self._state = CircuitBreakerState.OPEN
            self._last_failure_time = time.time()

    def force_closed(self) -> None:
        """Force l'etat CLOSED et remet les compteurs a zero."""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def reset(self) -> None:
        """Remet le circuit Breaker a son etat initial."""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._success_count = 0
            self._total_calls = 0

    def get_stats(self) -> dict:
        """Retourne les statistiques du circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": self._total_calls,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self._last_failure_time,
        }

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name!r}, "
            f"state={self.state.value}, "
            f"failures={self._failure_count}/{self.failure_threshold})"
        )
