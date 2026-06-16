# 02_SRS_Software_Specifications.md

# مواصفات متطلبات البرمجيات (SRS)
## اسم المشروع: المنصة الذكية للتحكيم الأكاديمي الشامل (SARA)
**(Smart Academic Review Architecture - Multi-Expert Platform)**

---

| **معلومات الوثيقة** | **التفاصيل** |
| :--- | :--- |
| **الإصدار** | 1.1 |
| **التاريخ** | 25 يناير 2025 |
| **المرجع** | مبني على BRD v1.1 |
| **الجمهور المستهدف** | فريق التطوير (Backend/Frontend)، مهندسو DevOps، مختبرو الجودة (QA) |

---

## 1. مقدمة (Introduction)

### 1.1 الغرض (Purpose)
تهدف هذه الوثيقة إلى تحديد المتطلبات البرمجية التفصيلية لبناء منصة **SARA**. تغطي الوثيقة المعمارية التقنية، نماذج البيانات، واجهات برمجة التطبيقات (APIs)، والمنطق البرمجي اللازم لتحقيق أهداف العمل الموضحة في وثيقة BRD.

### 1.2 نطاق النظام (System Scope)
نظام **SARA** هو تطبيق ويب سحابي (Cloud-Native Web Application) يعتمد على الذكاء الاصطناعي التوليدي (GenAI). يتكون النظام من:
1.  **واجهة أمامية (Frontend):** تفاعلية لبناء تجربة مستخدم سلسة وعرض التقارير المعقدة.
2.  **خادم خلفي (Backend):** عالي الأداء لإدارة عمليات المعالجة المتوازية والتكامل مع نماذج الذكاء الاصطناعي.
3.  **محرك الذكاء (AI Engine):** نواة النظام المسؤولة عن تحليل، نقد، وتوليد التقارير.
4.  **بنية تحتية (Infrastructure):** للتخزين الآمن وإدارة قواعد البيانات.

---

## 2. المعمارية التقنية (Technical Architecture)

### 2.1 المكدس التقني (Technology Stack)

| المكون (Component) | التقنية (Technology) | المبررات (Rationale) |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | اللغة المعيارية للذكاء الاصطناعي والتعامل مع البيانات. |
| **Backend Framework** | **FastAPI** | دعم أصلي للعمليات غير المتزامنة (Async/Await) الضرورية لطلبات الـ AI الطويلة، والتحقق الصارم من البيانات (Pydantic). |
| **Database** | **PostgreSQL (v15+)** | دعم قوي لـ `JSONB` لتخزين نتائج النقد المرنة، ودعم `pgvector` للمستقبل. استخدام **SQLAlchemy (Async)** و **Alembic**. |
| **Frontend Framework** | **React.js (Next.js)** | تجربة مستخدم تفاعلية (SPA)، SEO جيد، ودعم ممتاز لمكونات UI الحديثة. |
| **File Storage** | **AWS S3** | أمان عالي (Encryption at Rest)، تكلفة منخفضة، وقابلية توسع غير محدودة. |
| **AI Provider** | **Google Gemini API** | نافذة سياق كبيرة (Context Window) لمعالجة الأبحاث الطويلة، ودعم متعدد اللغات. |
| **Task Queue** | **FastAPI BackgroundTasks** | للمعالجة الخلفية البسيطة (يمكن الترقية لـ Celery + Redis عند الحاجة للتوسع الضخم). |
| **Payment Gateway** | **Stripe API** | دعم عالمي، توثيق ممتاز، ومعالجة آمنة للمدفوعات. |
| **Authentication** | **JWT (Custom Implementation)** | تحكم كامل في البيانات والجلسات دون الاعتماد على طرف ثالث مكلف. |

### 2.2 المتطلبات العامة للنظام (System Constraints)
*   **SC-01:** يجب أن يعمل النظام بالكامل في بيئة Dockerized لسهولة النشر.
*   **SC-02:** جميع الاستجابات من الـ API يجب أن تكون بتنسيق JSON.
*   **SC-03:** الوقت الأقصى لرفع الملف (Upload Timeout) هو 5 دقائق.
*   **SC-04:** الوقت الأقصى لمعالجة الطلب الواحد (Processing Timeout) هو 10 دقائق (يتم التعامل مع هذا عبر Polling).

---

## 3. المتطلبات الوظيفية التفصيلية (Detailed Functional Requirements)

