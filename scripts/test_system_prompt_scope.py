"""Test real (sin mocks) del alcance del SYSTEM_PROMPT.

Levanta el servidor MCP real de Design System, arma una AgentSession con el
SYSTEM_PROMPT de producción y verifica:

1. Una pregunta de conocimiento general se responde normalmente (no se niega) y
   sin llamar tools.
2. Una pregunta sobre el design system del usuario sí dispara una tool del
   servidor `design-system`.
3. El log de interacciones registró la llamada MCP del caso 2 (request + response).

Uso: python scripts/test_system_prompt_scope.py
Requiere ANTHROPIC_API_KEY en el entorno / .env.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent_session import AgentSession
from app.interaction_log import log
from app.mcp_clients import MCPManager, MCPServerClient
from app.web import SYSTEM_PROMPT, DEFAULT_DESIGN_SYSTEM_SERVER_PATH

REFUSAL_MARKERS = (
    "no puedo ayudar",
    "no puedo responder",
    "solo puedo",
    "está fuera de",
    "fuera de mi alcance",
    "no está relacionad",
)


async def main() -> None:
    design_system = MCPServerClient(
        name="design-system",
        command=sys.executable,
        args=[str(DEFAULT_DESIGN_SYSTEM_SERVER_PATH)],
    )
    manager = MCPManager([design_system])
    await manager.connect_all()

    failures: list[str] = []
    try:
        # --- Caso 1: conocimiento general ---
        session = AgentSession(manager, system=SYSTEM_PROMPT)
        reply = await session.send("¿Quién es el presidente de Guatemala?")
        print(f"[1] reply: {reply!r}\n    tool_calls: {session.last_tool_calls}")
        low = reply.lower()
        if any(m in low for m in REFUSAL_MARKERS):
            failures.append("Caso 1: el modelo se negó a responder conocimiento general")
        if "arévalo" not in low and "arevalo" not in low:
            failures.append("Caso 1: la respuesta no menciona a Arévalo")
        if session.last_tool_calls:
            failures.append(f"Caso 1: llamó tools inesperadamente: {session.last_tool_calls}")

        # --- Caso 2: pregunta de design system ---
        session2 = AgentSession(manager, system=SYSTEM_PROMPT)
        reply2 = await session2.send(
            "¿Cuáles son los tokens de color de mi design system?"
        )
        print(f"[2] reply: {reply2!r}\n    tool_calls: {session2.last_tool_calls}")
        ds_calls = [c for c in session2.last_tool_calls if c["server"] == "design-system"]
        if not ds_calls:
            failures.append("Caso 2: no se llamó ninguna tool del servidor design-system")

        # --- Caso 3: log de interacciones ---
        entries = log.entries
        req = [e for e in entries if e.get("server") == "design-system" and e.get("direction") == "request"]
        resp = [e for e in entries if e.get("server") == "design-system" and e.get("direction") == "response"]
        print(f"[3] log entries design-system: {len(req)} request / {len(resp)} response")
        if not req or not resp:
            failures.append("Caso 3: el log no registró request+response de la llamada MCP")
    finally:
        await manager.close_all()

    if failures:
        print("\nFALLÓ:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nOK — los 3 casos pasaron")


if __name__ == "__main__":
    asyncio.run(main())
