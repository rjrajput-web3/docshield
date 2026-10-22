"""DocShield — FastAPI application entry point.

Serves the single-page frontend and the /api/* endpoints that proxy to the
Clocked API (https://clocked.rezolve.ai/clocked). The Clocked API key stays
server-side in the CLOCKED_API_KEY environment variable; browsers only ever
talk to this app's own endpoints.

Local run:
    uvicorn api.index:app --reload --port 8000
On Vercel, this module's `app` is the serverless entry point.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:  # package import (local uvicorn from the repo root)
    from api.clocked_client import ClockedError, post as clocked_post
    from api.samples import SAMPLES
except ImportError:  # flat import (some serverless runtimes)
    from clocked_client import ClockedError, post as clocked_post  # type: ignore
    from samples import SAMPLES  # type: ignore

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="DocShield", version="0.1.0")


class DocIn(BaseModel):
    """A document supplied as pasted text or as a base64-encoded PDF."""

    text: str | None = None
    pdf_base64: str | None = None


class StepOut(BaseModel):
    result: dict
    credits: str | None = None
    cost_usd: str | None = None
    elapsed_s: float
    meta: dict = {}


def doc_fragment(doc: DocIn, text_limit: int) -> tuple[dict, dict]:
    """Build the {'text': ...} or {'pdf': ...} part of a Clocked payload."""
    meta: dict = {}
    if doc.pdf_base64:
        return {"pdf": doc.pdf_base64}, meta
    text = (doc.text or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="Provide document text or a PDF.")
    if len(text) > text_limit:
        meta["truncated_to"] = text_limit
        text = text[:text_limit]
    return {"text": text}, meta


def run_step(path: str, payload: dict, meta: dict) -> StepOut:
    try:
        res = clocked_post(path, payload)
    except ClockedError as exc:
        detail = exc.args[0] if exc.args else "Clocked API error"
        if exc.body:
            detail = f"{detail}: {exc.body}"
        raise HTTPException(status_code=502, detail=detail) from exc
    return StepOut(
        result=res.data,
        credits=res.credits,
        cost_usd=res.cost_usd,
        elapsed_s=round(res.elapsed_s, 2),
        meta=meta,
    )


@app.post("/api/protect", response_model=StepOut)
def protect(doc: DocIn) -> StepOut:
    """Step 1 — find PII and return an anonymized, safe-to-share copy."""
    fragment, meta = doc_fragment(doc, text_limit=60_000)  # Protect limit
    payload = {**fragment, "anonymize": "replace"}
    return run_step("/pii", payload, meta)


EXTRACT_FIELDS = {
    "parties": {
        "description": "The names of the parties (people or organizations) who are part of this agreement",
        "list": True,
        "max_items": 6,
    },
    "effective_date": {
        "description": "The date the agreement starts or takes effect",
        "format": "date",
    },
    "payment_amount": {
        "description": "The main payment amount owed under the document, exactly as written including any currency",
    },
    "payment_timing": {
        "description": "When payment is due, or how soon after delivery or invoice it must be made",
    },
    "notice_period": {
        "description": "How much notice must be given to cancel or terminate the agreement",
    },
    "term_length": {
        "description": "How long the agreement lasts (its term or duration)",
    },
}

FIELD_LABELS = {
    "parties": "Parties",
    "effective_date": "Start / effective date",
    "payment_amount": "Payment amount",
    "payment_timing": "Payment timing",
    "notice_period": "Notice period to cancel",
    "term_length": "Term / duration",
}


@app.post("/api/extract", response_model=StepOut)
def extract(doc: DocIn) -> StepOut:
    """Step 2 — pull the key facts out of the document, with confidence."""
    fragment, meta = doc_fragment(doc, text_limit=200_000)  # Extract limit
    payload = {**fragment, "fields": EXTRACT_FIELDS}
    out = run_step("/extract", payload, meta)
    out.result = {**out.result, "_labels": FIELD_LABELS}
    return out


DECIDE_QUESTIONS = {
    "payment_obligation": {
        "type": "noul",
        "instructions": "Does this document require one party to pay money to the other party?",
    },
    "auto_renews": {
        "type": "noul",
        "instructions": "Does the agreement renew automatically at the end of its term unless someone cancels it first?",
    },
    "overall_risk": {
        "type": "score",
        "min": 1,
        "max": 10,
        "instructions": "Rate the overall risk of this document for the person who signs or agrees to it: 1 means very safe and standard, 10 means very risky or one-sided.",
    },
    "document_type": {
        "type": "choice",
        "options": [
            "Freelance or services agreement",
            "Rental or lease agreement",
            "Employment offer letter",
            "Invoice or payment document",
            "Loan agreement",
            "Other document",
        ],
        "instructions": "Which category best describes this document?",
    },
}


@app.post("/api/decide", response_model=StepOut)
def decide(doc: DocIn) -> StepOut:
    """Step 3 — plain-language answers about obligations, renewal and risk."""
    fragment, meta = doc_fragment(doc, text_limit=200_000)
    if "text" in fragment:
        payload = {"state": fragment["text"], "questions": DECIDE_QUESTIONS}
    else:  # PDF input replaces the state
        payload = {"pdf": fragment["pdf"], "questions": DECIDE_QUESTIONS}
    return run_step("/decide", payload, meta)


class VerifyIn(DocIn):
    claim: str


@app.post("/api/verify", response_model=StepOut)
def verify(body: VerifyIn) -> StepOut:
    """Step 4 — check a claim about the document, claim by claim."""
    claim = (body.claim or "").strip()
    if not claim:
        raise HTTPException(status_code=422, detail="Type a claim to check first.")
    if body.pdf_base64:
        payload = {"pdf": body.pdf_base64, "answer": claim, "evidence": "all"}
        return run_step("/grounding", payload, {})
    fragment, meta = doc_fragment(body, text_limit=200_000)
    payload = {
        "documents": [fragment["text"]],
        "answer": claim,
        "evidence": "all",
    }
    return run_step("/grounding", payload, meta)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "docshield"}


@app.get("/api/samples")
def samples() -> list:
    return SAMPLES


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
