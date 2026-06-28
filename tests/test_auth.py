import httpx
import pytest

from flow_it_api.auth import Authenticator
from flow_it_api.exceptions import FlowItAuthError


@pytest.mark.asyncio
async def test_login_success(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="http://vmc.local/auth",
        json={"token": "fake_token", "user": "api", "expires_in": 600},
    )

    auth = Authenticator("http://vmc.local", "password")
    token = await auth.login()

    assert token == "fake_token"
    assert auth.token == "fake_token"


@pytest.mark.asyncio
async def test_login_failure(httpx_mock):
    httpx_mock.add_response(method="POST", url="http://vmc.local/auth", status_code=401)

    auth = Authenticator("http://vmc.local", "wrong_password")
    with pytest.raises(FlowItAuthError):
        await auth.login()


@pytest.mark.asyncio
async def test_get_valid_token(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="http://vmc.local/auth",
        json={"token": "token1", "user": "api", "expires_in": 600},
    )

    auth = Authenticator("http://vmc.local", "password")

    # First call triggers login
    token1 = await auth.get_valid_token()
    assert token1 == "token1"

    # Second call returns cached token
    token2 = await auth.get_valid_token()
    assert token2 == "token1"

    assert len(httpx_mock.get_requests()) == 1
