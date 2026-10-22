# Testing & verification record

_Last updated: October 22, 2026 (local verification from the development VM)._

## Summary

- The DocShield app itself is fully verified locally: it boots, serves the
  page, and its non-API endpoints return correct responses.
- The request/response shapes DocShield sends were cross-checked line by line
  against the **official `clocked-sdk` Python package source** and its
  documented quickstart call (`decide(state=..., questions={"name":
  {"type": "noul", "instructions": ...}})` — they match.
- **Blocked from this VM only:** every POST to the Clocked API hangs without
  any response, with three independent clients (curl, httpx via this app,
  and the official SDK). Plain GETs to the same host answer in ~1 s, so the
  host and network path are fine — it is specifically the API POSTs that
  never return from this machine. The app must be re-verified end to end
  from the deployed host (Vercel), where egress is direct.

## Local app checks (all passing)

| Check | Result |
|---|---|
| `uvicorn api.index:app` boots | OK |
| `GET /` (the single-page UI) | 200, full page served |
| `GET /api/health` | 200 `{"status": "ok", "service": "docshield"}` |
| `GET /api/samples` | 200, both sample documents returned |
| App import / route table | `/api/protect`, `/api/extract`, `/api/decide`, `/api/verify`, `/api/samples`, `/api/health` all registered |

## Live API probes — precise record

All probes used the real account key (server-side only) and tiny inputs
(a 3-sentence agreement). One attempt each, 90-second bound, via the
official `clocked-sdk`:

| Endpoint | Call | Outcome | Wall time |
|---|---|---|---|
| Protect | `POST /clocked/pii` — `pii(text=…, anonymize="replace")` | `RequestTimeoutError` — "No response within 90 seconds." | 90.42 s |
| Extract | `POST /clocked/extract` — `extract(text=…, fields={…})` | `RequestTimeoutError` — same | 90.36 s |
| Decide | `POST /clocked/decide` — `decide(state=…, questions={"auto_renews": {"type": "noul", …}})` | `RequestTimeoutError` — same | 90.31 s |
| Verify | `POST /clocked/grounding` — `grounding(documents=[…], answer=…, evidence="all")` | `RequestTimeoutError` — same | 90.37 s |

Corroborating attempts the same day, same machine:

- Raw `curl` POST to `/clocked/decide`: tunnel opened, then **no response
  for >10 minutes**; a bounded retest gave up at 150 s (curl exit 28).
- DocShield's own `POST /api/protect` (httpx → Clocked): still in flight
  after ~4.5 minutes; stopped manually.
- Plain GETs to `https://clocked.rezolve.ai` from this VM: **0.5–1.2 s**
  (HTTP 403 bot wall for browser-less GETs) — DNS, routing and TLS to the
  host all work.
- The SDK documentation notes the API gateway has its own 120-second
  limit and the SDK's default timeout is 130 s so "the gateway's answer
  always arrives first" — from this VM, not even a gateway answer arrived.

Conclusion: the failure is in this VM's egress path for API POSTs, not in
the request shapes, the key, or the app. No `X-Clocked-Credits` header was
ever received, so **no credit debit could be confirmed** (the account
showed 20,000 credits / 0 used at scouting time; it is possible, though
unconfirmed, that a timed-out request was processed server-side).

## Environment quirks found (and handled in `api/clocked_client.py`)

1. **httpx + `NO_PROXY`:** on this VM, `NO_PROXY` contains bracketed IPv6
   entries (`[::1]`, …) that make httpx raise `InvalidURL` while merely
   constructing a client. → The client is built with `trust_env=False`.
2. **TLS-intercepting egress proxy:** this VM reaches the internet through
   a proxy that re-signs TLS. Python's bundled CA store rejects it
   (`CERTIFICATE_VERIFY_FAILED: self-signed certificate in chain`). →
   When the standard `HTTPS_PROXY` / `SSL_CERT_FILE` environment variables
   are present, the client honours them explicitly.
3. On a plain host (e.g. Vercel) neither variable is set: the client uses
   direct egress and default certificate verification. No code change is
   needed between local and deployed runs.

## What to re-verify after deployment

1. Run the full flow on the deployed URL with Sample 1 (freelance
   agreement): Protect entities + anonymized copy, Extract facts,
   Decide answers, then Verify with the claim
   *"I get paid $500 within 30 days of delivery."* (expected: Supported)
   and *"I can cancel at any time without any notice."* (expected: not
   supported — the agreement requires 15 days' notice).
2. Note the `X-Clocked-Credits` value shown in each step's footer and
   confirm the account balance moved by roughly that amount.
