import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from app.agent_session import AgentSession
from app.mcp_clients import MCPManager, RemoteMCPServerClient

EXIT_WORDS = {"salir", "exit", "quit"}

async def main() -> None:
    load_dotenv()
    url = os.environ["REMOTE_MCP_URL"]

    remote = RemoteMCPServerClient(name="remote-demo", url=url)
    manager = MCPManager([remote])

    print(f"Conectando al servidor MCP remoto ({url})...")
    await manager.connect_all()
    print("Conectado. Tools disponibles:", ", ".join(t["name"] for t in manager.anthropic_tools()))
    print("Chat con el servidor MCP remoto — escribí 'salir' o Ctrl+C para terminar.\n")

    session = AgentSession(manager)
    try:
        while True:
            try:
                prompt = input("> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if prompt.strip().lower() in EXIT_WORDS:
                break
            reply = await session.send(prompt)
            print(reply, "\n")
    finally:
        await manager.close_all()

if __name__ == "__main__":
    asyncio.run(main())
