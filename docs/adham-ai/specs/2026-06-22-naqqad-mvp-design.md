# Design Spec — Naqqad MVP (Validation Build)

**ID:** SPEC-MVP-001
**Type:** Design Spec (MVP / Validation)
**Author:** Mohaned (with Claude)
**Date:** 2026-06-22
**Status:** Draft — Pending Review
**Related:** [PRD-001 (High-Level)](../../prds/prd-high-naqqad.md) · [chunklib pluggable-chunker design](2026-06-18-chunklib-pluggable-chunker-design.md) · [Phase-1 Foundation plan](../plans/2026-06-16-naqqad-phase1-foundation.md)

---

## 1. Purpose

Spin up the smallest **real** version of Naqqad that lets us validate the core idea before investing in the full platform. The full PRD is large (jury assembly, DSE self-learning, billing/credits via Tap Payments, tiers, admin panel, institutional B2B, PDF typography). This MVP strips that down to one thing done for real: **a researcher uploads an Arabic academic paper (.docx) and gets back genuinely useful, expert-level critique in Arabic, streamed live, then a downloadable report.**

### 1.1 What we're validating (four goals, one slice)

The four validation goals are **nested, not parallel** — one thin-but-real end-to-end slice exercises all four:

| Goal | How this MVP tests it |
|---|---|
| **Technical feasibility** | The 2-stage API pipeline actually runs on real, messy Arabic `.docx` with bidi content. |
| **Critique quality** | A real researcher reads the output and judges whether it's useful and trustworthy. |
| **End-to-end UX** | The full happy path (upload → configure → stream → report) feels right. |
| **Demand / willingness** | The reaction to a working result — "was this useful? / want more?" — is the realest demand signal. |

A landing page measures curiosity; a working critique measures pull. The "was this useful? / want more?" prompt on the report screen **is** the demand instrument.

### 1.2 Success criteria

- ≥ 8–15 real researchers run a real Arabic paper through the full flow.
- A 100-page paper completes critique in a few minutes (not a hard SLA yet).
- Qualitative: researchers rate the critique useful (👍) and ask "how do I get more?"
- Pipeline handles real `.docx` (headings, footnotes, mixed Arabic+Latin) without crashing.

---

## 2. Scope

### 2.1 In scope — build for real

- `.docx` upload (Arabic), single file per session.
- **Stage-1 chunker** — structural parse + semantic chunking via a hosted API model.
- Auto-detect discipline + language; auto-assemble a jury (up to 3 specialist personas).
- **Stage-2 critique** — premium hosted API model, streamed chapter-by-chapter.
- Critique view: streaming output, severity badges (حرجة / كبيرة / تحرير), per-chapter progress.
- Report: structured findings on-screen + HTML/browser-print export.
- Tone gate: Constructive (نقد بنّاء) acknowledged before run.
- Lightweight feedback: 👍/👎 + "want more?" CTA (the demand instrument).
- 24-hour secure deletion of uploaded files and reports.

### 2.2 Faked / deferred (stubbed for the MVP)

- **Billing** → "join the paid waitlist" button (captures intent, no payment).
- **Accounts** → none; anonymous session + shareable result link.
- **DSE approval queue** → newly-generated discipline instructions auto-apply for the session; no admin UI, no promotion workflow.
- **Jury customization** → auto-assembled only; no manual persona selection.
- **PDF typography** → HTML report + browser print; no WeasyPrint/ReportLab Arabic-RTL spike yet.
- **Report depth selector** → one good default depth (Standard).

### 2.3 Cut entirely (not in the MVP)

- Tiers / token bundles / credits / Tap Payments.
- Institutional B2B accounts + style-guide upload.
- Admin panel, system-wide usage analytics.
- Reviewer "Forensic" mode (محكّم) — Researcher / Constructive only.
- EN / FR UI (Arabic only).
- `.txt` / `.md` upload (`.docx` only).
- Native mobile apps.

---

## 3. Key decisions (this build)

| # | Decision | Rationale |
|---|---|---|
| D1 | **API-based model only; local model dropped entirely.** | Simpler to ship and validate; no GPU/self-hosting ops. The Ollama/Qwen default and the "local for privacy" angle are removed. |
| D2 | **Single provider: Anthropic**, official `anthropic` Python SDK, one API key. | One SDK, one key, strong Arabic; `chunklib` stays provider-agnostic so this is config, not lock-in. |
| D3 | **Stage-1 chunker = `claude-haiku-4-5`** ($1/$5 per MTok, 200K ctx). | Cheap, fast, platform-absorbed (not billed to users). |
| D4 | **Stage-2 critique = `claude-sonnet-4-6`** ($3/$15 per MTok, 1M ctx, adaptive thinking). | Cost-balanced; strong Arabic. Model choice is `ProviderConfig`, so swapping to Opus 4.8 for max quality is a config flip. |
| D5 | **Infra aligned with Phase-1 plan** (FastAPI + Postgres + Redis + Celery + S3/localstack), **minus Ollama**. | Build the production backend foundation now; avoid a migration later. |
| D6 | **No login** — anonymous session + shareable result link. | Lowest friction to get real papers in front of us fast. Drops the JWT/auth module from the Phase-1 plan. |

