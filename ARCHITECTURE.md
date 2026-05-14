# Architecture

> **This file is maintained automatically by the AI. Do not edit manually unless correcting an error. The only field you need to fill in is the Project Description below — the AI derives or grows everything else.**

> **Scope:** Fullstack project — a frontend and a backend application living alongside each other. Single source of truth for both sides, including the contract between them.

---

## Project Description

<!--
Paste a one-line or one-paragraph description of what you're building.
Example: "A task manager with a React web app and a Node REST API, for solo freelancers tracking client work."
The AI reads this on the first session and fills in Project + Applications below automatically.
-->

A proof-of-concept AI ticket triage system: a FastAPI backend that accepts a customer support ticket via HTTP, runs a Claude agentic loop with three structured tools (classify, score sentiment, draft reply), retrieves relevant SOPs via in-memory cosine search (Ollama embeddings), and returns a fully structured JSON response — deployed on Fly.io for the client to curl and pressure-test.

---

## Project

_Auto-filled by the AI from the Project Description on the first session. The AI will confirm these with you before proceeding._

- **Name:** Triage POC
- **Type:** Backend-only REST API (no frontend in this POC)
- **Purpose:** Prove that a Claude tool-calling loop can classify, score, and draft replies to customer support tickets using SOP retrieval
- **Target Users:** Internal (engineer + client pressure-testing the live URL)
- **Stage:** Prototype / POC
- **Repo Layout:** Single repo — `app/` (backend), `sops/` (content), `tests/` (regression), project root (config)

---

## Applications

_Auto-filled by the AI on the first session from the Project Description. Confirmed with the user before any scaffolding._

### Frontend
- **Location:** none (out of scope for POC)
- **Kind:** none
- **Purpose:** N/A — client interacts directly via curl / Postman

### Backend
- **Location:** `./app/`
- **Kind:** REST API (FastAPI + Uvicorn)
- **Purpose:** Accept ticket payload → retrieve SOPs → run Claude agentic loop → return structured triage result

### Shared Code
- **Location:** none
- **Contents:** N/A — single-side project

---

## Tech Stack

_Filled in as decisions are made. Each side has its own table because stacks diverge._

### Frontend
_None — POC is backend-only._

### Backend
| Layer | Choice | Version | Notes |
| ----- | ------ | ------- | ----- |
| Language | Python | 3.12 | Pinned in pyproject.toml |
| Framework | FastAPI | ≥0.115 | Async, Pydantic v2, auto OpenAPI |
| LLM (primary) | gemma4:e4b | via Ollama | Self-hosted, tool-calling capable |
| LLM (fallback) | gemma3:4b | via Ollama | Available but does NOT support tools |
| Embeddings | nomic-embed-text | via Ollama | 768-dim, self-hosted, no data egress |
| Retrieval | In-memory cosine | numpy ≥1.26 | O(n) over 5 SOPs — no DB needed |
| Web server | Uvicorn | ≥0.30 | Standard FastAPI runtime |
| Logging | structlog | ≥24.2 | JSON to stdout |

### Shared / Tooling
| Layer | Choice | Version | Notes |
| ----- | ------ | ------- | ----- |
| Package manager | uv | latest | Lockfile via uv.lock |
| Hosting | Fly.io free tier | — | Buildpack-based, no Dockerfile |
| Secrets (local) | .env + python-dotenv | ≥1.0 | gitignored |
| Secrets (deploy) | Fly.io secrets | — | Never in repo |

---

## Dependencies

_Tracked as packages are added. Keep in sync with lockfiles._

### Frontend
| Package | Purpose | Added |
| ------- | ------- | ----- |

### Backend
| Package | Purpose | Added |
| ------- | ------- | ----- |
| fastapi | HTTP framework | M0 |
| uvicorn[standard] | ASGI server | M0 |
| pydantic + pydantic-settings | Schemas + env var loading | M0 |
| httpx | Ollama embed + LLM HTTP calls | M0 |
| numpy | Cosine similarity over embeddings | M0 |
| python-frontmatter | Parse SOP YAML frontmatter | M0 |
| structlog | JSON structured logging | M0 |
| python-dotenv | .env loading for local dev | M0 |
| email-validator | EmailStr validation in Pydantic | M0 |
| pytest + pytest-asyncio | Test suite | M5 |

