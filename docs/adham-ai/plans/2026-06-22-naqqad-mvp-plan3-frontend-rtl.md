# Naqqad MVP — Plan 3: Next.js RTL Frontend (the three screens)

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or build to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Arabic-first, RTL web UI for the MVP happy path: **Upload & Configure → live Critique View (SSE) → Report** with the "was this useful? / want more?" feedback instrument — talking to the Plan 1 + Plan 2 backend.

**Architecture:** Next.js (App Router) + Tailwind, `dir="rtl"` / `lang="ar"` at the root. Pure logic (severity mapping, API client) is unit-tested with Vitest; the streaming Critique View consumes the backend SSE stream via the browser `EventSource` API; visual screens are verified via manual smoke steps. Sessions are addressed anonymously by `share_token` in the URL (`/s/[token]/...`).

**Tech Stack:** Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS · Vitest + @testing-library/react · browser `EventSource`

**Depends on:** [Plan 1](2026-06-22-naqqad-mvp-plan1-backend-foundation.md) + [Plan 2](2026-06-22-naqqad-mvp-plan2-critique-streaming.md) (backend API). **Related:** [MVP design spec](../specs/2026-06-22-naqqad-mvp-design.md) (the three-screen mockup).

---

## File Structure

```
web/
├── package.json
├── next.config.mjs
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.mjs
├── vitest.config.ts
├── vitest.setup.ts
├── .env.local.example
├── app/
│   ├── layout.tsx                  # RTL, lang=ar, Arabic font
│   ├── globals.css
│   ├── page.tsx                    # Screen 1: Upload & Configure
│   └── s/[token]/
│       ├── critique/page.tsx       # Screen 2: live Critique View (SSE)
│       └── report/page.tsx         # Screen 3: Report + feedback
├── lib/
│   ├── types.ts
│   ├── severity.ts                 # severity → {labelAr, classes}
│   └── api.ts                      # upload, getSession, getReport, postFeedback, streamUrl
├── components/
│   ├── SeverityBadge.tsx
│   ├── FindingCard.tsx
│   ├── JuryPreview.tsx
│   └── FeedbackWidget.tsx
└── __tests__/
    ├── severity.test.ts
    ├── api.test.ts
    └── SeverityBadge.test.tsx
```

> **Working directory:** `/Users/mohanedsayed/Researchers-Validation-Center`; frontend commands from `/Users/mohanedsayed/Researchers-Validation-Center/web`.

---

## Task 1: Scaffold Next.js + Tailwind + RTL

**Files:**
- Create: `web/package.json`, `web/next.config.mjs`, `web/tsconfig.json`, `web/tailwind.config.ts`, `web/postcss.config.mjs`, `web/.env.local.example`
- Create: `web/app/layout.tsx`, `web/app/globals.css`

- [ ] **Step 1.1: Create `web/package.json`**

```json
{
  "name": "naqqad-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "test": "vitest run"
  },
  "dependencies": {
    "next": "15.1.3",
    "react": "19.0.0",
    "react-dom": "19.0.0"
  },
  "devDependencies": {
    "@testing-library/react": "16.1.0",
    "@testing-library/jest-dom": "6.6.3",
    "@types/node": "22.10.2",
    "@types/react": "19.0.2",
    "@types/react-dom": "19.0.2",
    "autoprefixer": "10.4.20",
    "jsdom": "25.0.1",
    "postcss": "8.4.49",
    "tailwindcss": "3.4.17",
    "typescript": "5.7.2",
    "vitest": "2.1.8"
  }
}
```

- [ ] **Step 1.2: Create `web/next.config.mjs`**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

- [ ] **Step 1.3: Create `web/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 1.4: Create `web/tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2937",
        parchment: "#fdfcf8",
        accent: "#b45309",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 1.5: Create `web/postcss.config.mjs`**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 1.6: Create `web/.env.local.example`**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 1.7: Create `web/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html,
body {
  background: #f4f1ea;
  color: #1f2937;
}
```

