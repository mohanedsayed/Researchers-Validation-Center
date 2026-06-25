# نقّاد MVP — الخطة 3: واجهة Next.js أمامية بنظام RTL (الشاشات الثلاث)

> **للعاملين الوكلاء (agentic workers):** مهارة فرعية مطلوبة: استخدم subagent-driven-development (موصى به) أو build لتنفيذ هذه الخطة مهمةً تلو الأخرى. تستخدم الخطوات صياغة مربعات الاختيار (`- [ ]`) للتتبع.

**الهدف:** بناء واجهة الويب العربية أولًا بنظام RTL للمسار السعيد في الـ MVP: **الرفع والإعداد ← عرض النقد الحي (SSE) ← التقرير** مع أداة التغذية الراجعة "هل كان هذا مفيدًا؟ / هل تريد المزيد؟" — في تخاطب مع الواجهة الخلفية الخاصة بالخطة 1 + الخطة 2.

**البنية المعمارية:** Next.js (App Router) + Tailwind، مع `dir="rtl"` / `lang="ar"` عند الجذر. يُختبر المنطق الصرف (تعيين الخطورة، عميل الـ API) اختبارًا وحدويًا بأداة Vitest؛ ويستهلك عرض النقد المتدفق تدفّق SSE الصادر عن الواجهة الخلفية عبر واجهة المتصفح `EventSource` API؛ وتُتحقَّق الشاشات المرئية عبر خطوات فحص دخان يدوية (manual smoke). تُعنوَن الجلسات على نحو مجهول عبر `share_token` في عنوان الـ URL (`/s/[token]/...`).

**حزمة التقنيات:** Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS · Vitest + @testing-library/react · واجهة المتصفح `EventSource`

**يعتمد على:** [الخطة 1](2026-06-22-naqqad-mvp-plan1-backend-foundation.md) + [الخطة 2](2026-06-22-naqqad-mvp-plan2-critique-streaming.md) (واجهة الـ API الخلفية). **ذات صلة:** [مواصفة تصميم الـ MVP](../specs/2026-06-22-naqqad-mvp-design.md) (نموذج الشاشات الثلاث).

---

## بنية الملفات

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

> **دليل العمل (Working directory):** `/Users/mohanedsayed/Researchers-Validation-Center`؛ تُنفَّذ أوامر الواجهة الأمامية من `/Users/mohanedsayed/Researchers-Validation-Center/web`.

---

## المهمة 1: تهيئة Next.js + Tailwind + RTL

**الملفات:**
- إنشاء: `web/package.json`، `web/next.config.mjs`، `web/tsconfig.json`، `web/tailwind.config.ts`، `web/postcss.config.mjs`، `web/.env.local.example`
- إنشاء: `web/app/layout.tsx`، `web/app/globals.css`

- [ ] **الخطوة 1.1: إنشاء `web/package.json`**

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

- [ ] **الخطوة 1.2: إنشاء `web/next.config.mjs`**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

- [ ] **الخطوة 1.3: إنشاء `web/tsconfig.json`**

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

- [ ] **الخطوة 1.4: إنشاء `web/tailwind.config.ts`**

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

- [ ] **الخطوة 1.5: إنشاء `web/postcss.config.mjs`**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **الخطوة 1.6: إنشاء `web/.env.local.example`**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **الخطوة 1.7: إنشاء `web/app/globals.css`**

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

- [ ] **الخطوة 1.8: إنشاء `web/app/layout.tsx`**

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

- [ ] **الخطوة 1.9: تثبيت الاعتماديات والتحقق من إقلاع خادم التطوير**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
cp .env.local.example .env.local
npm install
npm run dev
```

المتوقَّع: يبدأ خادم التطوير الخاص بـ Next.js على `http://localhost:3000` (زُره: يُعرَض ترويسة RTL "نَقّاد" بمحاذاة إلى اليمين). أوقفه بـ Ctrl-C.

