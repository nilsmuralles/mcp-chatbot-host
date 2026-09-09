# chatbot-host

A chatbot, backed by an Anthropic LLM, that connects
to multiple [Model Context Protocol](https://modelcontextprotocol.io) (MCP) servers, 
official ones (Filesystem, Git), a custom local one (a Design System assistant, in the
sibling repo [`mcp-design-system-server`](../mcp-design-system-server)), and a remote one
and exposes a Web UI for chatting with it.

## Features

| Feature | Where | Description |
|---|---|---|
| LLM API connection | `app/llm_client.py` | Sends prompts to Claude via the Anthropic API and returns the response. |
| Session context | `app/session.py` (`ChatSession`) | Keeps the full conversation history so follow-up questions ("when was he born?") resolve correctly. |
| MCP interaction log | `app/interaction_log.py` | Logs every request/response exchanged with any connected MCP server, to the console and to `logs/<timestamp>.jsonl`. |
| Filesystem + Git MCP | `app/mcp_clients.py`, `scripts/chat_with_mcp.py` | Connects the official Filesystem and Git MCP servers, sandboxed to `workspace/`, so the chatbot can create files, init a repo, commit, etc. |
| Design System MCP | `app/agent_session.py` (`AgentSession`) | Connects the custom `mcp-design-system-server` to query/analyze a Design System (colors, typography, spacing, accessibility). |
| Remote MCP client | `scripts/chat_with_remote_mcp.py` | A Streamable HTTP client for a remote MCP server (see [`remote-mcp-server`](../remote-mcp-server)). Code is ready; the Worker is not deployed yet. |
| Classmates' MCP servers | `scripts/chat_with_classmates_mcp.py` | Connects two MCP servers built by classmates for this same course project — `restaurant-mcp-server` (Go) and `mcp_f1_strategy` (Python) — cloned into `external-mcps/`. |
| Web UI | `web/` | A chat interface built with Vite + React + shadcn/ui, talking to a FastAPI backend. |
| Connectors tab | `web/src/Connectors.tsx`, `/api/connectors` | Add or remove extra MCP servers (local or remote) from the browser, on top of the 3 core ones — no restart, no code changes. Persisted in `mcp_servers.json`. |
| Logs tab | `web/src/Logs.tsx`, `/api/logs` | Browse every MCP request/response ever recorded, straight from `logs/*.jsonl`. |

## Installation

Requires Python 3.10+ and Node.js (only needed for the Filesystem MCP server, which runs
via `npx`).

```bash
git clone <this-repo-url>
cd chatbot-host
python3 -m venv venv
source venv/bin/activate   # on Windows (not WSL): venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY (see Troubleshooting below if the API call fails
# with a credit-balance error — that's a billing issue, not a bug)
```

## Usage

Each script under `scripts/` is a standalone way to exercise one feature:

```bash
python scripts/test_llm_connection.py "who was Alan Turing?"   # basic API connection
python scripts/chat_session.py                                  # interactive chat with session context
python scripts/demo_interaction_log.py                          # sanity-checks the log format with fake data
python scripts/chat_with_mcp.py                                 # chat with Filesystem + Git MCP tools
python scripts/chat_with_remote_mcp.py                          # chat with the remote MCP server (needs REMOTE_MCP_URL in .env)
python scripts/chat_with_classmates_mcp.py                      # chat with the classmates' MCP servers (see below)
```

`chat_with_classmates_mcp.py` needs both external servers set up first:

```bash
mkdir -p external-mcps && cd external-mcps

git clone https://github.com/DiegoOF07/restaurant-mcp-server.git
(cd restaurant-mcp-server && go build -o bin/restaurant-mcp-server ./cmd/server)  # needs Go 1.25+

git clone https://github.com/Branuvg/mcp_f1_strategy.git
(cd mcp_f1_strategy && uv sync)  # needs uv; see that repo's README for a pip-only fallback
```

Both defaults assume this exact layout (`external-mcps/<repo>/...`); override with
`RESTAURANT_MCP_SERVER_PATH` / `F1_MCP_SERVER_PATH` in `.env` if you put them elsewhere.

To run the full Web UI (chat with Filesystem, Git, and the Design System MCP server all
connected):

```bash
# terminal 1 — backend
python scripts/run_web.py

# terminal 2 — frontend
cd web
npm install
npm run dev
```

Then open the URL Vite prints (typically `http://localhost:5173`).

## Troubleshooting

**Windows + WSL**: pick one environment and stick to it for both installing and running.
If you install dependencies (`pip install`, `npm install`) using Windows' Python/Node but
then run the scripts from a WSL terminal (or vice versa), the dependencies won't be found
— WSL and Windows have completely separate Python/Node installations and package
directories, even though they share the same filesystem. Run every command in this README
from the same shell (all inside WSL, or all inside Windows PowerShell/cmd) — don't mix.

**"Your credit balance is too low"**: this is a real Anthropic API billing error, not a
bug — the API credit is separate from any Claude.ai/Claude Pro subscription. Check
[console.anthropic.com](https://console.anthropic.com) → Billing.

## Project structure

```
chatbot-host/
  app/
    llm_client.py        # thin Anthropic API wrapper
    session.py            # ChatSession — context, no tools
    agent_session.py       # AgentSession — context + MCP tool-use loop
    mcp_clients.py          # MCPServerClient (stdio) / RemoteMCPServerClient (HTTP)
    interaction_log.py      # MCP request/response logging
    web.py                   # FastAPI backend for the Web UI
  scripts/                    # standalone demos, one per feature (see Usage above)
  web/                          # Vite + React + shadcn/ui frontend
  workspace/                     # sandbox used by the Filesystem/Git MCP demo (gitignored)
  logs/                            # persisted interaction logs (gitignored)
  external-mcps/                    # classmates' MCP servers, cloned locally (gitignored)
```
