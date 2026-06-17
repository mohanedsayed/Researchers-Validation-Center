# التصميم: `chunklib` — مُجزِّئ دلالي مستقل وقابل للتوصيل

> **الحالة:** تصميم / مواصفات (قبل التنفيذ)
> **التاريخ:** 2026-06-18
> **المُعِدّ:** أدهم (بمساعدة Claude)
> **مرتبط بـ:** [خطة المرحلة الأولى لنقّاد](../plans/2026-06-16-naqqad-phase1-foundation.md) — هذا التصميم **يحلّ محلّ المهمة 9 (خدمة المُجزِّئ عبر Ollama)** في تلك الخطة، بحزمة خارجية قابلة لإعادة الاستخدام.

> **ملاحظة:** هذا ترجمة عربية لملف المواصفات. النسخة الإنجليزية الأصلية هي المرجع المعتمد عند أي اختلاف: [النسخة الإنجليزية](./2026-06-18-chunklib-pluggable-chunker-design.md). تُركت مقاطع الشيفرة ومسارات الملفات وأسماء الأصناف/الدوال بالإنجليزية لأنها مصدر الحقيقة عند التنفيذ.

---

## 1. الغرض والدوافع

في المرحلة الأولى من نقّاد، كانت عملية التجزئة مدمجة كخدمة داخلية ضمن التطبيق (`app/services/chunker.py`) مع **ربط Ollama + Qwen2.5:7b بشكل ثابت** بداخلها (الدالة `_call_ollama` موصولة مباشرةً بنقطة نهاية Ollama `‎/api/generate` وبصيغة استجابتها). ولاستخدام نموذج مختلف يتعيّن تعديل الشيفرة الداخلية للخدمة.

هذا يتعارض مع منتج هو **متعدّد المزوّدين أصلاً**: فخارطة الطريق تضع نقد المرحلة الثانية على Gemini/Claude، ونموذج البيانات يدعم بالفعل **إحضار مفتاحك الخاص (BYOK)** (الحقلان `User.byok_api_key` و`CreateSessionConfig.byok_api_key`).

**الهدف:** فصل التجزئة في حزمة مستقلة منشورة وقابلة لإعادة الاستخدام (`chunklib`) مع **تجريد عام لمزوّد نموذج اللغة (LLM)**، بحيث يمكن توصيل أي نموذج عبر الإعدادات — دون أي تغيير في الشيفرة للنماذج التي تتشارك البروتوكول نفسه، ومع مُحوِّل (adapter) صغير واحد فقط لأي بروتوكول جديد فعلاً. وتُعاد طبقة المزوّد نفسها لاحقاً في محرّك نقد المرحلة الثانية.

### ما هو خارج النطاق (لهذه الحزمة)
- تحليل صيغ الملفات `.docx` / `.txt`. **المُدخل هو Markdown فقط** — يُنتَج من النظام الرئيسي (أو نظام آخر) في صورة ملف `.md`.
- نقد المرحلة الثانية، وتجميع هيئة التحكيم، وتوليد التقارير. (هذه مستهلِكات مستقبلية لطبقة `providers`.)
- طبقة "تتحدّث إلى كل نموذج دون أي شيفرة" بشكل شامل — وهذا غير موجود؛ راجع §4.

---

## 2. القرارات المؤكَّدة

| # | القرار | الاختيار |
|---|---|---|
| النطاق | إلى أي مدى تكون "خارجية"؟ | **حزمة مستقلة منشورة** (لها `pyproject` خاص، وترقيم إصدارات semver، وتكامل مستمر CI، وإصدارات مُرقّمة) |
| النموذج | نموذج التجزئة الافتراضي | **Qwen2.5 (`qwen2.5:7b`)** عبر Ollama، **مُدمَج بشكل عام بحيث يمكن استبداله** بأي نموذج آخر عبر الإعدادات |
| #1 | اسم الحزمة | **`chunklib`** |
| #3 | مسؤولية التحليل (parsing) | **التطبيق/نظام خارجي يتولّى التحليل ← ويمرّر Markdown.** و`chunklib` يحلّل Markdown فقط لبناء المخطط/الإزاحات. |
| #4 | صيغة المُدخل والإزاحات | **Markdown فقط.** الإزاحات قائمة على **الحرف + الكلمة** — **وليست بالبايت**. |