- [ ] **الخطوة 1.10: الالتزام (Commit)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/package.json web/next.config.mjs web/tsconfig.json web/tailwind.config.ts web/postcss.config.mjs web/.env.local.example web/app/layout.tsx web/app/globals.css web/package-lock.json
git commit -m "feat(mvp-web): scaffold Next.js + Tailwind, RTL Arabic layout"
```

---

## المهمة 2: الأنواع + تعيين الخطورة (TDD)

**الملفات:**
- إنشاء: `web/lib/types.ts`
- إنشاء: `web/lib/severity.ts`
- إنشاء: `web/vitest.config.ts`، `web/vitest.setup.ts`
- إنشاء: `web/__tests__/severity.test.ts`

- [ ] **الخطوة 2.1: إنشاء `web/vitest.config.ts`**

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

- [ ] **الخطوة 2.2: إنشاء `web/vitest.setup.ts`**

```typescript
import "@testing-library/jest-dom/vitest";
```

- [ ] **الخطوة 2.3: إنشاء `web/lib/types.ts`**

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

> ملاحظة: لا يتضمّن `SessionResponse` في الواجهة الخلفية الحقل `jury_config` ضمن مخطّط الخطة 2. قبل استهلاك ذلك في المهمة 4، أضِف `jury_config: dict | None` إلى `SessionResponse` في `backend/app/schemas/session.py` (سطر واحد) وأعِد البناء — انظر المهمة 4، الخطوة 4.1.

- [ ] **الخطوة 2.4: كتابة الاختبار الفاشل `web/__tests__/severity.test.ts`**

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

- [ ] **الخطوة 2.5: التشغيل — تَوقَّع الفشل (FAIL)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
npm run test 2>&1 | head -20
```

المتوقَّع: فشل (FAIL) — `@/lib/severity` غير موجود.

- [ ] **الخطوة 2.6: إنشاء `web/lib/severity.ts`**

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

- [ ] **الخطوة 2.7: تشغيل الاختبارات — تَوقَّع النجاح (PASS)**

```bash
npm run test
```

المتوقَّع: نجاح اختبارات الخطورة (PASS).

- [ ] **الخطوة 2.8: الالتزام (Commit)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/lib/types.ts web/lib/severity.ts web/vitest.config.ts web/vitest.setup.ts web/__tests__/severity.test.ts
git commit -m "feat(mvp-web): types + severity mapping (TDD)"
```

---

## المهمة 3: عميل الـ API (TDD)

**الملفات:**
- إنشاء: `web/lib/api.ts`
- إنشاء: `web/__tests__/api.test.ts`

- [ ] **الخطوة 3.1: كتابة الاختبار الفاشل `web/__tests__/api.test.ts`**

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

- [ ] **الخطوة 3.2: التشغيل — تَوقَّع الفشل (FAIL)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
npm run test 2>&1 | head -20
```

المتوقَّع: فشل (FAIL) — `@/lib/api` غير موجود.

- [ ] **الخطوة 3.3: إنشاء `web/lib/api.ts`**

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

- [ ] **الخطوة 3.4: تشغيل الاختبارات — تَوقَّع النجاح (PASS)**

```bash
npm run test
```

المتوقَّع: نجاح اختبارات الخطورة + الـ API (PASS).

- [ ] **الخطوة 3.5: الالتزام (Commit)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/lib/api.ts web/__tests__/api.test.ts
git commit -m "feat(mvp-web): API client (upload/session/report/feedback) — TDD"
```

---

## المهمة 4: المكوّنات المشتركة

**الملفات:**
- تعديل: `backend/app/schemas/session.py` (إظهار `jury_config`)
- إنشاء: `web/components/SeverityBadge.tsx`
- إنشاء: `web/components/FindingCard.tsx`
- إنشاء: `web/components/JuryPreview.tsx`
- إنشاء: `web/__tests__/SeverityBadge.test.tsx`

- [ ] **الخطوة 4.1: إظهار `jury_config` في `SessionResponse` الخاص بالواجهة الخلفية**

في `backend/app/schemas/session.py`، أضِف هذا الحقل إلى `SessionResponse` (بعد `detected_disciplines`):

```python
    jury_config: dict | None = None
```

أعِد تشغيل الواجهة الخلفية (`docker compose restart backend`) كي يتمكّن معاينة الواجهة الأمامية من قراءته.

- [ ] **الخطوة 4.2: كتابة اختبار المكوّن الفاشل `web/__tests__/SeverityBadge.test.tsx`**

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

- [ ] **الخطوة 4.3: التشغيل — تَوقَّع الفشل (FAIL)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
npm run test 2>&1 | head -20
```

المتوقَّع: فشل (FAIL) — `@/components/SeverityBadge` غير موجود.

- [ ] **الخطوة 4.4: إنشاء `web/components/SeverityBadge.tsx`**

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

