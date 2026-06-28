"""Constants for the FlowIt VMC API."""

from enum import IntEnum, StrEnum


class Speed(StrEnum):
    """VMC Fan speed levels."""

    OFF = "off"
    LEVEL_1 = "1"
    LEVEL_2 = "2"
    LEVEL_3 = "3"
    LEVEL_4 = "4"
    LEVEL_5 = "5"
    AUTO = "auto"
    BOOST = "boost"


class BypassMode(StrEnum):
    """VMC Bypass operation modes."""

    IN_OUT = "0"
    IN_ONLY = "1"
    OUT_ONLY = "2"


class FilterStatus(IntEnum):
    """Filter cleanliness status percentage/level."""

    DIRTY_0 = 0
    DIRTY_25 = 1
    DIRTY_50 = 2
    DIRTY_75 = 3
    CLEAN = 4


class AlertFilterStatus(IntEnum):
    """Alert status for filter maintenance."""

    CLEAN = 0
    DIRTY = 1
    CLOGGED = 2
    MISSING = 3
    NOT_CHECKED = 4


DEFAULT_USERNAME = "api"
TIMEOUT = 10
