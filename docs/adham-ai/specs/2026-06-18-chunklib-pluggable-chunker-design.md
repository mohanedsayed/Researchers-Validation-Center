# Design: `chunklib` — Standalone Pluggable Semantic Chunker

> **Status:** Design / spec (pre-implementation)
> **Date:** 2026-06-18
> **Author:** Adham (with Claude)
> **Related:** [Naqqad Phase 1 Foundation plan](../plans/2026-06-16-naqqad-phase1-foundation.md) — this design **replaces Task 9 (Ollama Chunker Service)** of that plan with an external, reusable package.

---

## 1. Purpose & Motivation

Phase 1 of Naqqad embedded chunking as an app-internal service (`app/services/chunker.py`) with **Ollama + Qwen2.5:7b hardwired** into it (`_call_ollama` is bolted directly to Ollama's `/api/generate` endpoint and response shape). To use a different model you would edit the service internals.

This is inconsistent with a product that is **already multi-provider**: the roadmap puts Stage-2 critique on Gemini/Claude, and the data model already supports **BYOK** (`User.byok_api_key`, `CreateSessionConfig.byok_api_key`).

**Goal:** Extract chunking into a standalone, published, reusable package (`chunklib`) with a **generic LLM-provider abstraction** so any model can be plugged in via configuration — no code change for models that share a protocol, one small adapter for a genuinely new protocol. The same provider layer is reused later by the Stage-2 critique engine.

### Non-goals (this package)
- File-format parsing of `.docx` / `.txt`. **Input is markdown only** — produced upstream by the main system (or another system) as an `.md` file.
- Stage-2 critique, jury assembly, report generation. (Future consumers of the `providers` layer.)
- A universal "talks to every model with zero code" layer — that does not exist; see §4.

---

## 2. Confirmed Decisions

| # | Decision | Choice |
|---|---|---|
| Scope | How "external"? | **Standalone published package** (own `pyproject`, semver, CI, versioned releases) |
| Model | Default chunking model | **Qwen2.5 (`qwen2.5:7b`)** via Ollama, **integrated generically so it can be swapped** for any other model via config |
| #1 | Package name | **`chunklib`** |
| #3 | Parsing ownership | **App/external owns parsing → passes markdown in.** `chunklib` only parses markdown to build the outline/offsets. |
| #4 | Input format & offsets | **Markdown only.** Offsets are **character + word** based — **not bytes**. |

---

## 3. Architecture — Two In-Process Layers

`chunklib` ships two independently-importable layers in one package:

```
chunklib/
  pyproject.toml                 # standalone build, semver, optional extras per provider
  src/chunklib/
    __init__.py                  # public exports
    models.py                    # Span, RawParagraph, ParsedDocument, OutlineNode,
                                 #   DocumentOutline, ChunkPosition, Chunk, ChunkResult
    errors.py                    # exception hierarchy
    config.py                    # ProviderConfig, ChunkerConfig, env loaders
    providers/                   # ── Layer 1: generic "pipe in any model" ──
      __init__.py
      base.py                    # LLMProvider, GenerationOptions, LLMResponse, Usage
      ollama.py                  # OllamaProvider (default; native /api/generate, format=json)
      openai_compatible.py       # OpenAICompatibleProvider (OpenAI, vLLM, LiteLLM, LM Studio, …)
      anthropic.py               # AnthropicProvider (Stage-2 / Claude)
      registry.py                # register_provider / create_provider / available_providers
      retry.py                   # RetryPolicy + with_retry
    markdown/                    # ── markdown → structured paragraphs + outline + offsets ──
      __init__.py
      parser.py                  # MarkdownParser (offset-tracking)
    strategies/                  # ── how to chunk (pluggable) ──
      __init__.py
      base.py                    # ChunkingStrategy
      deterministic.py           # markdown structure → base chunks (no model)
      semantic.py                # LLM groups/splits paragraph indices (Qwen2.5 default)
      auto.py                    # deterministic base + optional semantic refinement
    enrich/
      __init__.py
      language.py                # detect_language (ar/en/mixed) + LanguageDetector
      tokens.py                  # estimate_tokens + TokenEstimator
    chunker.py                   # Chunker facade/orchestrator
  tests/
```

**Key invariant:** these are **architectural layers in one Python process**, not microservices. The chunker calls the provider via a direct in-memory method call — no IPC, no serialization between layers. The *only* network boundary is `provider → model`, which exists in every design. **Layer separation therefore has zero runtime cost.**

- `chunklib.providers` knows about models/HTTP/auth. Knows **nothing** about documents, chunks, or offsets.
- `chunklib` (markdown + strategies + enrich + chunker) knows about documents and positions. It talks to a model **only** through the `LLMProvider` interface; it never imports Ollama/httpx directly.

---

## 4. How "Plug In Any Model" Actually Works

You implement **per protocol, not per model**. Switching models on a protocol you already support is **config-only**; a genuinely new protocol needs one small adapter (~50–100 lines), written once.

| Action | Code needed? |
|---|---|
| Swap Qwen2.5 → Llama3 → Mistral on the same Ollama/server | Config only (`model`) |
| Local Ollama → OpenAI / Groq / Together / OpenRouter / vLLM / LM Studio / llama.cpp | Config only (`base_url` + `model` + `api_key`) — all OpenAI-compatible |
| Add Anthropic Claude (native `/v1/messages`) | One adapter, once |
| Add Google Gemini (native API) | One adapter, once |
| Reach 100+ providers via one endpoint | Config only, via a LiteLLM proxy behind `OpenAICompatibleProvider` |

**v1 ships:** `OllamaProvider` (default, Qwen2.5), `OpenAICompatibleProvider` (the workhorse), `AnthropicProvider` (for Stage-2). `create_provider(config)` selects the adapter by `provider` name; `register_provider(name, factory)` lets any consumer add a protocol **without modifying the library**.

**BYOK** resolves cleanly to `ProviderConfig(provider=…, model=…, api_key=user_key)`.

---

## 5. Data Contracts (`models.py`)

Offsets use a single `Span` (character **and** word indices into the normalized markdown source; never bytes).

```python
@dataclass(frozen=True)
class Span:
    char_start: int
    char_end: int
    word_start: int
    word_end: int

@dataclass
class RawParagraph:
    text: str
    paragraph_index: int          # ordinal among paragraphs ("article" position)
    span: Span
    heading_path: list[str]       # breadcrumb, e.g. ["الفصل الأول", "1.1 خلفية الدراسة"]
    chapter_id: str | None
    section_id: str | None
    outline_node_id: str | None   # leaf heading node this paragraph sits under

@dataclass
class OutlineNode:                # one heading in the document tree
    id: str
    level: int                    # 1 = chapter (#), 2 = section (##), 3+ = subsection
    title: str
    order: int                    # global sequence among nodes
    parent_id: str | None
    span: Span                    # span covering this node's content (heading + body)
    chunk_ids: list[str]          # chunks living under this node

@dataclass
class DocumentOutline:            # the full hierarchical document map / TOC
    nodes: list[OutlineNode]
    source_length_chars: int
    source_length_words: int
    def root_chapters(self) -> list[OutlineNode]: ...
    def path_to(self, node_id: str) -> list[OutlineNode]: ...    # breadcrumb
    def node(self, node_id: str) -> OutlineNode | None: ...
    def children_of(self, node_id: str) -> list[OutlineNode]: ...

@dataclass
class ParsedDocument:
    source: str                   # normalized markdown text (offsets index into this)
    paragraphs: list[RawParagraph]
    outline: DocumentOutline
    estimated_pages: int          # max(1, total_chars // 2000)

@dataclass
class ChunkPosition:              # WHERE a chunk lies in the document
    chunk_index: int              # global ordinal among chunks
    paragraph_indices: list[int]  # source paragraphs composing this chunk
    span: Span                    # union span over constituent paragraphs
    heading_path: list[str]
    chapter_id: str | None
    section_id: str | None
    outline_node_id: str | None

@dataclass
class Chunk:                      # library output (app maps to its ORM row)
    id: str
    text: str
    position: ChunkPosition
    chapter_title: str | None     # convenience mirrors of position
    section_title: str | None
    language_hint: str | None     # "ar" | "en" | "mixed"
    token_estimate: int
    metadata: dict

@dataclass
class ChunkResult:
    chunks: list[Chunk]
    outline: DocumentOutline      # document-position map
    detected_language: str | None
    estimated_pages: int
    strategy_used: str            # "deterministic" | "semantic" | "auto"
    provider_used: str | None     # e.g. "ollama:qwen2.5:7b", or None
```

---

## 6. Layer 1 — Providers (generic LLM access)

### `providers/base.py`
```python
@dataclass
class GenerationOptions:
    temperature: float = 0.1
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None
    json_mode: bool = False               # request structured/JSON output
    seed: int | None = None
    timeout: float = 120.0
    extra: dict = field(default_factory=dict)   # provider-specific passthrough

@dataclass
class Usage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

@dataclass
class LLMResponse:
    text: str
    model: str
    usage: Usage | None = None
    finish_reason: str | None = None
    raw: dict = field(default_factory=dict)     # untouched provider payload

class LLMProvider(Protocol):          # implemented as ABC so retry/close/ctx are shared
    @property
    def name(self) -> str: ...        # "ollama" | "openai" | "anthropic"
    @property
    def model(self) -> str: ...
    async def generate(self, prompt: str, *, system: str | None = None,
                       options: GenerationOptions | None = None) -> LLMResponse: ...
    async def generate_json(self, prompt: str, *, schema: dict | None = None,
                           system: str | None = None,
                           options: GenerationOptions | None = None) -> Any: ...
    async def health(self) -> bool: ...
    async def aclose(self) -> None: ...
    async def __aenter__(self) -> "LLMProvider": ...
    async def __aexit__(self, *exc) -> None: ...
```

### `providers/ollama.py` (default — Qwen2.5)
```python
class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "qwen2.5:7b", *,
                 base_url: str = "http://localhost:11434",
                 timeout: float = 120.0,
                 client: "httpx.AsyncClient | None" = None,
                 default_options: GenerationOptions | None = None): ...
    async def generate(...) -> LLMResponse: ...   # POST /api/generate, stream=False
    async def generate_json(...) -> Any: ...       # uses Ollama format="json"
    async def health(self) -> bool: ...            # GET /api/tags
    async def aclose(self) -> None: ...
    # maps prompt_eval_count / eval_count → Usage
```

### `providers/openai_compatible.py` (workhorse)
```python
class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, model: str, *, base_url: str, api_key: str | None = None,
                 timeout: float = 120.0, client=None,
                 default_options: GenerationOptions | None = None): ...
    async def generate(...) -> LLMResponse: ...    # POST /v1/chat/completions
    # json_mode → response_format={"type": "json_object"}
```

### `providers/anthropic.py` (Stage-2 / Claude)
```python
class AnthropicProvider(LLMProvider):
    def __init__(self, model: str, *, api_key: str,
                 base_url: str = "https://api.anthropic.com",
                 timeout: float = 120.0, client=None,
                 default_options: GenerationOptions | None = None): ...
    async def generate(...) -> LLMResponse: ...    # POST /v1/messages
```

### `providers/registry.py`
```python
ProviderFactory = Callable[["ProviderConfig"], LLMProvider]

def register_provider(name: str, factory: ProviderFactory) -> None: ...
def create_provider(config: ProviderConfig) -> LLMProvider: ...
def available_providers() -> list[str]: ...
# built-ins auto-registered: "ollama", "openai", "anthropic"
```

### `providers/retry.py`
```python
@dataclass
class RetryPolicy:
    max_attempts: int = 3
    min_wait: float = 2.0
    max_wait: float = 10.0
    multiplier: float = 1.0

def with_retry(policy: RetryPolicy):   # decorator (tenacity); retries
    ...                                # ProviderTimeoutError / ProviderUnavailableError / RateLimitError
```

---

## 7. Markdown Parser (`markdown/parser.py`)

A line-based, **offset-tracking** parser (custom rather than an AST lib, because precise char/word spans are easier to compute from source positions).

```python
class MarkdownParser:
    def __init__(self, *, chars_per_page: int = 2000): ...
    def parse(self, markdown: str) -> ParsedDocument: ...
```

Behavior:
- `# ` → `OutlineNode(level=1)` (chapter); `## ` → level 2 (section); `### `+ → deeper levels.
- Blank-line-separated text blocks → `RawParagraph`, each carrying `heading_path`, `chapter_id`, `section_id`, `outline_node_id`.
- Each paragraph and node records a `Span`: `char_start/char_end` (indices into normalized `source`) and `word_start/word_end` (indices into the whitespace-tokenized word list).
- `estimated_pages = max(1, len(source) // chars_per_page)`.

---

## 8. Chunking Strategies (`strategies/`)

```python
class ChunkingStrategy(Protocol):
    name: str
    async def chunk(self, doc: ParsedDocument, *,
                   provider: LLMProvider | None = None) -> list[Chunk]: ...
```

### `DeterministicStrategy` (no model)
One `Chunk` per `RawParagraph`, preserving span + outline linkage. Always available; the default when no provider is configured.

### `SemanticStrategy` (LLM — Qwen2.5 default)
**The LLM decides grouping boundaries over existing paragraph indices only — it never rewrites text.** This keeps offsets exact and prevents hallucinated content.

- Builds a prompt listing paragraphs (index + short preview), instructing the model to return JSON groupings, e.g. `[[0,1], [2], [3,4,5]]`, merging paragraphs that form one coherent idea and splitting overly long ones at logical boundaries.
- The library then constructs each merged `Chunk` by concatenating the constituent paragraphs' source text and computing the **union `Span`** over their spans (exact char/word offsets preserved).
- Configurable prompt via `prompt_builder: Callable[[ParsedDocument], str] | None`.
- **Falls back to `DeterministicStrategy` on any provider error, timeout, or invalid/unparseable grouping** (validated: indices in range, no overlaps, full coverage).
```python
class SemanticStrategy(ChunkingStrategy):
    def __init__(self, *, prompt_builder=None, retry_policy: RetryPolicy | None = None): ...
    async def chunk(self, doc, *, provider) -> list[Chunk]: ...   # provider required
```

### `AutoStrategy` (default)
Runs deterministic base extraction; if a provider is configured and `semantic_refinement` is on, applies `SemanticStrategy`; otherwise returns the deterministic chunks.

---

## 9. Enrichment (`enrich/`)

Pure, pluggable functions — defaults match the existing Phase-1 behavior.

```python
def detect_language(text: str) -> str: ...     # "ar" | "en" | "mixed" (0.75 / 0.25 thresholds)
class LanguageDetector(Protocol):
    def detect(self, text: str) -> str: ...      # default: RegexLanguageDetector

def estimate_tokens(text: str) -> int: ...       # heuristic: max(1, int(len(words) * 1.3))
class TokenEstimator(Protocol):
    def estimate(self, text: str) -> int: ...     # swappable for a tiktoken-based estimator later
```

---

## 10. Facade (`chunker.py`)

```python
class Chunker:
    def __init__(self, provider: LLMProvider | None = None, *,
                 strategy: ChunkingStrategy | None = None,            # default AutoStrategy
                 language_detector: LanguageDetector | None = None,   # default regex
                 token_estimator: TokenEstimator | None = None,       # default heuristic
                 retry_policy: RetryPolicy | None = None): ...

    @classmethod
    def from_config(cls, config: "ChunkerConfig") -> "Chunker": ...   # builds provider via registry

    async def chunk_markdown(self, markdown: str | bytes) -> ChunkResult: ...  # parse → chunk → enrich
    async def chunk_parsed(self, doc: ParsedDocument) -> ChunkResult: ...
    async def aclose(self) -> None: ...
    async def __aenter__(self) -> "Chunker": ...
    async def __aexit__(self, *exc) -> None: ...
```

`chunk_markdown` is the primary entry point (markdown-only input). `chunk_parsed` is exposed for callers that already hold a `ParsedDocument`.

---

## 11. Config (`config.py`)

```python
@dataclass
class ProviderConfig:
    provider: str = "ollama"                 # "ollama" | "openai" | "anthropic" | custom
    model: str = "qwen2.5:7b"                # default model — swap freely
    base_url: str | None = None
    api_key: str | None = None
    options: GenerationOptions | None = None
    extra: dict = field(default_factory=dict)
    @classmethod
    def from_env(cls, prefix: str = "CHUNKLIB_") -> "ProviderConfig": ...

@dataclass
class ChunkerConfig:
    provider: ProviderConfig | None = None   # None → deterministic-only
    strategy: str = "auto"                   # "auto" | "deterministic" | "semantic"
    semantic_refinement: bool = True
    retry: RetryPolicy | None = None
    language_detection: bool = True
    token_estimation: bool = True
    chars_per_page: int = 2000
```

**Default config = Ollama + `qwen2.5:7b`**, generic and swappable.

---

## 12. Errors (`errors.py`)

```python
ChunkerError                       # base
├── LLMError
│   ├── ProviderTimeoutError
│   ├── ProviderUnavailableError
│   ├── ProviderResponseError
│   ├── RateLimitError
│   └── AuthenticationError
├── MarkdownParseError
├── StrategyError
└── StructuredOutputError          # LLM grouping JSON invalid / failed validation
```

---

## 13. Public Exports (`__init__.py`)

```python
from chunklib.chunker import Chunker
from chunklib.config import ProviderConfig, ChunkerConfig
from chunklib.models import (
    Span, RawParagraph, ParsedDocument, OutlineNode, DocumentOutline,
    ChunkPosition, Chunk, ChunkResult,
)
from chunklib.providers.base import LLMProvider, GenerationOptions, LLMResponse, Usage
from chunklib.providers.registry import register_provider, create_provider, available_providers
from chunklib.providers.retry import RetryPolicy
from chunklib.enrich.language import detect_language
from chunklib.enrich.tokens import estimate_tokens
from chunklib.errors import ChunkerError, LLMError  # … and subclasses
```

---

## 14. Integration with the Naqqad App

The app's chunker service shrinks to thin glue:

```python
# app/services/chunker.py
from chunklib import Chunker, ChunkerConfig, ProviderConfig
from app.config import settings

def build_chunker() -> Chunker:
    return Chunker.from_config(ChunkerConfig(
        provider=ProviderConfig(
            provider="ollama",
            model=settings.ollama_chunker_model,   # qwen2.5:7b
            base_url=settings.ollama_base_url,
        ),
    ))
```

The Celery task ([chunking.py](../plans/2026-06-16-naqqad-phase1-foundation.md)) calls `await chunker.chunk_markdown(md_bytes)` and maps `ChunkResult` → ORM rows.

**Schema impact on the Phase-1 plan (downstream change to capture):**
- `Chunk` ORM gains: `char_start`, `char_end`, `word_start`, `word_end`, `outline_node_id`, `paragraph_indices` (JSONB).
- The `DocumentOutline` is persisted — recommended: a JSONB column on `CritiqueSession` (e.g. `document_outline`) or a dedicated `outline_nodes` table if it needs to be queried.
- Upstream must deliver markdown: the app converts uploaded `.docx`/`.txt` to `.md` **before** invoking `chunklib` (parsing is the app's responsibility, per decision #3).

**Reuse payoff:** Stage-2 critique imports only `chunklib.providers` and does `create_provider(ProviderConfig(provider="anthropic", model="claude-…", api_key=byok))` — same layer, no re-implementation.

---

## 15. Performance Notes

- **Runtime:** dominated by the single LLM call on the semantic path (seconds for Qwen2.5:7b). Parsing = ms; language/token regex = µs; layer indirection = ns. Deterministic-only path makes **no** model call. Layer separation adds **no measurable runtime cost**.
- **Delivery:** building the standalone package is ~3–5 dev-days vs ~1 for the inline service — front-loaded, then recovered when Stage-2 reuses the provider layer.
- **Model choice is config, not code:** launch on a cheap hosted Flash model (zero GPU) for velocity, or run local **Qwen2.5 / Command R7B Arabic** for privacy — switch via `ProviderConfig`.

---

## 16. Testing Strategy

- **Providers:** unit-test each adapter's request/response mapping with a mocked `httpx` transport. A `FakeProvider` (returns canned groupings) drives the semantic strategy with no network/Ollama.
- **Markdown parser:** golden tests for heading hierarchy (1/2/3 levels), paragraph extraction, and **offset correctness** — assert `source[span.char_start:span.char_end]` equals the paragraph text, and word indices match.
- **Strategies:** deterministic chunk count; semantic merging via `FakeProvider`; **fallback-to-deterministic** on provider error and on invalid groupings (out-of-range / overlapping / incomplete coverage).
- **Enrichment:** Arabic / English / mixed language detection (matches Phase-1 thresholds); token estimate > 0.
- **Facade:** `chunk_markdown` end-to-end on an Arabic sample → `ChunkResult` with populated `outline`, `chunks`, offsets, `detected_language`.

---

## 17. Packaging

- Standalone repo / installable distribution; semver; CI (lint + tests).
- Core deps: `httpx`, `tenacity`. Markdown parsing is custom (no heavy dep).
- Optional extras: `chunklib[anthropic]`, `chunklib[all]` — though all current providers use plain REST via `httpx`, so extras mainly gate optional SDKs if added later.
- Python ≥ 3.11 (matches Naqqad backend).

---

## 18. Open Item for Review

**The LLM's role under markdown-only input.** Because markdown carries explicit structure, the deterministic path alone produces a valid outline + chunks. The design treats **Qwen2.5 as an optional semantic-refinement pass** (boundary decisions over paragraph indices) layered on top. Confirm this is the intended role, or specify if the LLM should instead do something heavier (e.g. semantic tagging/classification of chunks for the critique engine — though that may belong to Stage-2).
