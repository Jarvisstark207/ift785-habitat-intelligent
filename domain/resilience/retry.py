"""
Decorateur @retry — retry avec backoff exponentiel.

Complement du Circuit Breaker : tente plusieurs fois un appel
avant d'abandonner.

Ordre recommande des protections :
  @timeout(5)     -> protege contre blocage infini
  @retry(3, 1.5)  -> tente plusieurs fois avant d'abandonner
  CircuitBreaker  -> coupe si trop d'echecs consecutifs

Usage:
    @retry(max_attempts=3, backoff=1.5)
    def call_external_api():
        ...
"""

import functools
import time
from typing import Any, Callable, Type, Tuple


def retry(
    max_attempts: int = 3,
    backoff: float = 1.5,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorateur qui rejoue l'appel en cas d'echec.

    Parametres:
        max_attempts : nombre maximal de tentatives
        backoff      : facteur multiplicatif du delai entre tentatives
        exceptions   : types d'exceptions interceptes (defaut: Exception)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = backoff
            last_exc: Exception = RuntimeError("max_attempts < 1")
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= backoff
            raise last_exc

        return wrapper
    return decorator