> See memory: chunker is API-model-only as of 2026-06-22.

---

## 4. User flow (the one happy path)

```mermaid
sequenceDiagram
    actor R as Researcher
    participant UI as Web UI (Next.js, RTL)
    participant API as FastAPI
    participant W as Celery worker
    participant S1 as Stage-1 (Haiku 4.5)
    participant S2 as Stage-2 (Sonnet 4.6)
    participant Store as Encrypted S3 + Postgres

    R->>UI: Upload .docx
    UI->>API: POST /sessions/upload
    API->>Store: Encrypt + store file; create session (status=parsing)
    API->>W: dispatch chunking task
    W->>S1: parse + semantic chunk (python-docx + Haiku)
    S1-->>W: chunks + chapter map + detected discipline/language
    W->>Store: persist chunks; status=queued
    R->>UI: Confirm jury preview + tone gate → start
    UI->>API: POST /sessions/{id}/critique
    API->>W: dispatch critique task (status=critiquing)
    W->>S2: stream critique per chunk
    S2-->>UI: SSE stream (severity-tagged findings)
    W->>Store: persist report; status=completed
    R->>UI: read report, download/print, 👍/👎, "want more?"
    Store->>Store: secure wipe at T+24h (Celery Beat)
```

---

## 5. Architecture

### 5.1 Two-stage pipeline

**Stage-1 — Chunker (cheap, platform cost, not billed).**
- `python-docx` deterministically extracts the document's structure (headings, paragraphs, footnotes, tables) — no LLM needed for raw structure.
- `claude-haiku-4-5` performs the *semantic* step: grouping paragraphs into topic-coherent chunks that respect chapter/section boundaries, and emitting per-chunk metadata (chapter, section, token count). Uses structured outputs (`output_config.format`) for a strict chunk JSON schema.
- Detects discipline + language from the assembled structure.
- Implemented via `chunklib` with the **default provider flipped from Ollama to Anthropic** (this is the only substantive change to the existing chunklib design — see §9).

**Stage-2 — Critique (premium, the value).**
- `claude-sonnet-4-6` with adaptive thinking, receiving only the structured chunks (never the raw file).
- Auto-assembles a jury (up to 3 specialist personas) merged via the Hybrid Synthesis approach from the PRD.
- Streams critique per chunk/chapter; each finding tagged with severity (Critical / Major / Editorial → حرجة / كبيرة / تحرير).
- Streamed to the browser over SSE via `client.messages.stream()`.
- Prompt-injection guard: uploaded content is passed strictly as data, never as instructions; system prompts stay server-side.

### 5.2 Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | Next.js (App Router) + Tailwind, **RTL-native Arabic** | SSE client for streaming critique; HTML report + browser print |
| Backend | FastAPI (Python 3.11) + async SQLAlchemy 2.0 | Mirrors Phase-1 plan |
| LLM SDK | official `anthropic` Python SDK | streaming + structured outputs |
| Chunking | `chunklib` (`python-docx` + Anthropic provider) | provider-agnostic; Anthropic is the new default |
| Queue | Redis 7 + Celery 5 (+ Celery Beat) | async chunking/critique; Beat for 24h wipe |
| DB | PostgreSQL 16 | sessions, chunks, reports, feedback |
| Storage | S3-compatible (localstack in dev), AES-256 at rest | TTL lifecycle for 24h delete |
| Deploy | docker-compose: `api`, `worker`, `beat`, `postgres`, `redis`, `localstack`, `web` | Ollama service removed |

### 5.3 Data model (MVP — anonymous, no User)

- **CritiqueSession** — root entity (no user FK). Opaque shareable ID/token; jury config; tone; status lifecycle; `expires_at` (T+24h).
- **UploadedFile** — encrypted blob reference (`.docx`); belongs to one session; destroyed on expiry.
- **Chunk** — Stage-1 output; belongs to a session; chapter/section metadata + token count.
- **CritiqueReport** — structured Stage-2 output; severity-tagged findings; HTML-exportable; destroyed with the session.
- **DisciplineInstruction** — DSE-generated critique standard; **auto-applied** for the session (no approval workflow in MVP); persisted so it can seed the future knowledge library.
- **Feedback** — 👍/👎 + optional comment + "want more?" intent flag, keyed to a session. *This is the validation data.*

Dropped vs full PRD for MVP: `User`, `Subscription`, `CreditLedger`, `Institution`.

### 5.4 Status lifecycle

`Uploading → Parsing → Queued → Critiquing → Completed → Expired` (with `Failed → Queued` auto-retry on LLM errors). Matches PRD §10.1.

---

