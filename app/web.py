import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from app.agent_session import AgentSession
from app.mcp_clients import MCPManager, MCPServerClient

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT / "workspace"
DEFAULT_DESIGN_SYSTEM_SERVER_PATH = (
    REPO_ROOT.parent / "mcp-design-system-server" / "app" / "server.py"
)

SYSTEM_PROMPT = (
    f"El directorio de trabajo para las herramientas de filesystem y git es: "
    f"{WORKSPACE}. Usalo como repo_path/path en cada tool call, salvo que el "
    f"usuario pida explícitamente otra ubicación."
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    WORKSPACE.mkdir(exist_ok=True)

    design_system_server_path = os.environ.get(
        "DESIGN_SYSTEM_SERVER_PATH", str(DEFAULT_DESIGN_SYSTEM_SERVER_PATH)
    )

    filesystem = MCPServerClient(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
    )
    git = MCPServerClient(name="git", command="mcp-server-git", args=[])
    design_system = MCPServerClient(
        name="design-system", command=sys.executable, args=[design_system_server_path]
    )
    manager = MCPManager([filesystem, git, design_system])

    await manager.connect_all()
    app.state.session = AgentSession(manager, system=SYSTEM_PROMPT)
    try:
        yield
    finally:
        await manager.close_all()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    reply = await app.state.session.send(request.message)
    return ChatResponse(reply=reply)
