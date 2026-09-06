import os
from typing import cast

from anthropic.types import MessageParam, ToolParam

from app.llm_client import DEFAULT_MODEL, MAX_TOKENS, get_client
from app.mcp_clients import MCPManager

MAX_TOOL_ITERATIONS = 10

class AgentSession:
    def __init__(self, manager: MCPManager) -> None:
        self.manager = manager
        self.messages: list[dict] = []

    async def send(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        tools = self.manager.anthropic_tools()

        for _ in range(MAX_TOOL_ITERATIONS):
            response = get_client().messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                messages=cast(list[MessageParam], self.messages),
                tools=cast(list[ToolParam], tools),
            )
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return "".join(
                    block.text for block in response.content if block.type == "text"
                )

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                result_text = await self.manager.call(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    }
                )
            self.messages.append({"role": "user", "content": tool_results})

        return "(se alcanzó el límite de iteraciones de tools sin una respuesta final)"