---

## 3. البنية المعمارية — طبقتان داخل العملية نفسها

تُقدِّم `chunklib` طبقتين قابلتين للاستيراد بشكل مستقل ضمن حزمة واحدة:

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

**الثابت الأساسي:** هاتان طبقتان **معماريتان داخل عملية بايثون واحدة**، وليستا خدمتين مصغّرتين (microservices). يستدعي المُجزِّئ المزوّدَ عبر استدعاء دالة في الذاكرة مباشرةً — دون أي اتصال بين العمليات (IPC) ودون تسلسل (serialization) بين الطبقتين. والحدّ الشبكي الوحيد هو `provider → model`، وهو موجود في كل تصميم. **وبالتالي فإن فصل الطبقات لا يُكلّف شيئاً في وقت التشغيل.**

- `chunklib.providers` يعرف النماذج وHTTP والمصادقة. ولا يعرف **شيئاً** عن المستندات أو المقاطع أو الإزاحات.
- `chunklib` (markdown + strategies + enrich + chunker) يعرف المستندات والمواضع. ويتحدّث إلى النموذج **فقط** عبر واجهة `LLMProvider`؛ ولا يستورد Ollama/httpx مباشرةً أبداً.

---

## 4. كيف يعمل "توصيل أي نموذج" فعلياً

تُنفّذ مُحوِّلاً **لكل بروتوكول، لا لكل نموذج**. تبديل النماذج ضمن بروتوكول مدعوم مسبقاً هو **عبر الإعدادات فقط**؛ أمّا البروتوكول الجديد فعلاً فيحتاج مُحوِّلاً صغيراً واحداً (~50–100 سطر)، يُكتَب مرّة واحدة.

| الإجراء | هل يحتاج شيفرة؟ |
|---|---|
| تبديل Qwen2.5 ← Llama3 ← Mistral على نفس Ollama/الخادم | عبر الإعدادات فقط (`model`) |
| من Ollama المحلي ← OpenAI / Groq / Together / OpenRouter / vLLM / LM Studio / llama.cpp | عبر الإعدادات فقط (`base_url` + `model` + `api_key`) — جميعها متوافقة مع OpenAI |
| إضافة Anthropic Claude (البروتوكول الأصلي `/v1/messages`) | مُحوِّل واحد، مرّة واحدة |
| إضافة Google Gemini (واجهة برمجية أصلية) | مُحوِّل واحد، مرّة واحدة |
| الوصول إلى أكثر من 100 مزوّد عبر نقطة نهاية واحدة | عبر الإعدادات فقط، باستخدام وسيط LiteLLM خلف `OpenAICompatibleProvider` |

**ما تشحنه النسخة الأولى:** `OllamaProvider` (الافتراضي، Qwen2.5)، و`OpenAICompatibleProvider` (المُحوِّل الأكثر استخداماً)، و`AnthropicProvider` (للمرحلة الثانية). تختار `create_provider(config)` المُحوِّلَ بحسب اسم `provider`؛ وتُتيح `register_provider(name, factory)` لأي مستهلِك إضافة بروتوكول **دون تعديل المكتبة**.

ويُحَلّ **BYOK** بأناقة إلى `ProviderConfig(provider=…, model=…, api_key=user_key)`.

---

## 5. عقود البيانات (`models.py`)

تستخدم الإزاحات بنية `Span` واحدة (فهارس الحرف **و**الكلمة داخل نصّ Markdown المُطبَّع؛ ولا تكون بالبايت إطلاقاً).

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

