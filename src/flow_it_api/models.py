"""Data models for the FlowIt VMC API."""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from .const import AlertFilterStatus, BypassMode, FilterStatus, Speed


def parse_bool(v: Any) -> bool:
    """
    Parse a value as a boolean.

    Supports string values like "TRUE" and "FALSE".
    """
    if isinstance(v, str):
        if v.upper() == "TRUE":
            return True
        if v.upper() == "FALSE":
            return False
    return bool(v)


FlowItBool = Annotated[bool, BeforeValidator(parse_bool)]


def parse_sensor_value(v: Any) -> float | None:
    """Parse sensor reading, returning None if 0."""
    try:
        val = float(v)
        if val == 0.0:
            return None
        return val
    except (TypeError, ValueError):
        return None


FlowItSensorValue = Annotated[float | None, BeforeValidator(parse_sensor_value)]


class SensorReadings(BaseModel):
    """Raw sensor readings (pressure, temperature, humidity)."""

    pressure: FlowItSensorValue
    temperature: FlowItSensorValue
    humidity: FlowItSensorValue

    @property
    def temperature_celsius(self) -> float | None:
        """Return temperature in Celsius."""
        if self.temperature is None:
            return None
        return round(self.temperature - 273.15, 2)


class MachineSensors(BaseModel):
    """Collection of all machine sensors."""

    Sin: SensorReadings = Field(..., description="Inflow sensor before fan")
    Sout: SensorReadings = Field(..., description="Inflow sensor after fan")
    Iin: SensorReadings = Field(..., description="Extraction sensor before fan")
    Iout: SensorReadings = Field(..., description="Extraction sensor after fan")


class MachineMode(BaseModel):
    """Machine operation mode and environmental data."""

    speed: Speed
    autoSpeed: str
    flowIn: FlowItBool
    flowOut: FlowItBool
    bypassMode: BypassMode
    iaq: int
    temperatureIn: FlowItSensorValue
    temperatureOut: FlowItSensorValue
    humidityIn: FlowItSensorValue
    humidityOut: FlowItSensorValue
    pressureIn: FlowItSensorValue
    pressureOut: FlowItSensorValue
    bypassOn: FlowItBool = False

    @property
    def temperatureIn_celsius(self) -> float | None:
        """Return inflow temperature in Celsius."""
        if self.temperatureIn is None:
            return None
        return round(self.temperatureIn - 273.15, 2)

    @property
    def temperatureOut_celsius(self) -> float | None:
        """Return outflow temperature in Celsius."""
        if self.temperatureOut is None:
            return None
        return round(self.temperatureOut - 273.15, 2)


class FilterDetail(BaseModel):
    """Detailed filter information."""

    status: FilterStatus
    changed: int


class MachineFilter(BaseModel):
    """Machine filter status (HEPA and G4)."""

    hepa: FilterDetail
    g4: FilterDetail


class MachineAlert(BaseModel):
    """Machine alerts and diagnostic status."""

    update_reboot: FlowItBool
    worries: FlowItBool
    ice: FlowItBool
    condensation: FlowItBool
    filterS: AlertFilterStatus
    filterI: AlertFilterStatus
    warmup: FlowItBool
    service: FlowItBool
    fault_code: str = Field(..., alias="fault-code")
    net_fault_code: str = Field(..., alias="net-fault-code")
    version: str


class MachineData(BaseModel):
    """Complete machine data container."""

    event: str
    sensors: MachineSensors
    mode: MachineMode
    filter: MachineFilter
    alert: MachineAlert


class MachineStatusResponse(BaseModel):
    """Full machine status response from REST/WS."""

    model_config = ConfigDict(populate_by_name=True)

    lastUpdate: int
    chrono_id: str
    status: FlowItBool
    name: str
    data: MachineData


class MachineInfoResponse(BaseModel):
    """Machine information response (version info)."""

    model: str
    api_ver: str
    fw_ver: str
    hw_ver: str
    hostname: str


class AuthResponse(BaseModel):
    """Authentication response with JWT token."""

    token: str
    user: str
    expires_in: int


class CommandRequest(BaseModel):
    """Request model for sending commands to the machine."""

    type_message: str = "set_parameters"
    speed: Speed
    flowIn: bool
    flowOut: bool


class CommandResponse(BaseModel):
    """Response from a command execution."""

    status: str
    speed: Speed
    flowIn: bool
    flowOut: bool
