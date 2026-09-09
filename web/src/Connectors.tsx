import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

type Connector = {
  name: string
  transport: "stdio" | "http"
}

const inputClass =
  "w-full rounded-md border bg-transparent px-3 py-1.5 text-sm outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"

async function fetchConnectors(): Promise<Connector[]> {
  const response = await fetch("/api/connectors")
  return response.json()
}

// Saca espacios y puntuación colgante típica de copiar/pegar (ej. el "." con el que
// termina una oración) que rompe rutas y URLs sin que se note a simple vista.
function cleanPastedValue(value: string): string {
  return value.trim().replace(/[.,;]+$/, "")
}

export default function Connectors() {
  const [connectors, setConnectors] = useState<Connector[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [name, setName] = useState("")
  const [transport, setTransport] = useState<"stdio" | "http">("stdio")
  const [command, setCommand] = useState("")
  const [args, setArgs] = useState("")
  const [cwd, setCwd] = useState("")
  const [env, setEnv] = useState("")
  const [url, setUrl] = useState("")

  useEffect(() => {
    refresh()
  }, [])

  async function refresh() {
    setConnectors(await fetchConnectors())
  }

  function resetForm() {
    setName("")
    setCommand("")
    setArgs("")
    setCwd("")
    setEnv("")
    setUrl("")
  }

  function parseEnv(text: string): Record<string, string> | undefined {
    const lines = text.split("\n").map((l) => l.trim()).filter(Boolean)
    if (lines.length === 0) return undefined
    const result: Record<string, string> = {}
    for (const line of lines) {
      const [key, ...rest] = line.split("=")
      if (key) result[key.trim()] = rest.join("=").trim()
    }
    return result
  }

  async function handleAdd() {
    setError(null)
    setIsSubmitting(true)
    try {
      const body =
        transport === "stdio"
          ? {
              name: name.trim(),
              transport,
              command: cleanPastedValue(command),
              args: args.split(",").map((a) => cleanPastedValue(a)).filter(Boolean),
              cwd: cwd.trim() ? cleanPastedValue(cwd) : undefined,
              env: parseEnv(env),
            }
          : { name: name.trim(), transport, url: cleanPastedValue(url) }

      const response = await fetch("/api/connectors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `Request failed: ${response.status}`)
      }
      resetForm()
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDelete(connectorName: string) {
    await fetch(`/api/connectors/${encodeURIComponent(connectorName)}`, { method: "DELETE" })
    await refresh()
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-4">
      <h1 className="text-lg font-semibold">Connectors</h1>
      <p className="text-sm text-muted-foreground">
        Servidores MCP extra, agregados en caliente sobre los 3 core (Filesystem, Git,
        Design System). Se persisten en <code>mcp_servers.json</code>.
      </p>

      <div className="flex flex-col gap-2 rounded-lg border p-3">
        {connectors.length === 0 && (
          <p className="text-sm text-muted-foreground">No hay connectors agregados todavía.</p>
        )}
        {connectors.map((c) => (
          <div key={c.name} className="flex items-center justify-between rounded-md border px-3 py-2">
            <span className="text-sm">
              <strong>{c.name}</strong> <span className="text-muted-foreground">({c.transport})</span>
            </span>
            <Button variant="outline" size="sm" onClick={() => handleDelete(c.name)}>
              Borrar
            </Button>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-3 rounded-lg border p-4">
        <h2 className="text-sm font-semibold">Agregar connector</h2>

        <input className={inputClass} placeholder="Nombre (ej. restaurant)" value={name} onChange={(e) => setName(e.target.value)} />

        <select
          className={inputClass}
          value={transport}
          onChange={(e) => setTransport(e.target.value as "stdio" | "http")}
        >
          <option value="stdio">stdio (servidor local)</option>
          <option value="http">http (servidor remoto)</option>
        </select>

        {transport === "stdio" ? (
          <>
            <input className={inputClass} placeholder="Comando (ej. /ruta/al/binario o uv)" value={command} onChange={(e) => setCommand(e.target.value)} />
            <input className={inputClass} placeholder="Args, separados por coma" value={args} onChange={(e) => setArgs(e.target.value)} />
            <input className={inputClass} placeholder="cwd (opcional)" value={cwd} onChange={(e) => setCwd(e.target.value)} />
            <Textarea
              className="min-h-16"
              placeholder={"Variables de entorno (opcional), una por línea: KEY=value"}
              value={env}
              onChange={(e) => setEnv(e.target.value)}
            />
          </>
        ) : (
          <input className={inputClass} placeholder="URL (ej. https://tu-worker.workers.dev/mcp)" value={url} onChange={(e) => setUrl(e.target.value)} />
        )}

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button onClick={handleAdd} disabled={isSubmitting || !name}>
          {isSubmitting ? "Conectando…" : "Agregar"}
        </Button>
      </div>
    </div>
  )
}
