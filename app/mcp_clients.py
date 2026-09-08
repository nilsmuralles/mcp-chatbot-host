import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from app.interaction_log import log

class _BaseMCPClient:
    def __init__(self, name: str) -> None:
        self.name = name
        self._session: ClientSession | None = None
        self.tools: list = []
        self._ready = asyncio.Event()
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._error: BaseException | None = None

    def _open_transport(self):
        raise NotImplementedError

    async def connect(self) -> None:
        self._task = asyncio.create_task(self._run())
        await self._ready.wait()
        if self._error is not None:
            raise self._error

    async def _run(self) -> None:
        try:
            async with self._open_transport() as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    self.tools = result.tools
                    self._session = session
                    self._ready.set()
                    await self._stop.wait()
        except BaseException as exc:
            self._error = exc
            self._ready.set()

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        assert self._session is not None, f"MCPServerClient '{self.name}' not connected"
        log.record(
            server=self.name,
            direction="request",
            method="tools/call",
            payload={"name": tool_name, "arguments": arguments},
        )
        result = await self._session.call_tool(tool_name, arguments)
        text = "\n".join(
            block.text for block in result.content if block.type == "text"
        )

        if result.structuredContent:
            text = f"{text}\n{json.dumps(result.structuredContent, ensure_ascii=False)}".strip()
        log.record(
            server=self.name,
            direction="response",
            method="tools/call",
            payload={"name": tool_name, "isError": result.isError, "text": text},
        )
        return text

    async def close(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task

class MCPServerClient(_BaseMCPClient):
    def __init__(
        self,
        name: str,
        command: str,
        args: list[str],
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        super().__init__(name)
        self._params = StdioServerParameters(command=command, args=args, cwd=cwd, env=env)

    def _open_transport(self):
        return stdio_client(self._params)

class RemoteMCPServerClient(_BaseMCPClient):
    def __init__(self, name: str, url: str) -> None:
        super().__init__(name)
        self._url = url

    def _open_transport(self):
        return streamablehttp_client(self._url)

class MCPManager:
    def __init__(self, clients: list[_BaseMCPClient]) -> None:
        self.clients = {client.name: client for client in clients}

    async def connect_all(self) -> None:
        for client in self.clients.values():
            await client.connect()

    async def close_all(self) -> None:
        for client in self.clients.values():
            await client.close()

    async def add_client(self, client: _BaseMCPClient) -> None:
        await client.connect()
        self.clients[client.name] = client

    async def remove_client(self, name: str) -> None:
        client = self.clients.pop(name)
        await client.close()

    def anthropic_tools(self) -> list[dict]:
        tools = []
        for client in self.clients.values():
            for tool in client.tools:
                tools.append(
                    {
                        "name": f"{client.name}__{tool.name}",
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema,
                    }
                )
        return tools

    async def call(self, prefixed_name: str, arguments: dict) -> str:
        server_name, tool_name = prefixed_name.split("__", 1)
        return await self.clients[server_name].call_tool(tool_name, arguments)
