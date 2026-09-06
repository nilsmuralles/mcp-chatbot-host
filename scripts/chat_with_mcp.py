import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent_session import AgentSession
from app.mcp_clients import MCPManager, MCPServerClient

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT / "workspace"

EXIT_WORDS = {"salir", "exit", "quit"}

async def main() -> None:
    WORKSPACE.mkdir(exist_ok=True)

    filesystem = MCPServerClient(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
    )
    git = MCPServerClient(
        name="git",
        command="mcp-server-git",
        args=["--repository", str(WORKSPACE)],
    )
    manager = MCPManager([filesystem, git])

    print("Conectando a los servidores MCP (filesystem, git)...")
    await manager.connect_all()
    print("Conectado. Tools disponibles:", ", ".join(t["name"] for t in manager.anthropic_tools()))
    print(f"Workspace: {WORKSPACE}")
    print("Chat con herramientas MCP — escribí 'salir' o Ctrl+C para terminar.\n")

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
