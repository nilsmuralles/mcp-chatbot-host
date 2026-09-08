import json
from pathlib import Path
from typing import Any

from app.mcp_clients import MCPServerClient, RemoteMCPServerClient, _BaseMCPClient

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "mcp_servers.json"

ConnectorEntry = dict[str, Any]

def load_config() -> list[ConnectorEntry]:
    if not CONFIG_PATH.exists():
        return []
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)

def save_config(entries: list[ConnectorEntry]) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

def build_client(entry: ConnectorEntry) -> _BaseMCPClient:
    if entry["transport"] == "stdio":
        return MCPServerClient(
            name=entry["name"],
            command=entry["command"],
            args=entry.get("args", []),
            cwd=entry.get("cwd"),
            env=entry.get("env"),
        )
    if entry["transport"] == "http":
        return RemoteMCPServerClient(name=entry["name"], url=entry["url"])
    raise ValueError(f"Unknown transport: {entry['transport']!r}")