## 6. Screens (Arabic-first, RTL)

1. **رفع بحث (Upload & Configure)** — `.docx` drop → auto-detected discipline + language → jury preview card → tone gate (Constructive) → start.
2. **عرض النقد (Critique View)** — streaming chapter-by-chapter output, severity badges, per-chapter progress bar.
3. **التقرير (Report)** — structured findings grouped by chapter + severity counts, download/print, and the **"was this useful? / want more?"** demand instrument.

---

## 7. Validation instrumentation

The point of the MVP is learning. Capture, per session:
- Completion: did the run finish? time-to-complete for the paper size.
- Engagement: did they reach the report and scroll/read it?
- Quality signal: 👍/👎 + optional free-text.
- Demand signal: "want more?" / "join paid waitlist" clicks (+ optional email).
- Failure log: which `.docx` features broke chunking (footnotes, tables, equations, embedded images).

---

## 8. Non-functional (lean for MVP)

- **Security:** AES-256 at rest, TLS in transit; prompts server-side only; uploaded content treated as data.
- **Privacy / retention:** 24-hour secure wipe of files + reports (Celery Beat + S3 TTL). Non-negotiable, kept from the PRD.
- **Resilience:** auto-retry with backoff on Anthropic API errors.
- **RTL/bidi:** Arabic-native UI; bidi handling for mixed Arabic+Latin in parse and output.
- **Performance:** parallel chunk processing; "few minutes for 100 pages" target, not a hard SLA yet.

---

## 9. Impact on existing docs

This MVP supersedes the local-model assumptions. Reconcile when convenient:
- [Phase-1 Foundation plan](../plans/2026-06-16-naqqad-phase1-foundation.md): replace Ollama/Qwen Stage-1 with Anthropic; drop the auth/JWT module (no login); keep the rest of the stack.
- [chunklib design](2026-06-18-chunklib-pluggable-chunker-design.md): default provider flips Ollama → Anthropic; remove "local for privacy" framing (and `.ar.md`).
- [prd-high-naqqad.md](../../prds/prd-high-naqqad.md) lines 139/206/358/399 (+ `.ar.md`): "cheap/local model" → "cheap hosted API model."

---

## 10. Roadmap — Now / Next / Remaining

What the MVP delivers, what to tackle right after, and everything still on the runway to the full PRD.

### 10.1 NOW — the MVP (this spec)

- Anonymous `.docx` upload → Stage-1 chunk (Haiku) → Stage-2 critique (Sonnet, streamed) → HTML report.
- Auto jury assembly + auto DSE (no approval).
- 24h delete. Feedback + "want more?" instrument.
- Stack: FastAPI + Postgres + Redis + Celery + S3(localstack) + Next.js RTL.

### 10.2 NEXT — first follow-ups once the idea is validated

| Item | Why next | Adds to stack |
|---|---|---|
| **Accounts (magic-link → full auth)** | Needed before billing; ties sessions to people | JWT/auth module (the dropped Phase-1 piece) |
| **Billing: Tap Payments + tiers + credits** | Turn validated demand into revenue | Tap Payments integration, `Subscription`/`CreditLedger` models |
| **Token metering** | Bill only Stage-2 tokens per PRD | usage accounting per session |
| **PDF report (Arabic RTL)** | Replace browser-print with real typography | WeasyPrint vs ReportLab spike |
| **Reviewer / Forensic mode** | Second core persona from the PRD | tone gate + prompt variants |
| **DSE approval workflow + Admin panel** | Promote auto-drafts into the shared knowledge library | admin UI, `DisciplineInstruction` status flow |
| **Report depth selector** | Executive / Standard / Deep Audit | prompt variants |

### 10.3 REMAINING — full-PRD scope still open

- Institutional B2B accounts + style-guide upload (Scholar tier).
- EN / FR localization (secondary languages).
- `.txt` / `.md` ingestion; up to 1,000-page documents.
- Multi-provider Stage-2 fallback (Gemini/Claude) + key rotation at scale.
- Free BYOK tier (20-page limit, watermarked output) + rate limits.
- System health dashboard, usage analytics, multi-provider observability.
- WCAG 2.1 AA + Arabic screen-reader support.
- Maps to the existing sub-plan roadmap: Plan 2 (Critique + DSE), Plan 3 (Reports), Plan 4 (full UI + Billing).

---

## 11. Open questions

1. Stage-1 semantic chunking: how much can be deterministic (`python-docx`) vs how much needs Haiku? (Spike during build — affects Stage-1 cost.)
2. Token-to-page ratio for Arabic academic `.docx` — measure on real samples to inform future pricing.
3. Shareable result link: is anonymous-but-guessable acceptable for 24h, or do we need an unguessable token + optional passphrase?
4. How is "want more?" intent captured without accounts — optional email field, or just a click count?
5. Do we need a minimal rate-limit / abuse guard on the anonymous upload endpoint for the MVP?
```