- [ ] **Step 1.8: Create `web/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "نَقّاد — Naqqad",
  description: "مجلس مناقشة افتراضي لنقد الأبحاث الأكاديمية",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body className="min-h-screen font-sans antialiased">
        <header className="bg-ink text-parchment px-6 py-3 text-lg font-semibold">
          نَقّاد
        </header>
        <main className="mx-auto max-w-3xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 1.9: Install dependencies and verify dev server boots**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
cp .env.local.example .env.local
npm install
npm run dev
```

Expected: Next.js dev server starts on `http://localhost:3000` (visit it: the RTL header "نَقّاد" renders right-aligned). Stop with Ctrl-C.

- [ ] **Step 1.10: Commit**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/package.json web/next.config.mjs web/tsconfig.json web/tailwind.config.ts web/postcss.config.mjs web/.env.local.example web/app/layout.tsx web/app/globals.css web/package-lock.json
git commit -m "feat(mvp-web): scaffold Next.js + Tailwind, RTL Arabic layout"
```

---

## Task 2: Types + Severity Mapping (TDD)

**Files:**
- Create: `web/lib/types.ts`
- Create: `web/lib/severity.ts`
- Create: `web/vitest.config.ts`, `web/vitest.setup.ts`
- Create: `web/__tests__/severity.test.ts`

- [ ] **Step 2.1: Create `web/vitest.config.ts`**

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
  },
});
```

- [ ] **Step 2.2: Create `web/vitest.setup.ts`**

```typescript
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 2.3: Create `web/lib/types.ts`**

```typescript
export type Severity = "critical" | "major" | "editorial";

export type SessionStatus =
  | "uploading"
  | "parsing"
  | "queued"
  | "critiquing"
  | "completed"
  | "failed"
  | "expired";

export interface JuryPersona {
  role: string;
  focus: string;
}

export interface JuryConfig {
  personas: JuryPersona[];
  merged_system_prompt: string;
}

export interface SessionResponse {
  id: string;
  share_token: string;
  status: SessionStatus;
  tone: string;
  report_depth: string;
  detected_language: string | null;
  detected_disciplines: string[] | null;
  tokens_consumed: number;
  created_at: string;
  expires_at: string;
  jury_config?: JuryConfig | null;
}

export interface Finding {
  severity: Severity;
  title: string;
  body: string;
  chapter_title: string | null;
}

export interface ReportResponse {
  session_id: string;
  summary: string | null;
  severity_counts: Record<string, number>;
  findings: (Finding & { id: string; order_index: number })[];
}
```

> Note: the backend `SessionResponse` does not include `jury_config` in Plan 2's schema. Before this is consumed in Task 4, add `jury_config: dict | None` to `backend/app/schemas/session.py`'s `SessionResponse` (one line) and rebuild — see Task 4, Step 4.1.

- [ ] **Step 2.4: Write the failing test `web/__tests__/severity.test.ts`**

```typescript
import { describe, expect, it } from "vitest";
import { severityMeta, SEVERITY_ORDER } from "@/lib/severity";

describe("severityMeta", () => {
  it("maps critical to Arabic label حرجة", () => {
    expect(severityMeta("critical").labelAr).toBe("حرجة");
  });

  it("maps major to كبيرة", () => {
    expect(severityMeta("major").labelAr).toBe("كبيرة");
  });

  it("maps editorial to تحرير", () => {
    expect(severityMeta("editorial").labelAr).toBe("تحرير");
  });

  it("provides tailwind classes per severity", () => {
    expect(severityMeta("critical").badgeClass).toContain("red");
  });

  it("orders severities critical → major → editorial", () => {
    expect(SEVERITY_ORDER).toEqual(["critical", "major", "editorial"]);
  });
});
```

- [ ] **Step 2.5: Run — expect FAIL**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
npm run test 2>&1 | head -20
```

Expected: FAIL — `@/lib/severity` not found.

- [ ] **Step 2.6: Create `web/lib/severity.ts`**

```typescript
import type { Severity } from "@/lib/types";

export const SEVERITY_ORDER: Severity[] = ["critical", "major", "editorial"];

interface SeverityMeta {
  labelAr: string;
  badgeClass: string;
  borderClass: string;
}

const META: Record<Severity, SeverityMeta> = {
  critical: {
    labelAr: "حرجة",
    badgeClass: "bg-red-600 text-white",
    borderClass: "border-red-600 bg-red-50",
  },
  major: {
    labelAr: "كبيرة",
    badgeClass: "bg-amber-600 text-white",
    borderClass: "border-amber-600 bg-amber-50",
  },
  editorial: {
    labelAr: "تحرير",
    badgeClass: "bg-gray-400 text-white",
    borderClass: "border-gray-400 bg-gray-50",
  },
};

export function severityMeta(severity: Severity): SeverityMeta {
  return META[severity] ?? META.editorial;
}
```

