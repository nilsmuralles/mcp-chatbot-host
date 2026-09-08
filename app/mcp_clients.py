from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from app.interaction_log import log

class _BaseMCPClient:
    def __init__(self, name: str) -> None:
        self.name = name
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self.tools: list = []

    async def connect(self) -> None:
        raise NotImplementedError

    async def _init_session(self, read, write) -> None:
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        result = await session.list_tools()
        self.tools = result.tools
        self._session = session

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
        log.record(
            server=self.name,
            direction="response",
            method="tools/call",
            payload={"name": tool_name, "isError": result.isError, "text": text},
        )
        return text

    async def close(self) -> None:
        await self._stack.aclose()

class MCPServerClient(_BaseMCPClient):
    def __init__(self, name: str, command: str, args: list[str]) -> None:
        super().__init__(name)
        self._params = StdioServerParameters(command=command, args=args)

    async def connect(self) -> None:
        read, write = await self._stack.enter_async_context(stdio_client(self._params))
        await self._init_session(read, write)

class RemoteMCPServerClient(_BaseMCPClient):
    def __init__(self, name: str, url: str) -> None:
        super().__init__(name)
        self._url = url

    async def connect(self) -> None:
        read, write, _ = await self._stack.enter_async_context(
            streamablehttp_client(self._url)
        )
        await self._init_session(read, write)

class MCPManager:
    def __init__(self, clients: list[_BaseMCPClient]) -> None:
        self.clients = {client.name: client for client in clients}

    async def connect_all(self) -> None:
        for client in self.clients.values():
            await client.connect()

    async def close_all(self) -> None:
        for client in self.clients.values():
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
