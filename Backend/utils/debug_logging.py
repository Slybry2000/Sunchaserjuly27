import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Environment-controlled debug logging
UNSPLASH_DEBUG = os.environ.get("UNSPLASH_DEBUG", "").lower() in ("1", "true", "yes")


def debug_log(message: str, **kwargs: Any) -> None:
    """Log debug information if UNSPLASH_DEBUG is enabled."""
    if UNSPLASH_DEBUG:
        # Add process ID for multi-process debugging
        pid = os.getpid()
        enhanced_message = f"[{pid}] {message}"
        if kwargs:
            logger.debug(enhanced_message, extra=kwargs)
        else:
            logger.debug(enhanced_message)
