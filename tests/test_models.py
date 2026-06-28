import json

import pytest

from flow_it_api.const import AlertFilterStatus, BypassMode, FilterStatus, Speed
from flow_it_api.models import MachineData, MachineStatusResponse

SAMPLE_STATUS = {
    "lastUpdate": 1775720173,
    "chrono_id": "00000000",
    "status": "TRUE",
    "name": "F412FACD51AE",
    "data": {
        "event": "api",
        "sensors": {
            "Sin": {"pressure": 99490.5, "temperature": 292.28, "humidity": 0.41515},
            "Sout": {
                "pressure": 99490.5,
                "temperature": 291.49002,
                "humidity": 0.41515,
            },
            "Iin": {"pressure": 99485.0, "temperature": 291.98999, "humidity": 0.41554},
            "Iout": {"pressure": 99472.0, "temperature": 291.78, "humidity": 0.41563},
        },
        "mode": {
            "speed": "auto",
            "autoSpeed": "2",
            "flowIn": "TRUE",
            "flowOut": "TRUE",
            "bypassMode": "0",
            "iaq": 100,
            "temperatureIn": 291.98999,
            "temperatureOut": 292.28,
            "humidityIn": 0.41554,
            "humidityOut": 0.41515,
            "pressureIn": 99485.0,
            "pressureOut": 99490.5,
            "bypassOn": "FALSE",
        },
        "filter": {
            "hepa": {"status": 4, "changed": 532880},
            "g4": {"status": 4, "changed": 532880},
        },
        "alert": {
            "update_reboot": "FALSE",
            "worries": "FALSE",
            "ice": "FALSE",
            "condensation": "FALSE",
            "filterS": 0,
            "filterI": 0,
            "warmup": "FALSE",
            "service": "FALSE",
            "fault-code": "0x000f7fdf",
            "net-fault-code": "0x0000001f",
            "version": "1.9.3 D",
        },
    },
}


def test_machine_status_parsing():
    status = MachineStatusResponse(**SAMPLE_STATUS)
    assert status.status is True
    assert status.data.mode.speed == Speed.AUTO
    assert status.data.mode.flowIn is True
    assert status.data.mode.bypassMode == BypassMode.IN_OUT
    assert status.data.filter.hepa.status == FilterStatus.CLEAN
    assert status.data.alert.filterS == AlertFilterStatus.CLEAN
    assert status.data.alert.fault_code == "0x000f7fdf"


def test_boolean_parsing():
    from flow_it_api.models import parse_bool

    assert parse_bool("TRUE") is True
    assert parse_bool("FALSE") is False
    assert parse_bool("true") is True
    assert parse_bool(True) is True
    assert parse_bool(0) is False


def test_sensor_value_parsing():
    from flow_it_api.models import SensorReadings, parse_sensor_value

    assert parse_sensor_value(292.28) == 292.28
    assert parse_sensor_value(0.0) is None
    assert parse_sensor_value(0) is None
    assert parse_sensor_value("invalid") is None

    # Test properties
    sensor = SensorReadings(pressure=0, temperature=0, humidity=0)
    assert sensor.pressure is None
    assert sensor.temperature is None
    assert sensor.humidity is None
    assert sensor.temperature_celsius is None

    sensor2 = SensorReadings(pressure=1000, temperature=273.15, humidity=50)
    assert sensor2.pressure == 1000.0
    assert sensor2.temperature == 273.15
    assert sensor2.humidity == 50.0
    assert sensor2.temperature_celsius == 0.0