> **شرح موجز للحقول الجوهرية:**
> - `Span` يحمل فهارس الحرف والكلمة معاً (`char_*` و`word_*`) — وهي المطابِقة لقرار #4.
> - `RawParagraph.paragraph_index` يمثّل "موضع المادة/الفقرة" داخل المستند.
> - `ChunkPosition.paragraph_indices` (جمع) لأن المقطع الواحد قد يجمع عدّة فقرات بعد التحسين الدلالي، و`span` فيه هو **اتحاد** نطاقات تلك الفقرات.
> - `DocumentOutline` هو خريطة مواضع المستند (الفصول/الأقسام/العناوين) بشكل شجري.

---

## 6. الطبقة الأولى — المزوّدون (وصول عام إلى نموذج اللغة)

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

### `providers/ollama.py` (الافتراضي — Qwen2.5)
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

### `providers/openai_compatible.py` (المُحوِّل الأكثر استخداماً)
```python
class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, model: str, *, base_url: str, api_key: str | None = None,
                 timeout: float = 120.0, client=None,
                 default_options: GenerationOptions | None = None): ...
    async def generate(...) -> LLMResponse: ...    # POST /v1/chat/completions
    # json_mode → response_format={"type": "json_object"}
```

### `providers/anthropic.py` (المرحلة الثانية / Claude)
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

## 7. مُحلِّل Markdown (`markdown/parser.py`)

مُحلِّل قائم على الأسطر **يتتبّع الإزاحات** (مُخصَّص بدلاً من مكتبة شجرة AST، لأن حساب نطاقات الحرف/الكلمة بدقّة أيسر من مواضع المصدر).

```python
class MarkdownParser:
    def __init__(self, *, chars_per_page: int = 2000): ...
    def parse(self, markdown: str) -> ParsedDocument: ...
```

السلوك:
- `# ` ← `OutlineNode(level=1)` (فصل)؛ `## ` ← المستوى 2 (قسم)؛ `### ` فما فوق ← مستويات أعمق.
- الكتل النصّية المفصولة بسطر فارغ ← `RawParagraph`، وكلٌّ منها يحمل `heading_path` و`chapter_id` و`section_id` و`outline_node_id`.
- تسجّل كلّ فقرة وكلّ عقدة `Span` يضمّ: `char_start/char_end` (فهارس داخل `source` المُطبَّع) و`word_start/word_end` (فهارس داخل قائمة الكلمات المُقطَّعة بالمسافات).
- `estimated_pages = max(1, len(source) // chars_per_page)`.

---

## 8. استراتيجيات التجزئة (`strategies/`)

```python
class ChunkingStrategy(Protocol):
    name: str
    async def chunk(self, doc: ParsedDocument, *,
                   provider: LLMProvider | None = None) -> list[Chunk]: ...
```

### `DeterministicStrategy` (بدون نموذج)
`Chunk` واحد لكلّ `RawParagraph`، مع الحفاظ على `span` والارتباط بالمخطط. متاحة دائماً، وهي الافتراضية حين لا يُضبَط أي مزوّد.

### `SemanticStrategy` (نموذج LLM — Qwen2.5 افتراضياً)
**يقرّر النموذجُ حدودَ التجميع على فهارس الفقرات الموجودة فقط — ولا يعيد كتابة النص إطلاقاً.** هذا يبقي الإزاحات دقيقة ويمنع اختلاق محتوى.