### 3.1 وحدة المصادقة والمستخدمين (Auth & User Module)
*   **FR-AUTH-01: التسجيل وتسجيل الدخول:**
    *   دعم التسجيل بالبريد الإلكتروني وكلمة المرور.
    *   تشفير كلمات المرور باستخدام **Argon2** أو **Bcrypt**.
    *   إصدار رموز وصول (Access Tokens) ورموز تحديث (Refresh Tokens) بصيغة JWT.
*   **FR-AUTH-02: إدارة الملف الشخصي:**
    *   تخزين تفضيلات المستخدم (اللغة الافتراضية، الدور الافتراضي).
    *   عرض سجل الرصيد والمعاملات المالية.

### 3.2 وحدة إدارة الجلسات والملفات (Session & File Module)
*   **FR-SESS-01: رفع الملفات:**
    *   قبول ملفات بصيغة `.docx` و `.pdf`.
    *   التحقق من صحة الملف (Magic Bytes Check) لمنع رفع ملفات خبيثة.
    *   تشفير الملف بمفتاح فريد (Symmetric Key) قبل رفعه إلى S3.
*   **FR-SESS-02: التحليل الهيكلي (Parsing):**
    *   استخدام مكتبة `python-docx` لاستخراج النصوص، العناوين، الجداول، والحواشي.
    *   إنشاء "هيكل عظمي" (Skeleton JSON) يحتوي على معرفات الفقرات (Ref-IDs) والعناوين.
*   **FR-SESS-03: إدارة دورة الحياة:**
    *   تنفيذ مهمة مجدولة (Cron Job) كل ساعة لفحص الجلسات المنتهية (>24 ساعة).
    *   حذف الملفات من S3 وسجلات النقد من قاعدة البيانات نهائياً.

### 3.3 وحدة الذكاء المركزي (Core Intelligence Engine)
*   **FR-CORE-01: تحديد التخصص (Profiling):**
    *   تحليل العنوان والملخص لتحديد التخصصات (Tags) واللغة.
*   **FR-CORE-02: إدارة المعرفة (DSE Logic):**
    *   التحقق من وجود التخصص في جدول `Domains`.
    *   إذا كان التخصص جديداً، استدعاء Gemini لتوليد "تعليمات نقد" (Prompt Template) وحفظها بحالة `DRAFT`.
*   **FR-CORE-03: معالجة الدفعات (Semantic Batching):**
    *   تقسيم "الهيكل العظمي" إلى وحدات موضوعية (Batches) لا تقطع السياق (مثلاً: فصل كامل أو مبحث كامل).
    *   تخزين خطة المعالجة (Start_ID -> End_ID) في `batch_schedule`.
*   **FR-CORE-04: التنفيذ المتوازي (Parallel Execution):**
    *   إرسال الدفعات بشكل متزامن (Async Gather) إلى Gemini API.
    *   إرفاق "ملف السياق الكامل" (File API) في كل طلب لضمان دقة النقد.
    *   إلزام النموذج بإخراج النتائج بصيغة JSON الموحدة (Universal Response Protocol).

### 3.4 وحدة التقارير والتجميع (Assembler & Reporting Module)
*   **FR-REP-01: تجميع النتائج:**
    *   دمج ملفات JSON الجزئية (من كل دفعة) في كائن JSON واحد كبير.
    *   فلترة النتائج بناءً على المستوى المطلوب (Summary/Standard/Deep).
*   **FR-REP-02: التوليد النهائي:**
    *   توليد ملف Markdown منسق يحتوي على الجداول والإحصائيات.
    *   تحويل Markdown إلى PDF (باستخدام مكتبة مثل `WeasyPrint` أو `ReportLab`) عند الطلب.
*   **FR-REP-03: الترجمة:**
    *   إذا كانت `target_language` مختلفة عن لغة البحث، يتم ترجمة "المحتوى التفسيري" فقط في التقرير (وليس الاقتباسات الأصلية).

### 3.5 وحدة المدفوعات (Billing Module)
*   **FR-PAY-01: بوابة Stripe:**
    *   إنشاء `Checkout Session` لشراء الرصيد.
    *   معالجة الـ `Webhooks` لتأكيد الدفع وتحديث رصيد المستخدم في قاعدة البيانات بشكل آمن (Atomic Transaction).
*   **FR-PAY-02: استهلاك الرصيد:**
    *   خصم الرصيد عند بدء عملية النقد (وليس عند الرفع).
    *   إعادة الرصيد في حال فشل المعالجة التقنية (System Failure).

---

## 4. نماذج البيانات (Data Models - Schema Definition)

