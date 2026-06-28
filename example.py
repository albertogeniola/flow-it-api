import argparse
import asyncio
import logging
import sys

from flow_it_api.client import FlowItVMCMachine
from flow_it_api.const import DEFAULT_USERNAME, Speed

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
_LOGGER = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="FlowIt VMC API Test Client")
    parser.add_argument(
        "host", help="IP or hostname of the VMC machine (e.g., http://192.168.1.50)"
    )
    parser.add_argument("password", help="API password from the machine's network menu")
    parser.add_argument(
        "--username",
        default=DEFAULT_USERNAME,
        help=f"API username (default: {DEFAULT_USERNAME})",
    )
    parser.add_argument(
        "--speed", choices=[s.value for s in Speed], help="Optionally set a new speed"
    )

    args = parser.parse_args()

    _LOGGER.info("Connecting to %s...", args.host)

    async with FlowItVMCMachine(args.host, args.password, args.username) as vmc:
        try:
            # 1. Get Basic Info. This api does not require any login.
            info = await vmc.get_info()
            _LOGGER.info(
                "Device Info: Model=%s, FW=%s, HW=%s",
                info.model,
                info.fw_ver,
                info.hw_ver,
            )

            # 2. Get Full Initial State
            state = await vmc.refresh_state()
            _LOGGER.info(
                "Initial State: Speed=%s, FlowIn=%s, FlowOut=%s",
                state.mode.speed,
                state.mode.flowIn,
                state.mode.flowOut,
            )
            _LOGGER.info(
                "Sensors: IAQ=%s, TempIn=%s°C (%s K), TempOut=%s°C (%s K)",
                state.mode.iaq,
                state.mode.temperatureIn_celsius,
                state.mode.temperatureIn,
                state.mode.temperatureOut_celsius,
                state.mode.temperatureOut,
            )

            # 3. Setup WebSocket for real-time updates
            async def on_ws_data(data):
                _LOGGER.info(
                    "WS Update -> Speed: %s, FlowIn: %s, FlowOut: %s, IAQ: %s, FilterS: %s",
                    data.mode.speed,
                    data.mode.flowIn,
                    data.mode.flowOut,
                    data.mode.iaq,
                    data.alert.filterS,
                )
                _LOGGER.info(
                    "WS Sensors -> TempIn: %s, HumIn: %s%%, TempOut: %s, HumOut: %s%%",
                    data.mode.temperatureIn,
                    data.mode.humidityIn,
                    data.mode.temperatureOut,
                    data.mode.humidityOut,
                )
                _LOGGER.info(
                    "WS Raw Sensors -> Sin: %s, Sout: %s, Iin: %s, Iout: %s",
                    data.sensors.Sin,
                    data.sensors.Sout,
                    data.sensors.Iin,
                    data.sensors.Iout,
                )

            vmc.websocket._on_data = on_ws_data
            vmc.websocket.start()
            _LOGGER.info("WebSocket listener started. Watching for changes...")

            # 4. Optionally Send a Command
            if args.speed:
                new_speed = Speed(args.speed)
                _LOGGER.info("Sending command: Set speed to %s", new_speed)
                await vmc.send_command(new_speed, flow_in=True, flow_out=True)
                _LOGGER.info("Command sent successfully.")

            # 5. Keep running to see WS updates
            _LOGGER.info("Press Ctrl+C to exit.")
            while True:
                await asyncio.sleep(1)

        except Exception as e:
            _LOGGER.error("An error occurred: %s", e)
        finally:
            _LOGGER.info("Shutting down...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
