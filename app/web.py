from fastapi import FastAPI
from pydantic import BaseModel

from app.session import ChatSession

app = FastAPI()
session = ChatSession()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    reply = session.send(request.message)
    return ChatResponse(reply=reply)