- يبني موجِّهاً (prompt) يَسرد الفقرات (الفهرس + معاينة قصيرة)، ويأمر النموذج بإرجاع تجميعات JSON، مثل `[[0,1], [2], [3,4,5]]`، يدمج الفقرات التي تُشكّل فكرة واحدة متماسكة ويقسم المفرطة في الطول عند حدود منطقية.
- ثمّ تُنشئ المكتبةُ كلّ `Chunk` مدموج بتسلسل نصوص الفقرات المُكوِّنة، وتحسب **اتحاد `Span`** على نطاقاتها (مع الحفاظ على إزاحات الحرف/الكلمة بدقّة).
- الموجِّه قابل للضبط عبر `prompt_builder: Callable[[ParsedDocument], str] | None`.
- **يرجع إلى `DeterministicStrategy` عند أي خطأ في المزوّد أو انتهاء مهلة أو تجميع غير صالح/غير قابل للتحليل** (يُتحقَّق: الفهارس ضمن المدى، دون تداخل، وبتغطية كاملة).
```python
class SemanticStrategy(ChunkingStrategy):
    def __init__(self, *, prompt_builder=None, retry_policy: RetryPolicy | None = None): ...
    async def chunk(self, doc, *, provider) -> list[Chunk]: ...   # provider required
```

### `AutoStrategy` (الافتراضية)
تُجري الاستخراج الحتمي الأساسي؛ فإن كان هناك مزوّد مضبوط وكان `semantic_refinement` مفعّلاً، تطبّق `SemanticStrategy`؛ وإلا تُرجِع المقاطع الحتمية.

---

## 9. الإثراء (`enrich/`)

دوال نقيّة وقابلة للاستبدال — والافتراضيات تطابق سلوك المرحلة الأولى الحالي.

```python
def detect_language(text: str) -> str: ...     # "ar" | "en" | "mixed" (0.75 / 0.25 thresholds)
class LanguageDetector(Protocol):
    def detect(self, text: str) -> str: ...      # default: RegexLanguageDetector

def estimate_tokens(text: str) -> int: ...       # heuristic: max(1, int(len(words) * 1.3))
class TokenEstimator(Protocol):
    def estimate(self, text: str) -> int: ...     # swappable for a tiktoken-based estimator later
```

---

## 10. الواجهة (`chunker.py`)

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

`chunk_markdown` هي نقطة الدخول الأساسية (مُدخل Markdown فقط). و`chunk_parsed` متاحة للمستدعين الذين يملكون `ParsedDocument` جاهزاً.

---

## 11. الإعدادات (`config.py`)

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

**الإعداد الافتراضي = Ollama + `qwen2.5:7b`**، عام وقابل للاستبدال.

---

## 12. الأخطاء (`errors.py`)

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

## 13. الصادرات العامة (`__init__.py`)

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

## 14. التكامل مع تطبيق نقّاد

تتقلّص خدمة المُجزِّئ في التطبيق إلى ربط رفيع:

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

تستدعي مهمّة Celery ([chunking.py](../plans/2026-06-16-naqqad-phase1-foundation.md)) الدالةَ `await chunker.chunk_markdown(md_bytes)` وتُسقِط `ChunkResult` على صفوف ORM.