### 4.1 Users Table
| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | المعرف الفريد |
| `email` | String | Unique, Index | البريد الإلكتروني |
| `hashed_password` | String | Not Null | كلمة المرور المشفرة |
| `credits` | Integer | Default 0 | رصيد النقاط |
| `role` | Enum | [STUDENT, REVIEWER, ADMIN] | دور المستخدم |
| `created_at` | Timestamp | | |

### 4.2 Domains Table (Knowledge Library)
| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `name` | String | Unique | اسم التخصص (مثلاً: "Quantum Physics") |
| `optimized_instruction` | Text | Not Null | التعليمات المولدة من DSE |
| `status` | Enum | [ACTIVE, PENDING] | حالة الاعتماد |

### 4.3 Sessions Table
| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `user_id` | UUID | FK -> Users | |
| `s3_key` | String | Not Null | مسار الملف في S3 |
| `title` | String | | عنوان البحث |
| `skeleton` | JSONB | | الهيكل العظمي للبحث |
| `batch_schedule` | JSONB | | خطة تقسيم الدفعات |
| `config` | JSONB | | (اللغة، الدور، الجامعة) |
| `status` | Enum | [UPLOADING, PROCESSING, COMPLETED] | حالة الجلسة |
| `created_at` | Timestamp | | |

### 4.4 CritiqueLogs Table
| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BigInt | PK | |
| `session_id` | UUID | FK -> Sessions | |
| `batch_index` | Integer | | ترتيب الدفعة |
| `content` | JSONB | Not Null | النقد الخام (JSON) |

---

## 5. واجهات برمجة التطبيقات (API Contract)

### 5.1 Authentication
*   `POST /api/v1/auth/register` (Email, Password) -> User
*   `POST /api/v1/auth/login` (Email, Password) -> {access_token, refresh_token}

### 5.2 Sessions Management
*   `POST /api/v1/sessions/upload` (File, Config) -> {session_id, cost}
*   `POST /api/v1/sessions/{id}/analyze` -> {status: "STARTED"}
*   `GET /api/v1/sessions/{id}/status` -> {progress: 50%, step: "Batch 5/10"}
*   `GET /api/v1/sessions/{id}/report` (Query: format=pdf) -> File Download

### 5.3 Admin Operations
*   `GET /api/v1/admin/domains?status=PENDING` -> List of new domains
*   `PUT /api/v1/admin/domains/{id}` (Approve/Edit) -> Domain updated

---

## 6. متطلبات الجودة والأمان (Quality & Security Attributes)

### 6.1 الأمان (Security)
*   **التشفير:** استخدام `Fernet` (Symmetric Encryption) لتشفير الملفات قبل رفعها.
*   **التحقق:** جميع الـ Endpoints المحمية تتطلب `Bearer Token` صالح.
*   **عزل BYOK:** مفاتيح API الخاصة بالمستخدمين في الوضع المجاني لا تُخزن أبداً في قاعدة البيانات، بل تُمرر في الذاكرة (In-Memory) فقط أثناء الجلسة.

### 6.2 الموثوقية (Reliability)
*   **إعادة المحاولة (Retry Logic):** استخدام مكتبة `tenacity` لإعادة محاولة طلبات Gemini في حال حدوث خطأ `429 Too Many Requests` أو `503 Service Unavailable`.
*   **التسجيل (Logging):** تسجيل هيكلي (Structured Logging) لكل خطوة في ملفات منفصلة أثناء وضع التطوير (DEV_MODE) لتسهيل التنقيح.

### 6.3 الأداء (Performance)
*   استخدام `asyncio.gather` لمعالجة الدفعات بالتوازي.
*   استخدام `gemini-1.5-flash` للمهام البسيطة (مثل التقسيم الهيكلي) للسرعة، و `gemini-1.5-pro` للمهام المعقدة (DSE والنقد).

---

## 7. خارطة طريق التنفيذ (Implementation Roadmap)

1.  **Phase 1: Skeleton & Parsing:** بناء الـ Document Parser وقاعدة البيانات.
2.  **Phase 2: Core Engine (DSE):** بناء منطق توليد التعليمات وإدارة التخصصات.
3.  **Phase 3: The Critique Loop:** تنفيذ المعالجة المتوازية والتكامل مع Gemini.
4.  **Phase 4: Reporting & UI:** بناء واجهة React وتوليد التقارير النهائية.
5.  **Phase 5: Payments & Security:** دمج Stripe وتفعيل سياسة الحذف التلقائي.

---
*نهاية وثيقة SRS v1.1*
