<!-- # 04_SDD_System_Architecture.md -->

# وثيقة تصميم النظام (System Design Document - SDD)
## اسم المشروع: المنصة الذكية للتحكيم الأكاديمي الشامل (SARA)
**(Smart Academic Review Architecture - Multi-Expert Platform)**

---

| **معلومات الوثيقة** | **التفاصيل** |
| :--- | :--- |
| **الإصدار** | 2.0 |
| **التاريخ** | 31 ديسمبر 2025 |
| **المرجع** | مبني على متطلبات المحرك الوكيل (Agentic Engine) |
| **الجمهور المستهدف** | فريق هندسة البرمجيات، مهندسو النظم، الـ Architect |

---

## 1. المعمارية الموجهة بالخدمات والبروتوكولات (Service-Protocol Architecture)

لقد تطورت معمارية SARA لتنتقل من نظام تحليل ثابت إلى **محرك سير عمل وكيل (Agentic Workflow Engine)** يعتمد على الفصل التام بين "الخدمة" و "البروتوكول". يتم إدارة سير العمل والربط بين الخدمات باستخدام **Temporal.io** كبديل قوي لـ Celery لضمان الاعتمادية والبث المباشر.

### 1.1 الهيكل الهجين والموزع (Hybrid & Distributed Structure)
*   **الخدمة (Service)**: هي المنتج النهائي الذي يراه المستخدم (مثل "نقد رسالة دكتوراة"). تحتوي على شروط المرفقات، التكلفة، ومعرف البروتوكول المرتبط.
*   **البروتوكول (Protocol)**: هو "العقل البرمجي" المصمم بصرياً أو عبر JSON. يتكون من سلسلة من العقد (Nodes) التي تنفذ مهاماً محددة وتتخذ قرارات توجيهية بناءً على مخرجات AI.
*   **مشغلات المهام الموزعة (Distributed Workers - Temporal)**: بدلاً من دمج جميع الخدمات في تطبيق واحد، يتم فصل المكونات الثقيلة (مثل `semantic_chunker`) لتعمل كـ Temporal Workers مستقلة (Microservices) تستمع إلى طوابير مهام (Task Queues) مخصصة لتنفيذ المهام الموكلة إليها.

---

## 2. محرك سير العمل الوكيل (Agentic Workflow Engine)

### 2.1 أنواع العقد (Node Types)
يتكون أي بروتوكول من الأنواع التالية من العقد:
1.  **Input Node**: تستقبل المرفقات وتتحقق من شروطها (عدد الكلمات، نوع الملف).
2.  **Processor Node**: تقوم بتفكيك الملف (Deconstruction) بناءً على الاستراتيجية المختارة (مثل المحلل الهيكلي الأكاديمي).
3.  **AI Node**: ترسل طلباً لـ Gemini مع "تلقينة" (Prompt) محددة، وتدعم الـ Context Caching.
4.  **Condition Node**: عقدة برمجية (تسمح بـ Snippets) لتوجيه المسار (مثلاً: `if (rating < 7) go to improvement_node`).
5.  **Loop Node**: تسمح بتكرار العملية على "دفعات" (Batches) داخل الملف.
6.  **Assembly Node**: تجميع النتائج المتفرقة وصياغة التقرير النهائي.

---

## 3. المعالجة الهيكلية الدلالية (Semantic Hierarchical Parsing)

هذا هو الابتكار الأساسي في SARA لضمان دقة النقد الأكاديمي.

### 3.1 المحلل الهيكلي (The Hierarchical Parser)
بدلاً من قراءة النص ككتلة واحدة، يقوم النظام ببناء شجرة للمستند:
*   **تتبع العناوين (Header Tracking)**: التعرف التلقائي على (أبواب، فصول، مباحث، مطالب).
*   **بصمة الموقع (Location Path)**: كل فقرة تُخزن ومعها مسارها النصي (مثلاً: الفصل 1 > المبحث 2).
*   **المعرفات الفريدة (Ref-IDs)**: لضمان إمكانية الإشارة الدقيقة لكل ملاحظة.

