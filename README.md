# DocShield

**Understand any document. Share it safely.**

DocShield is a small web app built on the [Clocked API](https://clocked.rezolve.ai).
Paste a contract, offer letter, invoice or agreement and DocShield will:

1. **Protect** — find personal information (names, emails, phone numbers, addresses, bank details) and produce an anonymized copy that is safe to share.
2. **Extract** — pull out the key facts: who the parties are, dates, payment amounts and timing, notice period and term.
3. **Decide** — answer plain questions about the document: Is there a payment obligation? Does it auto-renew? How risky is it (1–10)? What kind of document is it?
4. **Verify** — check any claim you type ("I get paid $500 within 30 days") against the document, claim by claim, with evidence quotes.

Built for the Clocked Build Challenge (October 21 – November 10, 2026).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then put your own Clocked API key in .env
```

Create/revoke API keys in the Clocked dashboard: https://clocked.rezolve.ai/account

## Run locally

```bash
set -a; . ./.env; set +a
.venv/bin/uvicorn api.index:app --port 8000
# open http://localhost:8000
```

## Architecture

```
Browser (single static page, api/static/index.html)
   │  POST /api/protect | /api/extract | /api/decide | /api/verify
   ▼
FastAPI app (api/index.py)  ──  api/clocked_client.py  ──►  Clocked API
   │                                                        https://clocked.rezolve.ai/clocked
   └─ GET /api/samples (built-in demo documents, api/samples.py)
```

- The browser never sees the Clocked API key. The FastAPI backend reads it
  from the `CLOCKED_API_KEY` environment variable and calls Clocked
  server-side.
- Every Clocked call sends `Authorization: Bearer <key>`,
  `Content-Type: application/json` and a fresh `Idempotency-Key` (UUID) per
  logical request; a retry of the same request reuses the same key, so a
  request is never charged twice.
- Each step's response is returned to the page together with the actual
  `X-Clocked-Credits` debit and the elapsed time, which the UI shows in the
  step's footer.
- Timeouts are bounded (150 s read) so a stuck upstream call surfaces as a
  clear error instead of hanging the page.
- The app is structured for Vercel serverless (`api/index.py` exposes
  `app`; `vercel.json` rewrites all routes to it), and runs unchanged under
  a plain `uvicorn` locally.

## How DocShield uses the Clocked API

| Step | Clocked endpoint | What DocShield sends | What the output drives in the app |
|---|---|---|---|
| Protect | `POST /clocked/pii` | The document text (or base64 PDF) with `anonymize: "replace"` | The entity table (type, value, confidence), per-type counts, and the anonymized safe-to-share copy of the document |
| Extract | `POST /clocked/extract` | The document + six named field definitions (parties, effective date, payment amount, payment timing, notice period, term) | The "key facts" table — each fact shown verbatim with its confidence score |
| Decide | `POST /clocked/decide` | The document as `state` + four typed questions: payment obligation (`noul`), auto-renewal (`noul`), overall risk (`score` 1–10), document type (`choice`) | Plain-language answers with the probabilities behind them |
| Verify | `POST /clocked/grounding` | The document as the source + the user's claim as `answer`, `evidence: "all"` | A claim-by-claim verdict (supported / contradicted / not stated) with evidence quotes from the document, plus grounded/ungrounded scores |

Endpoints used: **Protect (PII), Extract, Decide, Verify (Grounding)** —
covering all three Clocked capability groups (core, safety, knowledge).

## Testing

See [TESTING.md](TESTING.md) for the verification record: local checks,
live-API probe results, and the environment quirks found on the way.

## Notes

- Sample documents (people, companies, account numbers) are fictional demo
  data written for this project.
- Never commit a real key: `.env` is git-ignored; only `.env.example`
  (with a placeholder) is tracked.

