"""
Décorateurs transversaux - Itération 8 : Méta-programmation
@log_call       : log automatique entrée/durée/résultat
@validate_input : validation Pydantic avant exécution
@require_role   : vérification du rôle depuis provided_auth
"""

import functools
import inspect
import logging
import time

from fastapi import HTTPException
from starlette.requests import Request

from app.core.provided_auth import get_current_user_from_request, require_minimum_role
from app.core import log_store

logger = logging.getLogger(__name__)


def log_call(func):
    """
    Enregistre le nom de la fonction, les arguments, la durée et le résultat.
    Supporte les fonctions synchrones et asynchrones.
    Utilise functools.wraps pour préserver __name__ et __doc__.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            logger.info("%s called", func.__name__)
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.info("%s completed in %.3fs", func.__name__, duration)
                log_store.record(func.__name__, duration, success=True)
                return result
            except Exception as exc:
                duration = time.time() - start
                logger.error(
                    "%s raised %s in %.3fs: %s",
                    func.__name__, type(exc).__name__, duration, exc
                )
                log_store.record(func.__name__, duration, success=False,
                                 error=f"{type(exc).__name__}: {exc}")
                raise
        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        logger.info("%s called", func.__name__)
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.info("%s completed in %.3fs", func.__name__, duration)
            log_store.record(func.__name__, duration, success=True)
            return result
        except Exception as exc:
            duration = time.time() - start
            logger.error(
                "%s raised %s in %.3fs: %s",
                func.__name__, type(exc).__name__, duration, exc
            )
            log_store.record(func.__name__, duration, success=False,
                             error=f"{type(exc).__name__}: {exc}")
            raise
    return sync_wrapper
