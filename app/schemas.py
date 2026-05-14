from pydantic import BaseModel, EmailStr


class TicketIn(BaseModel):
    ticket_id: str
    customer_email: EmailStr
    subject: str
    body: str


class ToolCall(BaseModel):
    tool: str
    input: dict


class SopChunk(BaseModel):
    id: str
    title: str


class TriageResponse(BaseModel):
    ticket_id: str
    processing_ms: int
    model: str
    tool_calls: list[ToolCall]
    final_draft: str | None
    classification: str | None
    sentiment_score: int | None
    sop_chunks_used: list[SopChunk]
    error: str | None = None
