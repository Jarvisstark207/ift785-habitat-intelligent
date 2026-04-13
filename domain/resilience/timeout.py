"""
Decorateur @timeout — protege un appel contre les blocages infinis.

Usage:
    @timeout(seconds=5)
    def call_external_api():
        ...  # ne bloquera jamais plus de 5 secondes

Leve TimeoutError si le delai est depasse.
Compatible fonctions synchrones uniquement (threading.Timer).
"""

import functools
import threading
from typing import Any, Callable


def timeout(seconds: float = 5.0) -> Callable:
    """Decorateur qui coupe l'appel apres *seconds* secondes.

    Parametres:
        seconds: delai maximal en secondes (defaut: 5.0)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result: list = []
            error: list = []

            def target() -> None:
                try:
                    result.append(func(*args, **kwargs))
                except Exception as exc:
                    error.append(exc)

            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                raise TimeoutError(
                    f"'{func.__name__}' a depasse le delai de {seconds}s"
                )
            if error:
                raise error[0]
            return result[0] if result else None

        return wrapper
    return decorator
