import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"

type LogEntry = {
  timestamp: string
  server: string
  direction: "request" | "response"
  method: string
  payload: unknown
  session: string
}

async function fetchLogs(): Promise<LogEntry[]> {
  const response = await fetch("/api/logs")
  return response.json()
}

export default function Logs() {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)

  async function refresh() {
    setIsLoading(true)
    setEntries(await fetchLogs())
    setIsLoading(false)
  }

  useEffect(() => {
    refresh()
  }, [])

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Interaction log</h1>
        <Button variant="outline" size="sm" onClick={refresh} disabled={isLoading}>
          {isLoading ? "Cargando…" : "Refrescar"}
        </Button>
      </div>
      <p className="text-sm text-muted-foreground">
        Todas las solicitudes y respuestas JSON-RPC intercambiadas con los servidores MCP,
        leídas de <code>logs/*.jsonl</code>.
      </p>

      <div className="flex flex-col gap-2">
        {entries.length === 0 && !isLoading && (
          <p className="text-sm text-muted-foreground">No hay interacciones registradas todavía.</p>
        )}
        {[...entries].reverse().map((entry, i) => (
          <div key={i} className="rounded-lg border p-3 text-xs">
            <div className="mb-1 flex flex-wrap items-center gap-2 text-muted-foreground">
              <span>{new Date(entry.timestamp).toLocaleString()}</span>
              <span
                className={
                  entry.direction === "request"
                    ? "rounded bg-blue-600 px-1.5 py-0.5 text-white"
                    : "rounded bg-green-700 px-1.5 py-0.5 text-white"
                }
              >
                {entry.direction === "request" ? "→ REQUEST" : "← RESPONSE"}
              </span>
              <strong className="text-foreground">{entry.server}</strong>
              <span>{entry.method}</span>
              <span className="ml-auto">{entry.session}</span>
            </div>
            <pre className="overflow-x-auto whitespace-pre-wrap break-all rounded bg-muted p-2">
              {JSON.stringify(entry.payload, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  )
}
