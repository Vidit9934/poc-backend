import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from .claude_loop import run_loop
from .config import settings
from .logging_setup import configure_logging
from .retrieval import SOPS, load_sops, top_k
from .schemas import SopChunk, TicketIn, ToolCall, TriageResponse

configure_logging()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_sops()
    yield


app = FastAPI(title="Triage POC", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/debug/sops")
def debug_sops() -> list[dict]:
    return [{"id": s["id"], "title": s["title"]} for s in SOPS]


def _get(tool_calls: list[dict], name: str, key: str):
    for tc in tool_calls:
        if tc["tool"] == name:
            return tc["input"].get(key)
    return None


@app.post("/triage", response_model=TriageResponse)
async def triage(ticket: TicketIn) -> TriageResponse:
    run_id = str(uuid.uuid4())
    t0 = time.monotonic()
    log.info("triage_start", run_id=run_id, ticket_id=ticket.ticket_id)

    try:
        sops = top_k(ticket.subject + "\n" + ticket.body, k=3)
        calls_raw, draft = run_loop(ticket.model_dump(), sops)

        processing_ms = int((time.monotonic() - t0) * 1000)
        log.info(
            "triage_complete",
            run_id=run_id,
            processing_ms=processing_ms,
            tool_count=len(calls_raw),
        )

        return TriageResponse(
            ticket_id=ticket.ticket_id,
            processing_ms=processing_ms,
            model=f"ollama/{settings.ollama_llm_model}",
            tool_calls=[ToolCall(tool=c["tool"], input=c["input"]) for c in calls_raw],
            final_draft=draft.get("reply_md") if draft else None,
            classification=_get(calls_raw, "classify_ticket", "category"),
            sentiment_score=_get(calls_raw, "score_sentiment", "score"),
            sop_chunks_used=[SopChunk(id=s["id"], title=s["title"]) for s in sops],
        )
    except Exception as exc:
        processing_ms = int((time.monotonic() - t0) * 1000)
        log.error("triage_error", run_id=run_id, error=str(exc), processing_ms=processing_ms)
        return TriageResponse(
            ticket_id=ticket.ticket_id,
            processing_ms=processing_ms,
            model=f"ollama/{settings.ollama_llm_model}",
            tool_calls=[],
            final_draft=None,
            classification=None,
            sentiment_score=None,
            sop_chunks_used=[],
            error=str(exc),
        )
