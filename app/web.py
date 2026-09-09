import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.agent_session import AgentSession
from app.interaction_log import LOGS_DIR
from app.mcp_clients import MCPManager, MCPServerClient
from app.mcp_config import ConnectorEntry, build_client, load_config, save_config

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT / "workspace"
DEFAULT_DESIGN_SYSTEM_SERVER_PATH = (
    REPO_ROOT.parent / "mcp-design-system-server" / "app" / "server.py"
)

CORE_SERVER_NAMES = {"filesystem", "git", "design-system"}

SYSTEM_PROMPT = (
    f"El directorio de trabajo para las herramientas de filesystem y git es: "
    f"{WORKSPACE}. Usalo como repo_path/path en cada tool call, salvo que el "
    f"usuario pida explícitamente otra ubicación.\n\n"
    f"Para cualquier pregunta sobre colores, tipografía, espaciado, componentes de UI, "
    f"accesibilidad de una interfaz, o generación de código de un componente, usá "
    f"siempre las tools del servidor design-system en vez de responder con conocimiento "
    f"genérico — son la fuente de verdad del design system real del usuario, no una "
    f"convención genérica de otro framework."
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

    connector_entries: dict[str, ConnectorEntry] = {}
    for entry in load_config():
        client = build_client(entry)
        await manager.add_client(client)
        connector_entries[entry["name"]] = entry

    app.state.manager = manager
    app.state.connector_entries = connector_entries
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
    tool_calls: list[dict] = []

@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    reply = await app.state.session.send(request.message)
    return ChatResponse(reply=reply, tool_calls=app.state.session.last_tool_calls)

class ConnectorIn(BaseModel):
    name: str
    transport: str  # "stdio" | "http"
    command: str | None = None
    args: list[str] = []
    cwd: str | None = None
    env: dict[str, str] | None = None
    url: str | None = None

@app.get("/api/connectors")
def list_connectors() -> list[dict]:
    return [
        {"name": name, "transport": entry["transport"]}
        for name, entry in app.state.connector_entries.items()
    ]

@app.post("/api/connectors")
async def add_connector(connector: ConnectorIn) -> dict:
    if connector.name in CORE_SERVER_NAMES:
        raise HTTPException(400, f"'{connector.name}' is a core server, not a connector")
    if connector.name in app.state.connector_entries:
        raise HTTPException(400, f"A connector named '{connector.name}' already exists")

    entry: ConnectorEntry = connector.model_dump(exclude_none=True)
    client = build_client(entry)
    try:
        await app.state.manager.add_client(client)
    except BaseException as exc:
        attempted = (
            f"command={entry.get('command')!r} args={entry.get('args')!r}"
            if entry["transport"] == "stdio"
            else f"url={entry.get('url')!r}"
        )
        # anyio agrupa el error real dentro de un ExceptionGroup cuyo str() es solo
        # "unhandled errors in a TaskGroup" — sin desenvolverlo, el mensaje no dice nada
        # útil para diagnosticar (nos pasó de verdad con el conector remoto).
        real_exc = exc
        while isinstance(real_exc, BaseExceptionGroup) and len(real_exc.exceptions) == 1:
            real_exc = real_exc.exceptions[0]
        raise HTTPException(400, f"Could not connect ({attempted}): {real_exc!r}") from exc

    app.state.connector_entries[connector.name] = entry
    save_config(list(app.state.connector_entries.values()))
    return {"name": connector.name, "transport": connector.transport}

@app.delete("/api/connectors/{name}")
async def delete_connector(name: str) -> dict:
    if name not in app.state.connector_entries:
        raise HTTPException(404, f"No connector named '{name}'")
    await app.state.manager.remove_client(name)
    del app.state.connector_entries[name]
    save_config(list(app.state.connector_entries.values()))
    return {"deleted": name}

@app.get("/api/logs")
def get_logs() -> list[dict]:
    entries = []
    if LOGS_DIR.exists():
        for path in sorted(LOGS_DIR.glob("*.jsonl")):
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    entry["session"] = path.stem
                    entries.append(entry)
    entries.sort(key=lambda e: e["timestamp"])
    return entries
