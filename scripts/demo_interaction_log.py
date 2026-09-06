import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.interaction_log import log

log.record(
    server="filesystem",
    direction="request",
    method="tools/call",
    payload={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "read_file", "arguments": {"path": "README.md"}}},
)

log.record(
    server="filesystem",
    direction="response",
    method="tools/call",
    payload={"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "# chatbot-host"}]}},
)