### Shared
| Package | Purpose | Added |
| ------- | ------- | ----- |

---

## File Structure

_Updated as files and directories are added._

```
triage-poc/
├── pyproject.toml          # deps + Python 3.12 pin
├── Procfile                # web: uvicorn app.main:app ...
├── .env.example            # env var template (committed)
├── .env                    # actual values (gitignored)
├── .gitignore
├── BUILD_MILESTONES.md     # milestone plan + verification gates
├── POC_BUILD_PLAN.md       # authoritative spec
├── ARCHITECTURE.md         # this file
├── CLAUDE.md               # AI behaviour guidelines
│
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app, /health, /triage, /debug/sops
│   ├── config.py           # Pydantic Settings — env loading
│   ├── logging_setup.py    # structlog JSON config
│   ├── schemas.py          # TicketIn, ToolCall, SopChunk, TriageResponse
│   ├── retrieval.py        # SOP loader + nomic-embed cosine search
│   ├── tools.py            # 3 tool JSON schemas (OpenAI/Ollama format)
│   ├── prompts.py          # build_system_prompt(ticket, sops)
│   └── claude_loop.py      # run_loop via httpx → Ollama /api/chat
│
├── sops/
│   ├── sop-refund-001.md
│   ├── sop-billing-002.md
│   ├── sop-account-003.md
│   ├── sop-shipping-004.md
│   └── sop-general-005.md
│
└── tests/
    ├── test_health.py
    ├── test_tools_schema.py
    └── test_triage_smoke.py
```

---

## Architecture Overview

_Describe the end-to-end flow: browser/client → frontend → network → backend → data store. Note where auth, caching, and validation happen. A mermaid or ASCII diagram is welcome once there's enough to show._

---

## API Contract

_The interface between frontend and backend — the most important section of this file. Every shape the frontend depends on belongs here._

- **Protocol:** REST + JSON
- **Base URL (dev):** `http://localhost:8080`
- **Base URL (prod):** `https://triage-poc.fly.dev` (set at M6)
- **Versioning strategy:** none (POC; versioning deferred to Phase 1)
- **Schema source of truth:** Pydantic models in `app/schemas.py`; auto-published at `/docs`

### Endpoints / Operations

| Path / Op | Method | Purpose | Request | Response | Auth | FE Callers | Added |
| --------- | ------ | ------- | ------- | -------- | ---- | ---------- | ----- |
| `/health` | GET | Liveness check | — | `{status:"ok"}` | None | None | M0 |
| `/triage` | POST | Full triage pipeline | `TicketIn` | `TriageResponse` | None (POC) | None | M1 stub / M4 live |
| `/debug/sops` | GET | Dev: list loaded SOPs | — | `[{id,title}]` | None | None | M2 (remove pre-deploy) |

### Real-time / Events

_If WebSockets, SSE, or pub/sub are used, list channels and event shapes here._

---

## Data Models

_Source-of-truth models. Note where each lives: backend-only, shared package, or frontend view model. Keep server models and UI models distinct — don't let one leak into the other._

---

## State Ownership

_What lives where. Prevents duplication and drift._

- **Server state** (source of truth in the backend): [PLACEHOLDER]
- **Client state** (ephemeral UI state): [PLACEHOLDER]
- **URL state** (shareable, bookmarkable): [PLACEHOLDER]
- **Local persistence** (cookies, localStorage, device storage): [PLACEHOLDER]

---

## Auth Flow

_How identity flows across the boundary. Fill in as auth is wired up._

- **Mechanism:** [PLACEHOLDER] [e.g. JWT, session cookies, OAuth, magic link]
- **Token storage (FE):** [PLACEHOLDER]
- **Token lifetime / refresh:** [PLACEHOLDER]
- **Logout semantics:** [PLACEHOLDER]
- **Protected route convention:** [PLACEHOLDER]

---

## Error Contract

_How errors are shaped server-side and handled client-side. A stable error shape prevents UI bugs on every new failure mode._

- **Error response shape:** [PLACEHOLDER — e.g. `{ code, message, details? }`]
- **HTTP status convention:** [PLACEHOLDER]
- **FE handling strategy:** [PLACEHOLDER — e.g. toast for 4xx, boundary for 5xx]
- **Correlation ID / tracing:** [PLACEHOLDER]

