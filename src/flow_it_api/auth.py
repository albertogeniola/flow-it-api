"""Authentication management for the FlowIt VMC API."""

import time
from typing import Optional

import httpx

from .const import DEFAULT_USERNAME, TIMEOUT
from .exceptions import FlowItAuthError, FlowItConnectionError
from .models import AuthResponse


class Authenticator:
    """Handles JWT authentication and token lifecycle."""

    def __init__(
        self,
        host: str,
        password: str,
        username: str = DEFAULT_USERNAME,
        client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize the authenticator.

        :param host: Base URL of the VMC machine.
        :param password: API password.
        :param username: API username.
        :param client: Optional existing HTTPX async client.
        """
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self._client = client
        self._token: Optional[str] = None
        self._expires_at: float = 0

    @property
    def token(self) -> Optional[str]:
        """
        Return the current token if it is still valid.

        :return: Token string or None if expired or not set.
        """
        if self._token and time.time() < self._expires_at:
            return self._token
        return None

    async def login(self) -> str:
        """
        Login to the device and return the JWT token.

        :return: JWT token string.
        :raises FlowItAuthError: If credentials are invalid.
        :raises FlowItConnectionError: If connection fails.
        """
        url = f"{self.host}/auth"
        data = {"username": self.username, "password": self.password}

        own_client = False
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=TIMEOUT)
            own_client = True

        try:
            response = await self._client.post(url, json=data)
            if response.status_code == 401:
                raise FlowItAuthError("Invalid credentials")

            response.raise_for_status()
            auth_data = AuthResponse(**response.json())

            self._token = auth_data.token
            # Set expiration with a 30s buffer
            self._expires_at = time.time() + auth_data.expires_in - 30
            return self._token
        except httpx.HTTPError as e:
            raise FlowItConnectionError(f"Failed to connect to {url}: {e}") from e
        finally:
            if own_client:
                await self._client.aclose()
                self._client = None

    async def get_valid_token(self) -> str:
        """
        Return a valid token, logging in if necessary.

        :return: Valid JWT token string.
        """
        token = self.token
        if token:
            return token
        return await self.login()

    def invalidate_token(self) -> None:
        """Invalidate the current token forcing a re-login on next request."""
        self._token = None
        self._expires_at = 0
