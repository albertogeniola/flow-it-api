"""WebSocket client for the FlowIt VMC API."""

import asyncio
import json
import logging
from typing import Awaitable, Callable, Optional

import websockets

from .auth import Authenticator
from .models import MachineData, MachineStatusResponse

_LOGGER = logging.getLogger(__name__)


class FlowItWebSocket:
    """Handles real-time updates from the VMC machine via WebSocket."""

    def __init__(
        self,
        host: str,
        auth: Authenticator,
        on_data: Optional[Callable[[MachineData], Awaitable[None]]] = None,
    ):
        """
        Initialize the WebSocket client.

        :param host: Base URL of the VMC machine.
        :param auth: Authenticator instance for token management.
        :param on_data: Optional async callback for received data.
        """
        self.host = (
            host.replace("http://", "ws://").replace("https://", "wss://").rstrip("/")
        )
        self._auth = auth
        self._callbacks: list[Callable[[MachineData], Awaitable[None]]] = []
        if on_data is not None:
            self._callbacks.append(on_data)
        self._stop = False
        self._task: Optional[asyncio.Task] = None

    def register_callback(
        self, callback: Callable[[MachineData], Awaitable[None]]
    ) -> Callable[[], None]:
        """
        Register a callback to be called when new data is received via websocket.

        :param callback: Async function to call with the new MachineData.
        :return: A function that can be called to unregister the callback.
        """
        self._callbacks.append(callback)

        def unregister() -> None:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return unregister

    async def listen(self) -> None:
        """
        Start the websocket listener loop.

        Handles reconnection and authentication automatically.
        """
        url = f"{self.host}/ws"

        while not self._stop:
            try:
                token = await self._auth.get_valid_token()
                headers = {"Authorization": f"Bearer {token}"}

                async with websockets.connect(url, additional_headers=headers) as ws:
                    _LOGGER.info("Connected to WebSocket: %s", url)
                    async for message in ws:
                        if self._stop:
                            break

                        try:
                            data_dict = json.loads(message)
                            # The WS might send the full MachineStatusResponse or just MachineData
                            # Based on specs, it's usually the full status
                            status = MachineStatusResponse(**data_dict)
                            for callback in self._callbacks:
                                await callback(status.data)
                        except Exception as e:
                            _LOGGER.error("Failed to parse WebSocket message: %s", e)

            except (websockets.ConnectionClosed, OSError) as e:
                if not self._stop:
                    _LOGGER.warning("WebSocket connection lost, retrying in 5s: %s", e)
                    await asyncio.sleep(5)
            except Exception as e:
                if not self._stop:
                    _LOGGER.error("WebSocket unexpected error: %s", e)
                    await asyncio.sleep(5)

    def start(self) -> None:
        """Start the websocket listener in a background task."""
        self._stop = False
        self._task = asyncio.create_task(self.listen())

    async def stop(self) -> None:
        """Stop the websocket listener and cancel the task."""
        self._stop = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
