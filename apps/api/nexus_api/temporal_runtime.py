from dataclasses import dataclass

from temporalio.client import Client

from nexus_api.config import get_settings


@dataclass(frozen=True)
class TemporalHandle:
    workflow_id: str
    run_id: str | None


class TemporalRuntime:
    def __init__(self, address: str | None = None) -> None:
        self.address = address or get_settings().temporal_address

    async def client(self) -> Client:
        return await Client.connect(self.address)

    async def describe_namespace(self) -> dict[str, str]:
        client = await self.client()
        return {"namespace": client.namespace, "address": self.address}

