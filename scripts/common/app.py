"""
Scout & Steward

Module:
    app.py

Purpose:
    Provides the shared application context for all Scout & Steward
    scripts.

Responsibilities:
    - Load project configuration
    - Initialize logging
    - Expose project paths

Author:
    Meybell & Co.

Version:
    1.0.0
"""

from common.load_config import CONFIG
from common.logger import get_logger
import common.paths as paths


class App:
    """
    Shared application context.

    Every executable script should create one App instance:

        app = App("normalize")

    This provides convenient access to shared infrastructure without
    each script needing to import multiple modules.
    """

    def __init__(self, module_name: str) -> None:

        self.module_name: str = module_name

        self.config = CONFIG

        self.paths = paths

        self.logger = get_logger(module_name)

__all__ = [
    "App",
]
