import os

from app.llm_client import DEFAULT_MODEL, MAX_TOKENS, get_client

class ChatSession:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def send(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        response = get_client().messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            messages=self.messages,
        )
        reply = response.content[0].text
        self.messages.append({"role": "assistant", "content": reply})
        return reply