### 3.2 مستويات التمثيل (Representation Levels)
مع كل عملية رفع، يوفر النظام للمدير المتغيرات التالية لاستخدامها في البروتوكول:
| المتغير | الوصف | الاستخدام المفصل |
| :--- | :--- | :--- |
| `File_Full` | النص الكامل المفكك | للتحليل العميق والدقيق للفقرات. |
| `File_Short` | أول 150 حرف من كل فقرة | للمسح السريع (Fast Scan) وتحديد المواضيع. |
| `File_Skeleton` | هيكل البحث (العناوين والمواقع) | لتوجيه الـ AI لمواقع معينة في البحث. |

---

## 4. استراتيجية التكامل مع Gemini (Context Caching Strategy)

لتقليل التكلفة والحفاظ على السياق الكامل للبحث أثناء معالجة الدفعات:
1.  **File Upload**: يتم رفع الملف لمرة واحدة عبر `Google AI Files API`.
2.  **Context Caches**: يتم إنشاء "تخزين مؤقت" للسياق (الملف الكامل) ليبقى حياً طوال فترة عمل البروتوكول.
3.  **Batch Ingestion**: يتم إرسال "معرفات الفقرات" (IDs) في كل طلب، ويقوم الـ AI بالرجوع للملف المخزن مؤقتاً لقراءتها.

---

## 5. استراتيجية البث المباشر (Live SSE Streaming Strategy)

لتوفير تجربة (Live Critique) مباشرة وفعالة للمستخدم دون تحميل Temporal بأحداث كثيفة التردد (High-Frequency Events):
1.  **الأنشطة الموجهة للأحداث (Event-Driven Activities)**: تقوم الأنشطة (Temporal Activities) المسؤولة عن التواصل مع نماذج LLM ببث المخرجات لحظة بلحظة (Tokens/JSON chunks) إلى قناة في **Redis Pub/Sub**.
2.  **واجهة البث (SSE Endpoint)**: يقوم خادم FastAPI بالاستماع إلى هذه القناة في Redis ويدفع البيانات مباشرة إلى المتصفح عبر (Server-Sent Events - SSE).
3.  **تزامن الحالة (State Synchronization)**: بمجرد انتهاء النشاط من توليد النقد الكامل، يقوم بإرجاع النتيجة النهائية إلى مسار عمل Temporal (Workflow) لحفظ الحالة النهائية بشكل دائم (Durability) وتحديث قاعدة البيانات.

---

## 5. تصميم قاعدة البيانات المطور (Extended ERD)

### 5.1 جداول المحرك (Engine Tables)
*   **`services`**: `id, name, description, config (JSON), protocol_id`.
*   **`protocols`**: `id, name, definition (JSONB - The Workflow Tree), created_by`.
*   **`document_paragraphs`**: 
    *   `id`: UUID.
    *   `session_id`: FK.
    *   `content`: Text.
    *   `location_path`: String (e.g. "Chapter 1 > Section 2").
    *   `order_index`: Integer.
    *   `metadata`: JSONB (styles, bold, etc).

### 5.2 الحالة العالمية (Protocol State)
*   **`session_state`**: جدول مؤقت (أو مخزن في Redis) يحفظ المتغيرات التي يتم تمريرها بين العقد أثناء التنفيذ لضمان التواصل بين العقد البعيدة.

---

## 6. المسار التقني للتنفيذ (Implementation Roadmap v2)

1.  **CORE-PARSER**: تطوير المحلل الهيدروليكي (Headings-Aware Parser).
2.  **ORCHESTRATION**: إعداد Temporal.io لبناء مسارات العمل (Workflows) وإنشاء الـ Workers المنفصلة (بما في ذلك Chunker Worker في مستودع مستقل).
3.  **AGENT-RUNNER**: بناء مفسر الـ JSON (Interpreter) الذي ينفذ عقد البروتوكول داخل أنشطة Temporal.
4.  **VISUAL-BUILDER**: واجهة React Flow لمنشئ البروتوكولات.
5.  **INTEGRATION & STREAMING**: ربط المحرك بـ Gemini Context Caching وتنفيذ البث المباشر عبر Redis Pub/Sub و SSE.

---
*تم التحديث بواسطة SARA Architect - 31 ديسمبر 2025*