**الأثر على مخطط قاعدة البيانات في خطة المرحلة الأولى (تغيير لاحق يجب رصده):**
- يكتسب نموذج `Chunk` في ORM: `char_start` و`char_end` و`word_start` و`word_end` و`outline_node_id` و`paragraph_indices` (JSONB).
- يُحفَظ `DocumentOutline` — والمُوصى به: عمود JSONB على `CritiqueSession` (مثل `document_outline`)، أو جدول مخصّص `outline_nodes` إن لزم الاستعلام عنه.
- يجب أن يوفّر المصدرُ الأعلى Markdown: يحوّل التطبيقُ ملفات `.docx`/`.txt` المرفوعة إلى `.md` **قبل** استدعاء `chunklib` (التحليل من مسؤولية التطبيق، حسب القرار #3).

**مردود إعادة الاستخدام:** يستورد نقدُ المرحلة الثانية `chunklib.providers` فقط ويستدعي `create_provider(ProviderConfig(provider="anthropic", model="claude-…", api_key=byok))` — الطبقة نفسها، دون أي إعادة تنفيذ.

---

## 15. ملاحظات الأداء

- **وقت التشغيل:** يهيمن عليه استدعاء النموذج الواحد على المسار الدلالي (ثوانٍ لـ Qwen2.5:7b). التحليل = ميلي ثانية؛ تعابير اللغة/التوكنات = ميكرو ثانية؛ والوساطة بين الطبقات = نانو ثانية. ولا يُجري المسارُ الحتمي الصِّرف **أيّ** استدعاء للنموذج. وفصل الطبقات لا يُضيف **أيّ** كلفة ملموسة في وقت التشغيل.
- **زمن الإنجاز:** بناء الحزمة المستقلة يستغرق نحو 3–5 أيام عمل مقابل ~يوم واحد للخدمة المدمجة — كلفة مُقدَّمة، تُستردّ حين يُعيد نقدُ المرحلة الثانية استخدام طبقة المزوّد.
- **اختيار النموذج إعداد لا شيفرة:** أطلِق على نموذج Flash مستضاف رخيص (دون GPU) للسرعة، أو شغّل محلياً **Qwen2.5 / Command R7B Arabic** للخصوصية — والتبديل عبر `ProviderConfig`.

---

## 16. استراتيجية الاختبار

- **المزوّدون:** اختبار وحدة لتعيين الطلب/الاستجابة لكلّ مُحوِّل بنقل httpx مُحاكى. ويُشغّل `FakeProvider` (يُرجِع تجميعات مُعدّة سلفاً) الاستراتيجيةَ الدلالية دون شبكة/Ollama.
- **مُحلِّل Markdown:** اختبارات مرجعية (golden) للتسلسل الهرمي للعناوين (مستويات 1/2/3)، واستخراج الفقرات، و**صحّة الإزاحات** — التحقّق أن `source[span.char_start:span.char_end]` يساوي نصّ الفقرة، وأن فهارس الكلمات مطابِقة.
- **الاستراتيجيات:** عدد المقاطع الحتمي؛ الدمج الدلالي عبر `FakeProvider`؛ و**الرجوع إلى الحتمي** عند خطأ المزوّد وعند التجميعات غير الصالحة (خارج المدى / متداخلة / ناقصة التغطية).
- **الإثراء:** كشف اللغة العربية / الإنجليزية / المختلطة (يطابق عتبات المرحلة الأولى)؛ تقدير التوكنات > 0.
- **الواجهة:** `chunk_markdown` من الطرف إلى الطرف على عيّنة عربية ← `ChunkResult` مع `outline` و`chunks` والإزاحات و`detected_language` معبّأة.

---

## 17. التحزيم

- مستودع مستقل / توزيع قابل للتثبيت؛ ترقيم semver؛ تكامل مستمر CI (فحص + اختبارات).
- التبعيات الأساسية: `httpx` و`tenacity`. وتحليل Markdown مُخصَّص (دون تبعية ثقيلة).
- إضافات اختيارية: `chunklib[anthropic]` و`chunklib[all]` — وإن كان جميع المزوّدين الحاليين يستخدمون REST عبر `httpx`، فالإضافات تُقيّد بالأساس أيّ حزم SDK اختيارية تُضاف لاحقاً.
- بايثون ≥ 3.11 (يطابق خلفية نقّاد).

---

## 18. بند مفتوح للمراجعة

**دور النموذج في ظلّ مُدخل Markdown فقط.** لأن Markdown يحمل بنية صريحة، فإن المسار الحتمي وحده يُنتج مخططاً ومقاطع صالحة. يعامل التصميمُ **Qwen2.5 كمسار تحسين دلالي اختياري** (قرارات حدود على فهارس الفقرات) مبنيّ فوقه. يُرجى تأكيد أن هذا هو الدور المقصود، أو تحديد ما إذا كان ينبغي للنموذج القيام بشيء أثقل (مثل وسم/تصنيف المقاطع دلالياً لمحرّك النقد — وإن كان ذلك قد ينتمي للمرحلة الثانية).
