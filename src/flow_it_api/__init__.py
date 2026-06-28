"""Python API library client for the FlowIt VMC machine."""

import logging
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("flow-it-api")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "0.0.0"

_LOGGER = logging.getLogger(__name__)
_LOGGER.info("Loading flow-it-api version %s", __version__)