- [ ] **Step 2.7: Run tests — expect PASS**

```bash
npm run test
```

Expected: severity tests PASS.

- [ ] **Step 2.8: Commit**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/lib/types.ts web/lib/severity.ts web/vitest.config.ts web/vitest.setup.ts web/__tests__/severity.test.ts
git commit -m "feat(mvp-web): types + severity mapping (TDD)"
```

---

## Task 3: API Client (TDD)

**Files:**
- Create: `web/lib/api.ts`
- Create: `web/__tests__/api.test.ts`

- [ ] **Step 3.1: Write the failing test `web/__tests__/api.test.ts`**

```typescript
import { afterEach, describe, expect, it, vi } from "vitest";
import { critiqueStreamUrl, getReport, postFeedback, uploadDocx } from "@/lib/api";

const API = "http://localhost:8000";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("critiqueStreamUrl", () => {
  it("builds the SSE url from token", () => {
    expect(critiqueStreamUrl("abc")).toBe(`${API}/sessions/abc/critique/stream`);
  });
});

describe("uploadDocx", () => {
  it("POSTs multipart and returns the session", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ share_token: "tok1", status: "queued" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const file = new File([new Uint8Array([1, 2, 3])], "t.docx");
    const res = await uploadDocx(file);

    expect(res.share_token).toBe("tok1");
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe(`${API}/sessions/upload`);
    expect(opts.method).toBe("POST");
    expect(opts.body).toBeInstanceOf(FormData);
  });

  it("throws on non-ok response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 422 }));
    const file = new File([new Uint8Array([1])], "t.pdf");
    await expect(uploadDocx(file)).rejects.toThrow(/422/);
  });
});

describe("getReport / postFeedback", () => {
  it("getReport fetches the report json", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ findings: [] }) }),
    );
    const r = await getReport("tok1");
    expect(r.findings).toEqual([]);
  });

  it("postFeedback POSTs json", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: "f1" }) });
    vi.stubGlobal("fetch", fetchMock);
    await postFeedback("tok1", { helpful: true, wants_more: true });
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe(`${API}/sessions/tok1/feedback`);
    expect(JSON.parse(opts.body).wants_more).toBe(true);
  });
});
```

- [ ] **Step 3.2: Run — expect FAIL**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
npm run test 2>&1 | head -20
```

Expected: FAIL — `@/lib/api` not found.

- [ ] **Step 3.3: Create `web/lib/api.ts`**

```typescript
import type { ReportResponse, SessionResponse } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function critiqueStreamUrl(token: string): string {
  return `${API}/sessions/${token}/critique/stream`;
}

export async function uploadDocx(
  file: File,
  tone = "constructive",
): Promise<SessionResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("tone", tone);
  const res = await fetch(`${API}/sessions/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed (${res.status})`);
  return res.json();
}

export async function getSession(token: string): Promise<SessionResponse> {
  const res = await fetch(`${API}/sessions/${token}`);
  if (!res.ok) throw new Error(`Session fetch failed (${res.status})`);
  return res.json();
}

export async function getReport(token: string): Promise<ReportResponse> {
  const res = await fetch(`${API}/sessions/${token}/report`);
  if (!res.ok) throw new Error(`Report fetch failed (${res.status})`);
  return res.json();
}

export interface FeedbackPayload {
  helpful?: boolean | null;
  comment?: string | null;
  wants_more?: boolean;
  contact_email?: string | null;
}

export async function postFeedback(token: string, payload: FeedbackPayload): Promise<void> {
  const res = await fetch(`${API}/sessions/${token}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Feedback failed (${res.status})`);
}
```

- [ ] **Step 3.4: Run tests — expect PASS**

```bash
npm run test
```

Expected: severity + api tests PASS.

