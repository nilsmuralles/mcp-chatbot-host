import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from app.agent_session import AgentSession
from app.mcp_clients import MCPManager, MCPServerClient

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_MCPS = REPO_ROOT / "external-mcps"

DEFAULT_RESTAURANT_PATH = EXTERNAL_MCPS / "restaurant-mcp-server" / "bin" / "restaurant-mcp-server"
DEFAULT_F1_REPO_PATH = EXTERNAL_MCPS / "mcp_f1_strategy"

EXIT_WORDS = {"salir", "exit", "quit"}

async def main() -> None:
    load_dotenv()

    restaurant_path = os.environ.get("RESTAURANT_MCP_SERVER_PATH", str(DEFAULT_RESTAURANT_PATH))
    f1_repo_path = os.environ.get("F1_MCP_SERVER_PATH", str(DEFAULT_F1_REPO_PATH))

    restaurant = MCPServerClient(
        name="restaurant",
        command=restaurant_path,
        args=[],
        env={"MCP_USER_ROLE": "admin", "MCP_USER_ID": "demo-chatbot-host"},
    )
    f1 = MCPServerClient(
        name="f1-strategy",
        command="uv",
        args=[
            "run",
            "--project", f1_repo_path,
            "python", str(Path(f1_repo_path) / "src" / "server.py"),
        ],
    )
    manager = MCPManager([restaurant, f1])

    print("Conectando a los servidores MCP de compañeros (restaurant, f1-strategy)...")
    await manager.connect_all()
    print("Conectado. Tools disponibles:", ", ".join(t["name"] for t in manager.anthropic_tools()))
    print("Chat con MCPs de compañeros — escribí 'salir' o Ctrl+C para terminar.\n")

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
