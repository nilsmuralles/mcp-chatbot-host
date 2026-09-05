import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm_client import ask

DEFAULT_PROMPT = "¿Quién fue Alan Turing?"

def main() -> None:
    prompt = " ".join(sys.argv[1:]) or DEFAULT_PROMPT
    print(f"> {prompt}\n")
    print(ask(prompt))

if __name__ == "__main__":
    main()