- [ ] **Step 3.5: Commit**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/lib/api.ts web/__tests__/api.test.ts
git commit -m "feat(mvp-web): API client (upload/session/report/feedback) — TDD"
```

---

## Task 4: Shared Components

**Files:**
- Modify: `backend/app/schemas/session.py` (expose `jury_config`)
- Create: `web/components/SeverityBadge.tsx`
- Create: `web/components/FindingCard.tsx`
- Create: `web/components/JuryPreview.tsx`
- Create: `web/__tests__/SeverityBadge.test.tsx`

- [ ] **Step 4.1: Expose `jury_config` on the backend `SessionResponse`**

In `backend/app/schemas/session.py`, add this field to `SessionResponse` (after `detected_disciplines`):

```python
    jury_config: dict | None = None
```

Restart the backend (`docker compose restart backend`) so the frontend preview can read it.

- [ ] **Step 4.2: Write the failing component test `web/__tests__/SeverityBadge.test.tsx`**

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SeverityBadge } from "@/components/SeverityBadge";

describe("SeverityBadge", () => {
  it("renders the Arabic label for the severity", () => {
    render(<SeverityBadge severity="critical" />);
    expect(screen.getByText("حرجة")).toBeInTheDocument();
  });
});
```

- [ ] **Step 4.3: Run — expect FAIL**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
npm run test 2>&1 | head -20
```

Expected: FAIL — `@/components/SeverityBadge` not found.

- [ ] **Step 4.4: Create `web/components/SeverityBadge.tsx`**

```tsx
import { severityMeta } from "@/lib/severity";
import type { Severity } from "@/lib/types";

