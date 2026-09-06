import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

_client = None

def get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client

def ask(prompt: str) -> str:
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    response = get_client().messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Expected a text block, got '{block.type}'")
    return block.text