- [ ] **الخطوة 4.5: إنشاء `web/components/FindingCard.tsx`**

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

- [ ] **الخطوة 4.6: إنشاء `web/components/JuryPreview.tsx`**

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

- [ ] **الخطوة 4.7: تشغيل الاختبارات — تَوقَّع النجاح (PASS)**

```bash
npm run test
```

المتوقَّع: نجاح جميع الاختبارات الوحدوية + اختبارات المكوّنات (PASS).

- [ ] **الخطوة 4.8: الالتزام (Commit)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add backend/app/schemas/session.py web/components/ web/__tests__/SeverityBadge.test.tsx
git commit -m "feat(mvp-web): shared components (SeverityBadge, FindingCard, JuryPreview) + expose jury_config"
```

---

## المهمة 5: الشاشة 1 — الرفع والإعداد

**الملفات:**
- إنشاء: `web/app/page.tsx`

بعد الرفع، تستفتي الصفحة (poll) الجلسةَ حتى تغادر حالة `parsing` (اكتمال التقطيع + اللجنة)، ثم تعرض التخصص + معاينة اللجنة وبوابة النبرة (tone gate)، ثم تنتقل إلى شاشة النقد عند النقر على "ابدأ النقد".

- [ ] **الخطوة 5.1: إنشاء `web/app/page.tsx`**

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

- [ ] **الخطوة 5.2: فحص دخان يدوي (يتطلّب تشغيل الواجهة الخلفية مع مفتاح ANTHROPIC_API_KEY حقيقي)**

```bash
# Terminal 1: backend
cd /Users/mohanedsayed/Researchers-Validation-Center && docker compose up -d
# Terminal 2: frontend
cd /Users/mohanedsayed/Researchers-Validation-Center/web && npm run dev
```

افتح `http://localhost:3000`، وارفع ملف `.docx`. المتوقَّع: تظهر "جارٍ تحليل البنية…" ثم يظهر التخصص + معاينة اللجنة، ويُفعِّل مربعُ اختيار بوابة النبرة الزرَّ "ابدأ النقد".

- [ ] **الخطوة 5.3: الالتزام (Commit)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/app/page.tsx
git commit -m "feat(mvp-web): Upload & Configure screen (upload, poll, jury preview, tone gate)"
```

---

## المهمة 6: الشاشة 2 — عرض النقد الحي (SSE)

**الملفات:**
- إنشاء: `web/app/s/[token]/critique/page.tsx`

تستهلك تدفّق SSE الصادر عن الواجهة الخلفية عبر `EventSource`، وتعرض الملاحظات (findings) على نحو حي مع مؤشّر تقدّم، ثم تنتقل إلى التقرير عند حدث `done`.

- [ ] **الخطوة 6.1: إنشاء `web/app/s/[token]/critique/page.tsx`**

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

- [ ] **الخطوة 6.2: فحص دخان يدوي**

مع تشغيل الواجهة الخلفية + الأمامية، أكمِل عملية رفع على `/`، ثم انقر "ابدأ النقد". المتوقَّع: يتقدّم شريط التقدّم، وتتدفّق الملاحظات الموسومة بالخطورة فصلًا فصلًا، ثم تنتقل الصفحة تلقائيًا إلى `/s/<token>/report` عند الانتهاء.

- [ ] **الخطوة 6.3: الالتزام (Commit)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/app/s/
git commit -m "feat(mvp-web): live Critique View (SSE findings + progress)"
```

---

## المهمة 7: الشاشة 3 — التقرير + التغذية الراجعة (أداة الطلب)

**الملفات:**
- إنشاء: `web/components/FeedbackWidget.tsx`
- إنشاء: `web/app/s/[token]/report/page.tsx`

- [ ] **الخطوة 7.1: إنشاء `web/components/FeedbackWidget.tsx`**

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

- [ ] **الخطوة 7.2: إنشاء `web/app/s/[token]/report/page.tsx`**

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