export function SeverityBadge({ severity }: { severity: Severity }) {
  const meta = severityMeta(severity);
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs ${meta.badgeClass}`}>
      {meta.labelAr}
    </span>
  );
}
```

- [ ] **Step 4.5: Create `web/components/FindingCard.tsx`**

```tsx
import { SeverityBadge } from "@/components/SeverityBadge";
import { severityMeta } from "@/lib/severity";
import type { Finding } from "@/lib/types";

export function FindingCard({ finding }: { finding: Finding }) {
  const meta = severityMeta(finding.severity);
  return (
    <div className={`rounded-lg border-r-4 p-3 ${meta.borderClass}`}>
      <div className="flex items-center gap-2">
        <SeverityBadge severity={finding.severity} />
        <span className="font-semibold">{finding.title}</span>
      </div>
      <p className="mt-1 text-sm leading-7 text-gray-700">{finding.body}</p>
      {finding.chapter_title && (
        <p className="mt-1 text-xs text-gray-400">{finding.chapter_title}</p>
      )}
    </div>
  );
}
```

- [ ] **Step 4.6: Create `web/components/JuryPreview.tsx`**

```tsx
import type { JuryConfig } from "@/lib/types";

export function JuryPreview({
  disciplines,
  jury,
}: {
  disciplines: string[] | null;
  jury?: JuryConfig | null;
}) {
  return (
    <div className="rounded-lg bg-[#f3eee0] p-3 text-sm">
      <div className="text-gray-500">التخصص المكتشف</div>
      <strong>{disciplines && disciplines.length ? disciplines.join("، ") : "قيد التحديد…"}</strong>
      {jury?.personas && jury.personas.length > 0 && (
        <>
          <div className="mt-2 text-gray-500">لجنة المناقشة</div>
          <div className="mt-1 flex flex-wrap gap-1">
            {jury.personas.map((p, i) => (
              <span key={i} className="rounded bg-[#e7dcc0] px-2 py-0.5 text-xs">
                {p.role}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 4.7: Run tests — expect PASS**

```bash
npm run test
```

Expected: all unit + component tests PASS.

- [ ] **Step 4.8: Commit**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add backend/app/schemas/session.py web/components/ web/__tests__/SeverityBadge.test.tsx
git commit -m "feat(mvp-web): shared components (SeverityBadge, FindingCard, JuryPreview) + expose jury_config"
```

---

## Task 5: Screen 1 — Upload & Configure

**Files:**
- Create: `web/app/page.tsx`

After upload, the page polls the session until it leaves `parsing` (chunking + jury done), shows the discipline + jury preview and the tone gate, then navigates to the critique screen on "ابدأ النقد".

- [ ] **Step 5.1: Create `web/app/page.tsx`**

```tsx
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { JuryPreview } from "@/components/JuryPreview";
import { getSession, uploadDocx } from "@/lib/api";
import type { SessionResponse } from "@/lib/types";

export default function UploadPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [toneAck, setToneAck] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setBusy(true);
    try {
      const s = await uploadDocx(file);
      setSession(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل الرفع");
    } finally {
      setBusy(false);
    }
  }

  // Poll until chunking + jury are ready (status leaves parsing/uploading).
  useEffect(() => {
    if (!session) return;
    if (session.detected_disciplines || session.jury_config) return;
    pollRef.current = setInterval(async () => {
      try {
        const s = await getSession(session.share_token);
        setSession(s);
        if (s.jury_config || s.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {
        /* keep polling */
      }
    }, 2000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [session]);

  const ready = !!session && (!!session.jury_config || !!session.detected_disciplines);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">رفع بحث</h1>

      {!session && (
        <label className="block cursor-pointer rounded-xl border-2 border-dashed border-accent p-8 text-center text-[#8a7a52]">
          {busy ? "جارٍ الرفع…" : "اختر ملف Word (.docx)"}
          <input type="file" accept=".docx" className="hidden" onChange={onFile} disabled={busy} />
        </label>
      )}

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {session && (
        <div className="space-y-3">
          {!ready && <p className="text-sm text-gray-500">جارٍ تحليل البنية وتجميع اللجنة…</p>}
          {ready && (
            <>
              <JuryPreview
                disciplines={session.detected_disciplines}
                jury={session.jury_config}
              />
              <label className="flex items-center gap-2 rounded-lg border p-3 text-sm">
                <input
                  type="checkbox"
                  checked={toneAck}
                  onChange={(e) => setToneAck(e.target.checked)}
                />
                أقر بأن النقد سيكون بنبرة بنّاءة (للباحث)
              </label>
              <button
                disabled={!toneAck}
                onClick={() => router.push(`/s/${session.share_token}/critique`)}
                className="w-full rounded-lg bg-accent px-4 py-2 text-white disabled:opacity-40"
              >
                ابدأ النقد ←
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5.2: Manual smoke (requires backend running with a real ANTHROPIC_API_KEY)**

```bash
# Terminal 1: backend
cd /Users/mohanedsayed/Researchers-Validation-Center && docker compose up -d
# Terminal 2: frontend
cd /Users/mohanedsayed/Researchers-Validation-Center/web && npm run dev
```

Open `http://localhost:3000`, upload a `.docx`. Expected: "جارٍ تحليل البنية…" then the discipline + jury preview appear, the tone-gate checkbox enables the "ابدأ النقد" button.

- [ ] **Step 5.3: Commit**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/app/page.tsx
git commit -m "feat(mvp-web): Upload & Configure screen (upload, poll, jury preview, tone gate)"
```

---

## Task 6: Screen 2 — Live Critique View (SSE)

**Files:**
- Create: `web/app/s/[token]/critique/page.tsx`

Consumes the backend SSE stream via `EventSource`, rendering findings live with a progress indicator, then navigates to the report on `done`.

- [ ] **Step 6.1: Create `web/app/s/[token]/critique/page.tsx`**

```tsx
"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { FindingCard } from "@/components/FindingCard";
import { critiqueStreamUrl } from "@/lib/api";
import type { Finding } from "@/lib/types";

interface Progress {
  chunk: number;
  total: number;
  chapter_title: string | null;
}

export default function CritiquePage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const router = useRouter();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!token) return;
    const es = new EventSource(critiqueStreamUrl(token));
    esRef.current = es;

    es.addEventListener("progress", (e) => {
      setProgress(JSON.parse((e as MessageEvent).data));
    });
    es.addEventListener("finding", (e) => {
      const f = JSON.parse((e as MessageEvent).data) as Finding;
      setFindings((prev) => [...prev, f]);
    });
    es.addEventListener("done", () => {
      es.close();
      router.push(`/s/${token}/report`);
    });
    es.addEventListener("error", (e) => {
      // Distinguish a server 'error' event from a transport drop.
      const data = (e as MessageEvent).data;
      if (data) {
        try {
          setError(JSON.parse(data).detail ?? "حدث خطأ");
        } catch {
          setError("حدث خطأ");
        }
      } else {
        setError("انقطع الاتصال بالخادم");
      }
      es.close();
    });

    return () => es.close();
  }, [token, router]);

  const pct = progress ? Math.round((progress.chunk / progress.total) * 100) : 5;

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">عرض النقد</h1>
      <div className="h-1.5 w-full overflow-hidden rounded bg-gray-200">
        <div className="h-full bg-accent transition-all" style={{ width: `${pct}%` }} />
      </div>
      {progress && (
        <p className="text-xs text-gray-500">
          الفصل {progress.chunk} من {progress.total}
          {progress.chapter_title ? ` · ${progress.chapter_title}` : ""} — يُكتب الآن…
        </p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="space-y-2">
        {findings.map((f, i) => (
          <FindingCard key={i} finding={f} />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 6.2: Manual smoke**

With backend + frontend running, complete an upload on `/`, click "ابدأ النقد". Expected: the progress bar advances, severity-tagged findings stream in one chapter at a time, then the page auto-navigates to `/s/<token>/report` when done.

- [ ] **Step 6.3: Commit**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/app/s/
git commit -m "feat(mvp-web): live Critique View (SSE findings + progress)"
```

---

## Task 7: Screen 3 — Report + Feedback (the demand instrument)

**Files:**
- Create: `web/components/FeedbackWidget.tsx`
- Create: `web/app/s/[token]/report/page.tsx`

- [ ] **Step 7.1: Create `web/components/FeedbackWidget.tsx`**

```tsx
"use client";

import { useState } from "react";
import { postFeedback } from "@/lib/api";

export function FeedbackWidget({ token }: { token: string }) {
  const [helpful, setHelpful] = useState<boolean | null>(null);
  const [wantsMore, setWantsMore] = useState(false);
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  async function send(nextHelpful: boolean | null, nextWantsMore: boolean) {
    setHelpful(nextHelpful);
    setWantsMore(nextWantsMore);
    try {
      await postFeedback(token, {
        helpful: nextHelpful,
        wants_more: nextWantsMore,
        contact_email: email || null,
      });
      setSent(true);
    } catch {
      /* swallow — feedback is best-effort */
    }
  }

  return (
    <div className="rounded-lg border border-emerald-300 bg-emerald-50 p-4 text-center text-sm">
      <div className="mb-2">هل كان هذا التقرير مفيدًا؟</div>
      <div className="flex justify-center gap-3">
        <button
          onClick={() => send(true, wantsMore)}
          className={`rounded px-3 py-1 ${helpful === true ? "bg-emerald-600 text-white" : "bg-white border"}`}
        >
          👍 نعم
        </button>
        <button
          onClick={() => send(false, wantsMore)}
          className={`rounded px-3 py-1 ${helpful === false ? "bg-gray-600 text-white" : "bg-white border"}`}
        >
          👎 لا
        </button>
      </div>

      <div className="mt-4 border-t border-emerald-200 pt-3">
        <div className="font-semibold text-emerald-700">تريد نقد أبحاث أكثر؟</div>
        <input
          type="email"
          dir="ltr"
          placeholder="بريدك الإلكتروني"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-2 w-full rounded border px-2 py-1 text-center"
        />
        <button
          onClick={() => send(helpful, true)}
          className="mt-2 w-full rounded bg-emerald-600 px-3 py-1.5 text-white"
        >
          أبلغوني عند توفّر المزيد ←
        </button>
      </div>

      {sent && <p className="mt-2 text-emerald-700">شكرًا لك — تم تسجيل ملاحظتك.</p>}
    </div>
  );
}
```

- [ ] **Step 7.2: Create `web/app/s/[token]/report/page.tsx`**

```tsx
"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { FeedbackWidget } from "@/components/FeedbackWidget";
import { FindingCard } from "@/components/FindingCard";
import { severityMeta, SEVERITY_ORDER } from "@/lib/severity";
import { getReport } from "@/lib/api";
import type { ReportResponse } from "@/lib/types";

export default function ReportPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    getReport(token)
      .then(setReport)
      .catch((e) => setError(e instanceof Error ? e.message : "تعذّر جلب التقرير"));
  }, [token]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!report) return <p className="text-sm text-gray-500">جارٍ تحميل التقرير…</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">التقرير</h1>
        <button
          onClick={() => window.print()}
          className="rounded-lg bg-ink px-3 py-1.5 text-sm text-white"
        >
          تنزيل / طباعة PDF
        </button>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        {SEVERITY_ORDER.map((sev) => (
          <span key={sev} className={`rounded px-2 py-1 ${severityMeta(sev).badgeClass}`}>
            {report.severity_counts[sev] ?? 0} {severityMeta(sev).labelAr}
          </span>
        ))}
      </div>

      <div className="space-y-2">
        {report.findings.map((f) => (
          <FindingCard key={f.id} finding={f} />
        ))}
      </div>

      <FeedbackWidget token={token} />
    </div>
  );
}
```

- [ ] **Step 7.3: Run the unit suite (ensure nothing broke)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
npm run test
```

Expected: all unit + component tests PASS.

- [ ] **Step 7.4: Manual smoke — the full happy path**

With backend + frontend running: upload a `.docx` → watch streaming critique → land on the report → see severity counts + findings → click 👍 and "أبلغوني…". Then confirm the feedback persisted:

```bash
docker compose exec db psql -U naqqad -c "SELECT helpful, wants_more, contact_email FROM feedback ORDER BY created_at DESC LIMIT 1;"
```

Expected: a row reflecting your click.

- [ ] **Step 7.5: Commit**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/components/FeedbackWidget.tsx web/app/s/
git commit -m "feat(mvp-web): Report screen + feedback widget (demand instrument)"
```

---

## Task 8: Dockerize the Frontend

**Files:**
- Create: `web/Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 8.1: Create `web/Dockerfile`**

```dockerfile
FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

CMD ["npm", "run", "dev"]
```

- [ ] **Step 8.2: Add the `web` service to `docker-compose.yml`**

Add under `services:` (sibling of `backend`):

```yaml
  web:
    build: ./web
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./web:/app
      - /app/node_modules
```

- [ ] **Step 8.3: Verify the full stack comes up**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
docker compose up -d --build
docker compose ps
curl -s http://localhost:3000 | head -5
```

Expected: all services running; the frontend HTML (with `dir="rtl"` / `lang="ar"`) is served on port 3000.

- [ ] **Step 8.4: Commit**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/Dockerfile docker-compose.yml
git commit -m "feat(mvp-web): dockerize frontend; full-stack compose"
```

---

## Self-Review Checklist

**Spec coverage (MVP design §6 — the three screens):**
- [x] Arabic-first RTL UI (`lang="ar"`, `dir="rtl"`, right-aligned) → Task 1
- [x] Screen 1 — Upload & Configure: `.docx` upload, discipline + jury preview, tone gate → Task 5
- [x] Screen 2 — live Critique View: SSE streaming findings, severity badges, progress bar → Task 6
- [x] Screen 3 — Report: grouped findings + severity counts, download/print, feedback → Task 7
- [x] "was this useful? / want more?" demand instrument (👍/👎 + email capture) → Task 7
- [x] Anonymous, share_token-addressed routing (`/s/[token]/...`) → Tasks 5–7
- [x] Severity labels حرجة/كبيرة/تحرير → Task 2 (TDD)
- [x] Full-stack docker-compose (web + backend) → Task 8

**Placeholder scan:** none — every step has complete code. Manual smoke steps are used only for inherently-visual screens (Tasks 5/6/7 smoke), with unit/component tests (TDD) for severity mapping, the API client, and SeverityBadge.

**Type consistency:** `Severity = "critical"|"major"|"editorial"` (types.ts) matches the backend enum (Plan 2 Task 1) and `severity.ts` mapping. `SessionResponse.jury_config` (types.ts) is backed by the backend field added in Task 4.1. `critiqueStreamUrl`/`uploadDocx`/`getSession`/`getReport`/`postFeedback` (api.ts) are consumed with matching signatures in pages (Tasks 5–7). SSE event names `progress`/`finding`/`done`/`error` match the backend `_sse(...)` emitters (Plan 2 Task 5).
```
