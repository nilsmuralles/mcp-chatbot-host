import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.session import ChatSession

EXIT_WORDS = {"salir", "exit", "quit"}

def main() -> None:
    session = ChatSession()
    print("Chat interactivo escribir 'salir' o Ctrl+C para terminar.\n")
    while True:
        try:
            prompt = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if prompt.strip().lower() in EXIT_WORDS:
            break
        print(session.send(prompt), "\n")

if __name__ == "__main__":
    main()
