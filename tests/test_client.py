import pytest

from flow_it_api.client import FlowItVMCMachine
from flow_it_api.const import Speed
from flow_it_api.models import MachineStatusResponse

from .test_models import SAMPLE_STATUS


@pytest.mark.asyncio
async def test_refresh_state(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="http://vmc.local/auth",
        json={"token": "fake", "user": "api", "expires_in": 600},
    )
    httpx_mock.add_response(
        method="GET", url="http://vmc.local/status", json=SAMPLE_STATUS
    )

    async with FlowItVMCMachine("http://vmc.local", "pass") as machine:
        state = await machine.refresh_state()
        assert state.mode.speed == Speed.AUTO
        assert machine.machine_state.mode.speed == Speed.AUTO


@pytest.mark.asyncio
async def test_send_command(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="http://vmc.local/auth",
        json={"token": "fake", "user": "api", "expires_in": 600},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://vmc.local/command",
        json={"status": "ok", "speed": "3", "flowIn": True, "flowOut": True},
    )

    async with FlowItVMCMachine("http://vmc.local", "pass") as machine:
        # Pre-populate state to test optimistic update
        machine._state = MachineStatusResponse(**SAMPLE_STATUS)

        resp = await machine.send_command(Speed.LEVEL_3, True, True)
        assert resp.speed == Speed.LEVEL_3
        assert machine.machine_state.mode.speed == Speed.LEVEL_3


@pytest.mark.asyncio
async def test_get_info(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="http://vmc.local/info",
        json={
            "model": "VMC_XX",
            "api_ver": "1.0.1",
            "fw_ver": "1.9.3 D",
            "hw_ver": "1.0.0",
            "hostname": "ABC12_flow_it_vmc_tcp.local",
        },
    )

    async with FlowItVMCMachine("http://vmc.local", "pass") as machine:
        info = await machine.get_info()
        assert info.model == "VMC_XX"
        assert info.fw_ver == "1.9.3 D"
