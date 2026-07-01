# المهام: الأساس لمنصة نقّاد (Naqqad Phase 1: Foundation & Upload Pipeline)

**المدخلات**: مستندات التصميم من `/specs/001-naqqad-phase1-foundation/`
**المتطلبات الأساسية**: ملف plan.md، ملف spec.md، وملفات research.md و data-model.md.

**التنظيم**: يتم تجميع المهام حسب قصة المستخدم لتمكين التنفيذ والاختبار المستقل لكل قصة.

## المرحلة 1: الإعداد (البنية التحتية المشتركة)

**الغرض**: تهيئة المشروع والهيكل الأساسي

- [x] T001 إنشاء `backend/pyproject.toml` وإعداد التبعيات (dependencies)
- [x] T002 إنشاء `backend/.env.example` وإعداد متغيرات البيئة
- [x] T003 [P] إنشاء `backend/app/config.py` وتكوين الإعدادات بـ Pydantic
- [x] T004 [P] إنشاء `backend/app/main.py` مع `lifespan` و إعدادات CORS الأساسية
- [x] T005 [P] إنشاء `backend/Dockerfile`
- [x] T006 [P] إنشاء `docker-compose.yml` في جذر المشروع (db, redis, ollama, localstack, backend, worker, beat)
- [x] T007 تشغيل الحاويات للتأكد من عمل البنية التحتية وتنزيل نموذج Qwen في Ollama

---

## المرحلة 2: التأسيس (المتطلبات الأساسية المانعة)

**الغرض**: البنية التحتية الأساسية لقواعد البيانات والنماذج الأساسية التي يجب توفرها قبل بناء نقاط النهاية والخدمات.

- [x] T008 إنشاء `backend/app/database.py` لتهيئة `AsyncSession` باستخدام SQLAlchemy
- [x] T009 [P] إنشاء نموذج المستخدم `User` في `backend/app/models/user.py`
- [x] T010 [P] إنشاء نماذج الجلسات `CritiqueSession` والملفات المرفوعة `UploadedFile` في `backend/app/models/session.py`
- [x] T011 [P] إنشاء نموذج القطع النصية `Chunk` في `backend/app/models/chunk.py`
- [x] T012 [P] إنشاء نموذج إرشادات التخصص `DisciplineInstruction` في `backend/app/models/discipline.py`
- [x] T013 دمج جميع النماذج في `backend/app/models/__init__.py`
- [x] T014 تهيئة بيئة Alembic (Migrations) بإنشاء `backend/alembic.ini` و تعديل `backend/alembic/env.py` للعمل بشكل لا تزامني (async)
- [x] T015 إنشاء أول Migration للنماذج وتطبيقه على قاعدة البيانات (ملاحظة: تحتاج إلى تشغيل DB Container أولاً لتطبيق التغييرات)

---

## المرحلة 3: قصة المستخدم 2 (User Story) - المصادقة وإدارة الحسابات (الأولوية: P2)

**الهدف**: إنشاء حساب جديد وتسجيل الدخول لتأمين النظام وإدارة الجلسات.
*(ملاحظة: نضع هذه القصة قبل قصة المستخدم 1 لاعتماد نقاط النهاية للرفع على وجود مستخدم مسجل)*

### الاختبارات
- [x] T016 [P] [US2] إنشاء ملف إعداد الاختبارات `backend/tests/conftest.py`
- [x] T017 [P] [US2] كتابة اختبارات المصادقة (التسجيل وتسجيل الدخول) في `backend/tests/test_auth.py`

### التنفيذ
- [x] T018 [P] [US2] إنشاء أدوات التشفير ومعالجة JWT في `backend/app/utils/security.py`
- [x] T019 [P] [US2] إنشاء نماذج بيانات API (Pydantic Schemas) في `backend/app/schemas/auth.py`
- [x] T020 [US2] تنفيذ نقاط النهاية (Endpoints) الخاصة بالتسجيل وتسجيل الدخول في `backend/app/api/auth.py`
- [x] T021 [US2] تصدير نقاط النهاية في `backend/app/api/__init__.py` وتحديث `main.py` لاستخدامها

---

## المرحلة 4: قصة المستخدم 1 (User Story) - رفع وتجزئة المستندات (الأولوية: P1)

**الهدف**: معالجة رفع المستندات، تخزينها بشكل آمن ومُشفر في S3، وتجزئتها دلالياً (Semantic Chunking) باستخدام Ollama.

