"""
scripts/etl/retry_handler.py
Lógica de reintentos para pipeline ETL con exponential backoff.

RESPONSABILIDAD: Distinguir errores transient (retry) vs validation (no retry)
PRINCIPIO: "Resiliente a fallos temporales, pero falla rápido en errores de lógica"

Errores QUE SE REINTENTA (transient):
  - ConnectionError, TimeoutError (API Kawak inestable)
  - FileExistsError, PermissionError (lockeos temporales)
  - MemoryError (disponibilidad temporal)

Errores QUE NO SE REINTENTA (validation, lógica):
  - ValidationError (datos inválidos — retry no ayuda)
  - FileNotFoundError (archivo faltante — config error)
  - ValueError, TypeError (error de programa)
  - KeyError (fórmula incorrecta)
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    RetryError,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Excepciones que SÍ se reintenta (transient failures)
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    BrokenPipeError,
    OSError,  # Cubre FileExistsError, PermissionError, etc
)

# Excepciones que NO se reintenta (validation/logic errors)
NON_RETRYABLE_EXCEPTIONS = (
    ValueError,
    TypeError,
    KeyError,
    FileNotFoundError,
    IndexError,
)


class TransientFailure(Exception):
    """Excepción para marcar fallos transient (recuperables)."""

    pass


class ValidationFailure(Exception):
    """Excepción para marcar fallos de validación (no recuperables)."""

    pass


def is_retryable(exception: Exception) -> bool:
    """Determina si una excepción debe ser reintenrada."""
    # Si es una excepción conocida no retryable, no reintentar
    if isinstance(exception, NON_RETRYABLE_EXCEPTIONS):
        return False

    # Si es una excepción conocida retryable, reintentar
    if isinstance(exception, RETRYABLE_EXCEPTIONS):
        return True

    # Excepciones explícitas
    if isinstance(exception, ValidationFailure):
        return False
    if isinstance(exception, TransientFailure):
        return True

    # Por defecto, no reintentar (fail fast)
    return False


def retry_pipeline(
    max_attempts: int = 3,
    initial_wait: float = 2.0,
    max_wait: float = 60.0,
) -> Callable[[F], F]:
    """
    Decorador para reintentar operaciones de pipeline con exponential backoff.

    Args:
        max_attempts: Máximo número de intentos (default 3)
        initial_wait: Espera inicial en segundos (default 2)
        max_wait: Espera máxima en segundos (default 60)

    Returns:
        Función decorada

    Ejemplo:
        @retry_pipeline(max_attempts=3)
        def main():
            consolidar_api()
            actualizar_consolidado()
    """

    def decorator(func: F) -> F:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=initial_wait, max=max_wait),
            retry=retry_if_exception(is_retryable),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


class RetryStats:
    """Estadísticas de reintentos durante una sesión."""

    def __init__(self) -> None:
        self.total_attempts = 0
        self.successful_retries = 0
        self.failed_operations = 0
        self.transient_errors = []

    def record_attempt(self) -> None:
        self.total_attempts += 1

    def record_success_after_retry(self) -> None:
        self.successful_retries += 1

    def record_failure(self, exception: Exception) -> None:
        self.failed_operations += 1
        if is_retryable(exception):
            self.transient_errors.append((type(exception).__name__, str(exception)))

    def summary(self) -> dict[str, Any]:
        return {
            "total_attempts": self.total_attempts,
            "successful_retries": self.successful_retries,
            "failed_operations": self.failed_operations,
            "retry_success_rate": (
                self.successful_retries / self.total_attempts * 100
                if self.total_attempts > 0
                else 0
            ),
            "transient_errors_found": len(self.transient_errors),
        }


# Global stats instance
_retry_stats = RetryStats()


def get_retry_stats() -> dict[str, Any]:
    """Retorna estadísticas de reintentos."""
    return _retry_stats.summary()


def reset_retry_stats() -> None:
    """Reinicia estadísticas."""
    global _retry_stats
    _retry_stats = RetryStats()
