# FLOW-IT-API

A Python API library client for FlowIt VMC (Ventilazione Meccanica Controllata) machines.

This library provides a simple, asynchronous interface to interact with FlowIt VMC devices over a local network, supporting both REST API for commands/status and WebSockets for real-time updates.

## Context

FlowIt VMC devices use two fans to control airflow (Inflow and Outflow) and are equipped with multiple sensors (Temperature, Humidity, Pressure, IAQ). While these devices connect to FlowIt cloud services, they also expose a local LAN API for direct control.

## Installation

### Prerequisites
- Python 3.11 or higher

### Setup Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

For development:
```bash
pip install -e .[dev]
# Install pre-commit hooks
pre-commit install
```

## Usage

The library uses `httpx` for asynchronous HTTP requests and `websockets` for real-time updates.

### Basic Example

```python
import asyncio
import logging
from flow_it_api.client import FlowItVMCMachine
from flow_it_api.const import Speed

# Setup logging to see the library version and actions
logging.basicConfig(level=logging.INFO)

async def main():
    host = "http://192.168.1.50"
    # You can retrieve your API password from the device's menu using the on-board display
    password = "your_api_password"

    async with FlowItVMCMachine(host, password) as vmc:
        # Get device info (Model, FW version, etc.)
        info = await vmc.get_info()
        print(f"Device: {info.model}, FW: {info.fw_ver}")

        # Fetch initial state
        state = await vmc.refresh_state()
        print(f"Current Speed: {state.mode.speed}")
        print(f"Temperature: {state.mode.temperatureIn_celsius}°C")

        # Send a command
        await vmc.send_command(Speed.LEVEL_3, flow_in=True, flow_out=True)

if __name__ == "__main__":
    asyncio.run(main())
```

### Real-time Updates (WebSocket)

The library can listen for real-time updates pushed by the device:

```python
async def on_data(data):
    print(f"Update received! New IAQ: {data.mode.iaq}")

# Initialize machine and websocket
async with FlowItVMCMachine(host, password) as vmc:
    vmc.websocket._on_data = on_data
    vmc.websocket.start()
    # Keep the loop running to receive events
    await asyncio.sleep(60)
```

## Library Architecture

### Key Components

- **`FlowItVMCMachine`**: The primary entry point. Manages authentication, connection state, and coordination between REST and WebSocket clients.
- **`Authenticator`**: Handles JWT token acquisition and automatic renewal.
- **`FlowItWebSocket`**: Manages the persistent WebSocket connection and reconnection logic.
- **`Models`**: Pydantic models providing type-safe access to machine data, including automatic Kelvin-to-Celsius conversions.

### Features
- **Asynchronous**: Built on `asyncio`.
- **Automatic Auth**: Handles login and token refreshing transparently via decorators.
- **Type Safety**: Full Pydantic v2 model support.
- **Temperature Conversion**: Access temperatures in both Kelvin (raw) and Celsius (processed).
- **Comprehensive Logging**: Detailed internal logging for debugging, including version tracking at load time.
- **Dynamic Versioning**: Versioning is automatically managed via Git tags (VCS).

## Development

The project structure:
- `src/flow_it_api/`: Library source code (src layout).
- `tests/`: Unit tests (using `pytest`).
- `specs/`: OpenAPI/YAML specifications for the device API.
- `example.py`: A comprehensive CLI test client.

### Quality Control
This project uses several tools to ensure code quality:
- **Linting & Formatting**: `black`, `isort`, and `mypy` for type checking.
- **Git Hooks**: `pre-commit` is used to run all checks locally before every commit.
- **CI/CD**: GitHub Actions runs the full test suite across multiple Python versions and handles automated releases to PyPI.

To run tests locally:
```bash
pytest --cov=src --cov-report=term-missing
```
