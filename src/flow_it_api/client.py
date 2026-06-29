"""Main client for interacting with the FlowIt VMC machine."""

from functools import wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar, cast

import httpx

from .auth import Authenticator
from .const import DEFAULT_USERNAME, TIMEOUT, Speed
from .exceptions import FlowItCommandError, FlowItConnectionError, FlowItResponseError
from .models import (
    CommandRequest,
    CommandResponse,
    MachineData,
    MachineInfoResponse,
    MachineStatusResponse,
)
from .websocket import FlowItWebSocket

F = TypeVar("F", bound=Callable[..., Any])


def authenticated(func: F) -> F:
    """
    Decorator to ensure the client is authenticated before calling a method.

    Automatically handles token refresh if a 401 Unauthorized is received.
    """

    @wraps(func)
    async def wrapper(self: "FlowItVMCMachine", *args: Any, **kwargs: Any) -> Any:
        token = await self._auth.get_valid_token()
        try:
            return await func(self, token, *args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self._auth.invalidate_token()
                token = await self._auth.get_valid_token()
                return await func(self, token, *args, **kwargs)
            raise

    return cast(F, wrapper)


class FlowItVMCMachine:
    """Primary API client for FlowIt VMC devices."""

    def __init__(
        self,
        host: str,
        password: str,
        username: str = DEFAULT_USERNAME,
        session: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize the VMC machine client.

        :param host: Base URL of the VMC machine.
        :param password: API password.
        :param username: API username.
        :param session: Optional existing HTTPX async client (session).
        """
        self.host = host.rstrip("/")
        self._session = session
        self._own_session = False
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=TIMEOUT)
            self._own_session = True

        self._auth = Authenticator(self.host, password, username, client=self._session)
        self._state: Optional[MachineStatusResponse] = None
        self._info: Optional[MachineInfoResponse] = None
        self._ws: Optional[FlowItWebSocket] = None

    @property
    def websocket(self) -> FlowItWebSocket:
        """
        Return the websocket client for real-time updates.

        :return: FlowItWebSocket instance.
        """
        if self._ws is None:
            self._ws = FlowItWebSocket(
                self.host, self._auth, on_data=self._async_handle_ws_data
            )
        return self._ws

    async def _async_handle_ws_data(self, data: MachineData) -> None:
        """
        Internal handler for data received from the websocket.

        :param data: Parsed machine data from the WS event.
        """
        if self._state:
            self._state.data = data
        else:
            # If we don't have a full state yet, we just initialize the data part
            # but we won't have the top-level fields like name, chrono_id, etc.
            # until a refresh_state is called.
            pass

    def register_websocket_callback(
        self, callback: Callable[[MachineData], Awaitable[None]]
    ) -> Callable[[], None]:
        """
        Register a callback to be invoked when new data is received via the websocket.

        :param callback: Async function taking MachineData as parameter.
        :return: A function that can be called to unregister the callback.
        """
        return self.websocket.register_callback(callback)

    @property
    def machine_state(self) -> Optional[MachineData]:
        """
        Return the current machine data if available.

        :return: MachineData or None.
        """
        if self._state:
            return self._state.data
        return None

    @property
    def state(self) -> Optional[MachineStatusResponse]:
        """
        Return the full current machine state including metadata.

        :return: MachineStatusResponse or None.
        """
        return self._state

    @property
    def is_connected(self) -> bool:
        """
        Return True if the client has successfully fetched the state.

        :return: Connection status boolean.
        """
        return self._state is not None

    @property
    def _http(self) -> httpx.AsyncClient:
        """Return the async client, ensuring it is initialized."""
        if self._session is None:
            # Fallback in case of unexpected state
            self._session = httpx.AsyncClient(timeout=TIMEOUT)
            self._own_session = True
        return self._session

    async def get_info(self) -> MachineInfoResponse:
        """
        Fetch basic machine information (Model, FW, HW versions).

        Does not require authentication.

        :return: MachineInfoResponse instance.
        :raises FlowItConnectionError: If connection fails.
        """
        url = f"{self.host}/info"
        try:
            response = await self._http.get(url)
            response.raise_for_status()
            self._info = MachineInfoResponse(**response.json())
            return self._info
        except httpx.HTTPError as e:
            raise FlowItConnectionError(f"Failed to fetch info: {e}") from e

    @authenticated
    async def refresh_state(self, token: str) -> MachineData:
        """
        Fetch the full machine state via REST API.

        :param token: JWT token (provided by @authenticated).
        :return: MachineData instance.
        :raises FlowItConnectionError: If connection fails.
        :raises FlowItResponseError: If parsing fails.
        """
        url = f"{self.host}/status"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = await self._http.get(url, headers=headers)
            response.raise_for_status()
            self._state = MachineStatusResponse(**response.json())
            return self._state.data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise
            raise FlowItConnectionError(f"Failed to refresh state: {e}") from e
        except httpx.HTTPError as e:
            raise FlowItConnectionError(f"Failed to refresh state: {e}") from e
        except Exception as e:
            raise FlowItResponseError(f"Failed to parse state response: {e}") from e

    @authenticated
    async def send_command(
        self, token: str, speed: Speed, flow_in: bool, flow_out: bool
    ) -> CommandResponse:
        """
        Send a command to update speed and flow settings.

        :param token: JWT token (provided by @authenticated).
        :param speed: Target fan speed level.
        :param flow_in: Enable/disable inflow.
        :param flow_out: Enable/disable outflow.
        :return: CommandResponse instance.
        :raises FlowItCommandError: If the command fails.
        """
        url = f"{self.host}/command"
        headers = {"Authorization": f"Bearer {token}"}

        command = CommandRequest(speed=speed, flowIn=flow_in, flowOut=flow_out)

        try:
            response = await self._http.post(
                url, json=command.model_dump(), headers=headers
            )
            response.raise_for_status()
            cmd_resp = CommandResponse(**response.json())

            # Optimistically update local state if we have one
            if self._state:
                self._state.data.mode.speed = cmd_resp.speed
                self._state.data.mode.flowIn = cmd_resp.flowIn
                self._state.data.mode.flowOut = cmd_resp.flowOut

            return cmd_resp
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise
            raise FlowItCommandError(f"Command failed: {e}") from e
        except httpx.HTTPError as e:
            raise FlowItCommandError(f"Command failed: {e}") from e

    async def close(self) -> None:
        """Close the underlying HTTP client (if owned) and stop websocket listener."""
        if self._ws:
            await self._ws.stop()
        if self._own_session and self._session:
            await self._session.aclose()

    async def __aenter__(self) -> "FlowItVMCMachine":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
