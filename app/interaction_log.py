import json
from datetime import datetime
from pathlib import Path

ARROWS = {"request": "→ REQUEST ", "response": "← RESPONSE"}

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = REPO_ROOT / "logs"

class InteractionLog:
    def __init__(self) -> None:
        self.entries: list[dict] = []
        LOGS_DIR.mkdir(exist_ok=True)
        session_start = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self._log_path = LOGS_DIR / f"{session_start}.jsonl"

    def record(self, server: str, direction: str, method: str, payload: dict) -> None:
        entry = {
            "timestamp": datetime.now(),
            "server": server,
            "direction": direction,
            "method": method,
            "payload": payload,
        }
        self.entries.append(entry)
        self._print(entry)
        self._append_to_file(entry)

    def _print(self, entry: dict) -> None:
        arrow = ARROWS[entry["direction"]]
        ts = entry["timestamp"].strftime("%H:%M:%S")
        payload = json.dumps(entry["payload"], ensure_ascii=False)
        print(f"[{ts}] {arrow} ({entry['server']}) {entry['method']} {payload}")

    def _append_to_file(self, entry: dict) -> None:
        line = {**entry, "timestamp": entry["timestamp"].isoformat()}
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

log = InteractionLog()