- [ ] **الخطوة 7.3: تشغيل مجموعة الاختبارات الوحدوية (للتأكد من عدم انكسار شيء)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center/web
npm run test
```

المتوقَّع: نجاح جميع الاختبارات الوحدوية + اختبارات المكوّنات (PASS).

- [ ] **الخطوة 7.4: فحص دخان يدوي — المسار السعيد الكامل**

مع تشغيل الواجهة الخلفية + الأمامية: ارفع ملف `.docx` ← شاهِد النقد المتدفّق ← اهبط على التقرير ← شاهِد أعداد الخطورة + الملاحظات ← انقر 👍 و"أبلغوني…". ثم أكِّد أن التغذية الراجعة قد حُفظت:

```bash
docker compose exec db psql -U naqqad -c "SELECT helpful, wants_more, contact_email FROM feedback ORDER BY created_at DESC LIMIT 1;"
```

المتوقَّع: صفّ يعكس نقرتك.

- [ ] **الخطوة 7.5: الالتزام (Commit)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/components/FeedbackWidget.tsx web/app/s/
git commit -m "feat(mvp-web): Report screen + feedback widget (demand instrument)"
```

---

## المهمة 8: حوسبة الواجهة الأمامية في Docker

**الملفات:**
- إنشاء: `web/Dockerfile`
- تعديل: `docker-compose.yml`

- [ ] **الخطوة 8.1: إنشاء `web/Dockerfile`**

```dockerfile
FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

CMD ["npm", "run", "dev"]
```

- [ ] **الخطوة 8.2: إضافة خدمة `web` إلى `docker-compose.yml`**

أضِف تحت `services:` (شقيقة لـ `backend`):

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

- [ ] **الخطوة 8.3: التحقق من إقلاع الحزمة الكاملة (full stack)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
docker compose up -d --build
docker compose ps
curl -s http://localhost:3000 | head -5
```

المتوقَّع: تشغيل جميع الخدمات؛ وتقديم HTML الخاص بالواجهة الأمامية (مع `dir="rtl"` / `lang="ar"`) على المنفذ 3000.

- [ ] **الخطوة 8.4: الالتزام (Commit)**

```bash
cd /Users/mohanedsayed/Researchers-Validation-Center
git add web/Dockerfile docker-compose.yml
git commit -m "feat(mvp-web): dockerize frontend; full-stack compose"
```

---

## قائمة المراجعة الذاتية

**تغطية المواصفة (تصميم الـ MVP §6 — الشاشات الثلاث):**
- [x] واجهة عربية أولًا بنظام RTL (`lang="ar"`، `dir="rtl"`، محاذاة إلى اليمين) ← المهمة 1
- [x] الشاشة 1 — الرفع والإعداد: رفع `.docx`، التخصص + معاينة اللجنة، بوابة النبرة ← المهمة 5
- [x] الشاشة 2 — عرض النقد الحي: تدفّق ملاحظات SSE، شارات الخطورة، شريط التقدّم ← المهمة 6
- [x] الشاشة 3 — التقرير: ملاحظات مُجمَّعة + أعداد الخطورة، تنزيل/طباعة، تغذية راجعة ← المهمة 7
- [x] أداة الطلب "هل كان هذا مفيدًا؟ / هل تريد المزيد؟" (👍/👎 + التقاط البريد الإلكتروني) ← المهمة 7
- [x] توجيه (routing) مجهول معنوَن بـ share_token (`/s/[token]/...`) ← المهام 5–7
- [x] تسميات الخطورة حرجة/كبيرة/تحرير ← المهمة 2 (TDD)
- [x] docker-compose للحزمة الكاملة (web + backend) ← المهمة 8

**فحص العناصر النائبة (Placeholder scan):** لا شيء — كل خطوة تحمل شيفرة كاملة. تُستخدَم خطوات فحص الدخان اليدوية فقط للشاشات المرئية بطبيعتها (فحص دخان المهام 5/6/7)، مع اختبارات وحدوية/اختبارات مكوّنات (TDD) لتعيين الخطورة، وعميل الـ API، و SeverityBadge.

**اتساق الأنواع:** `Severity = "critical"|"major"|"editorial"` (types.ts) يطابق تعداد (enum) الواجهة الخلفية (الخطة 2 المهمة 1) وتعيين `severity.ts`. الحقل `SessionResponse.jury_config` (types.ts) مدعوم بحقل الواجهة الخلفية المُضاف في المهمة 4.1. وتُستهلَك `critiqueStreamUrl`/`uploadDocx`/`getSession`/`getReport`/`postFeedback` (api.ts) بتواقيع (signatures) متطابقة في الصفحات (المهام 5–7). وتطابق أسماء أحداث SSE `progress`/`finding`/`done`/`error` باعثات `_sse(...)` في الواجهة الخلفية (الخطة 2 المهمة 5).
```