---

## Key Design Decisions

_Added as decisions are made. Tag each with its scope: [FE] / [BE] / [CONTRACT] / [INFRA] / [BOTH]._

---

## Environment Variables

_Never commit actual values. Mark which side consumes each._

### Frontend
_None — POC is backend-only._

### Backend
| Variable | Purpose | Required | Default |
| -------- | ------- | -------- | ------- |
| `OLLAMA_BASE_URL` | Base URL of self-hosted Ollama | Yes | — |
| `OLLAMA_EMBED_MODEL` | Embedding model (nomic-embed-text) | Yes | — |
| `OLLAMA_LLM_MODEL` | Tool-calling LLM (gemma4:e4b) | Yes | — |

---

## External Integrations

_Added as services are connected. Note which side consumes each — some integrations belong on the server only (never expose their keys to the client)._

| Service | Consumed by | Purpose | Auth | Failure Mode |
| ------- | ----------- | ------- | ---- | ------------ |

---

## Testing Strategy

_Filled in as test infra is set up. Fullstack testing has more layers than single-app._

- **Frontend unit / component:** [PLACEHOLDER]
- **Backend unit:** [PLACEHOLDER]
- **Backend integration (DB, external services):** [PLACEHOLDER]
- **Contract tests (FE ↔ BE shape agreement):** [PLACEHOLDER]
- **End-to-end (browser driving real stack):** [PLACEHOLDER]
- **How to run each locally + in CI:** [PLACEHOLDER]

---

## Local Development

_How to bring the whole stack up on a dev machine. Should be copy-pasteable._

- **Prereqs:** [PLACEHOLDER]
- **First-time setup:** [PLACEHOLDER]
- **Run backend:** [PLACEHOLDER — port, command]
- **Run frontend:** [PLACEHOLDER — port, command]
- **Dev proxy / CORS:** [PLACEHOLDER]
- **Seed data / test accounts:** [PLACEHOLDER]

---

## Deployment & Infrastructure

_Filled in as deployment takes shape. Coordination matters here — a backend deploy can break production clients if the contract changes._

- **Frontend hosting:** [PLACEHOLDER]
- **Backend hosting:** [PLACEHOLDER]
- **Database / storage:** [PLACEHOLDER]
- **CI/CD pipelines:** [PLACEHOLDER]
- **Release coupling:** [PLACEHOLDER — are FE and BE shipped together, or independently?]
- **Backward-compat policy:** [PLACEHOLDER — how a BE change avoids breaking old FE clients still in the wild]
- **Secrets management:** [PLACEHOLDER]
- **Rollback plan:** [PLACEHOLDER]

---

## Technical Debt

_Added as shortcuts are taken. Tag with [FE] / [BE] / [CONTRACT] / [INFRA]._

- [ ]

---

## Known Bugs

_Added as bugs are discovered. Tag with [FE] / [BE] / [CONTRACT] / [INFRA]. Move to changelog when fixed._

- [ ]

---

## Out of Scope

_Added as things are explicitly deferred._

- [ ]

---

## Changelog

_Updated every session with a one-line summary. Always include a scope tag so it's obvious which side changed._

**Scope tags:** `[FE]` frontend · `[BE]` backend · `[CONTRACT]` API/shared types · `[BOTH]` coordinated change · `[INFRA]` deployment/tooling · `[DOCS]` documentation only

| Date | Scope | Change |
| ---- | ----- | ------ |
| 2026-05-14 | [BE] | M0 complete — project skeleton, FastAPI /health, config, structlog, all deps installed |
| 2026-05-14 | [BE] | M1 complete — Pydantic schemas (TicketIn, TriageResponse), stub /triage endpoint |
| 2026-05-14 | [BE] | M2 complete — 5 SOPs authored, nomic-embed-text retrieval, top_k cosine search verified |
| 2026-05-14 | [BE] | M3 complete — tool schemas, system prompt, agentic loop; switched LLM from Anthropic to Ollama gemma4:e4b via /api/chat |
| 2026-05-14 | [BE] | M4 complete — /triage wired end-to-end; all §13 acceptance criteria pass incl. injection probe |
| 2026-05-14 | [BE] | M5 complete — 10 tests pass (health, tools schema, smoke with mocks); no network calls in test suite |
