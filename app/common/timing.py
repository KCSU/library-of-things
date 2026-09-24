import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any


def log_slow(arg: Callable[..., Any] | float = 1.0) -> Callable[..., Any]:
    """
    Log at INFO when a call takes at least `arg` seconds.
    Usable as a bare decorator (@log_slow) or with a threshold (@log_slow(5.0)).
    """
    threshold = 1.0 if callable(arg) else float(arg)

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        logger = logging.getLogger(f.__module__)
        name = getattr(f, '__qualname__', repr(f))

        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return f(*args, **kwargs)
            finally:
                # Log even if raised.
                elapsed = time.perf_counter() - start
                if elapsed >= threshold:
                    logger.info('%s took %.2fs', name, elapsed)

        return wrapper

    return decorator(arg) if callable(arg) else decorator


# For work whose duration is worth knowing every time.
log_duration = log_slow(0.0)
