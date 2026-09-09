import { useState } from "react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"

import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller"
import { Message, MessageContent } from "@/components/ui/message"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import Connectors from "@/Connectors"
import Logs from "@/Logs"

type ChatMessage = {
  id: string
  role: "user" | "assistant"
  text: string
}

async function sendChatMessage(message: string): Promise<string> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  })
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  const data = await response.json()
  return data.reply as string
}

export default function App() {
  const [view, setView] = useState<"chat" | "connectors" | "logs">("chat")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [isSending, setIsSending] = useState(false)

  async function handleSend() {
    const text = input.trim()
    if (!text || isSending) return

    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", text }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsSending(true)

    try {
      const reply = await sendChatMessage(text)
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", text: reply },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: "Hubo un error contactando al servidor. Revisá la consola del backend.",
        },
      ])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="mx-auto flex h-svh w-full max-w-2xl flex-col p-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Design System Assistant</h1>
        <div className="flex gap-2">
          <Button variant={view === "chat" ? "default" : "outline"} size="sm" onClick={() => setView("chat")}>
            Chat
          </Button>
          <Button variant={view === "connectors" ? "default" : "outline"} size="sm" onClick={() => setView("connectors")}>
            Connectors
          </Button>
          <Button variant={view === "logs" ? "default" : "outline"} size="sm" onClick={() => setView("logs")}>
            Logs
          </Button>
        </div>
      </div>

      {view === "connectors" ? (
        <Connectors />
      ) : view === "logs" ? (
        <Logs />
      ) : (
        <>
      <MessageScrollerProvider autoScroll>
        <MessageScroller className="flex-1 rounded-lg border">
          <MessageScrollerViewport>
            <MessageScrollerContent className="flex flex-col gap-4 p-4">
              {messages.map((message) => (
                <MessageScrollerItem
                  key={message.id}
                  messageId={message.id}
                  scrollAnchor={message.role === "user"}
                >
                  <Message align={message.role === "user" ? "end" : "start"}>
                    <MessageContent>
                      {message.role === "assistant" ? (
                        <Bubble variant="outline">
                          <BubbleContent>
                            <div className="prose prose-sm max-w-none">
                              <Markdown remarkPlugins={[remarkGfm]}>{message.text}</Markdown>
                            </div>
                          </BubbleContent>
                        </Bubble>
                      ) : (
                        <Bubble className="*:data-[slot=bubble-content]:!bg-blue-600 *:data-[slot=bubble-content]:!text-white">
                          <BubbleContent>{message.text}</BubbleContent>
                        </Bubble>
                      )}
                    </MessageContent>
                  </Message>
                </MessageScrollerItem>
              ))}
              {isSending && (
                <Message align="start">
                  <MessageContent>
                    <Bubble variant="outline">
                      <BubbleContent className="shimmer">Pensando…</BubbleContent>
                    </Bubble>
                  </MessageContent>
                </Message>
              )}
            </MessageScrollerContent>
          </MessageScrollerViewport>
          <MessageScrollerButton />
        </MessageScroller>
      </MessageScrollerProvider>

      <div className="mt-4 flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="Preguntá algo sobre el Design System..."
          className="min-h-0 flex-1 resize-none"
          rows={1}
        />
        <Button onClick={handleSend} disabled={isSending}>
          Enviar
        </Button>
      </div>
        </>
      )}
    </div>
  )
}