### الاختبارات
- [x] T022 [P] [US1] إنشاء ملفات الاختبار (Fixtures) (sample.md, sample.txt)
- [x] T023 [P] [US1] كتابة اختبارات محلل الملفات (File Parser) في `backend/tests/test_file_parser.py`
- [x] T024 [P] [US1] كتابة اختبارات التخزين (Storage Service) في `backend/tests/test_storage.py`
- [x] T025 [P] [US1] كتابة اختبارات التجزئة عبر Ollama في `backend/tests/test_chunker.py`
- [x] T026 [P] [US1] كتابة اختبارات نقاط النهاية لرفع الملفات وجلب الجلسات في `backend/tests/test_upload.py` و `backend/tests/test_sessions.py`

### التنفيذ (الخدمات والتخزين)
- [x] T027 [P] [US1] تنفيذ خدمة `file_parser.py` في `backend/app/services/` لاستخراج النصوص من docx, txt, md
- [x] T028 [P] [US1] تنفيذ خدمة التخزين `storage.py` بدمج boto3 وتشفير AES-256
- [x] T029 [P] [US1] تنفيذ خدمة `chunker.py` للاتصال بـ Ollama (Qwen2.5) لتوليد تجزئة دلالية للنص
- [x] T030 [US1] تنفيذ مهام Celery للتجزئة في `backend/app/tasks/chunking.py` وتحديث الحالة في قاعدة البيانات

### التنفيذ (مسارات واجهة برمجة التطبيقات API)
- [x] T031 [P] [US1] إنشاء نماذج استجابة الجلسة `SessionResponse` وغيرها في `backend/app/schemas/session.py` و `backend/app/schemas/chunk.py`
- [x] T032 [US1] تنفيذ نقطة النهاية `POST /sessions/upload` في `backend/app/api/upload.py` (استقبال الملف، حفظه، وتشغيل Celery Task)
- [x] T033 [US1] تنفيذ نقطة النهاية `GET /sessions/{id}` و `GET /sessions/{id}/chunks` في `backend/app/api/sessions.py`

---

## المرحلة 5: قصة المستخدم 3 (User Story) - التدمير الآمن للجلسات (الأولوية: P3)

**الهدف**: ضمان مسح الجلسات والملفات المرفوعة دورياً (بعد مرور 24 ساعة) لأغراض الخصوصية والأمان.

### الاختبارات
- [x] T034 [P] [US3] كتابة اختبارات عملية التنظيف (Cleanup Task) في `backend/tests/test_cleanup.py`

### التنفيذ
- [x] T035 [US3] تنفيذ مهمة التنظيف المجدولة في `backend/app/tasks/cleanup.py` لحذف الجلسات المُنتهية من قاعدة البيانات وملفاتها المرافقة من S3
- [x] T036 [US3] تحديث تكوين Celery وإعداد جدول Celery Beat في `backend/app/tasks/celery_app.py`

---

## التبعيات وترتيب التنفيذ (Dependencies & Execution Order)

- **المرحلة 1 و 2**: يجب أن تكتمل بالكامل قبل البدء في أي مهام أخرى.
- **قصة المستخدم 2 (US2)**: تعتبر ممهدة ومطلوبة لعمليات المصادقة في قصة الرفع (US1)، لذا تم تقديمها لتصبح التبعية الأولى في مهام الويب.
- **قصة المستخدم 1 (US1)**: تعتمد على US2 لإجراء اختبارات شاملة مع تسجيل الدخول.
- **قصة المستخدم 3 (US3)**: يمكن البدء فيها فور الانتهاء من تجهيز قاعدة البيانات وتكوينات Celery ضمن المرحلة 1 و 2، لكن يفضل ربطها بعد الانتهاء من US1 لتوافر ملفات فعلية للاختبار.

## فرص التوازي (Parallel Execution Examples)

- **داخل المرحلة 1**: يمكن تجهيز ملفات الإعداد وملفات Docker كلها في نفس الوقت إذا توفر أكثر من مطور.
- **داخل المرحلة 2**: يمكن إنشاء جميع نماذج قواعد البيانات (models) في `backend/app/models/` كمهام متوازية.
- **داخل US1**: يمكن العمل على الاختبارات `test_file_parser.py` وتنفيذ خدمة `file_parser.py` في وقت واحد مع العمل على `storage.py` ومهمة S3 المستقلة كلياً.
