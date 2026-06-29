# دستور [PROJECT_NAME]
<!-- مثال: دستور المواصفات (Spec Constitution)، دستور تدفق المهام (TaskFlow Constitution)، إلخ. -->

## المبادئ الأساسية

### [PRINCIPLE_1_NAME]
<!-- مثال: I. المكتبة أولاً (Library-First) -->
[PRINCIPLE_1_DESCRIPTION]
<!-- مثال: كل ميزة تبدأ كمكتبة مستقلة؛ يجب أن تكون المكتبات قائمة بذاتها، قابلة للاختبار بشكل مستقل، وموثقة؛ يتطلب غرضاً واضحاً - لا توجد مكتبات تنظيمية فقط -->

### [PRINCIPLE_2_NAME]
<!-- مثال: II. واجهة سطر الأوامر (CLI Interface) -->
[PRINCIPLE_2_DESCRIPTION]
<!-- مثال: كل مكتبة تعرض وظائفها عبر واجهة سطر الأوامر (CLI)؛ بروتوكول الإدخال/الإخراج النصي: الإدخال/الوسائط (stdin/args) → الإخراج (stdout)، الأخطاء → (stderr)؛ دعم تنسيقات JSON + التنسيقات القابلة للقراءة بشرياً -->

### [PRINCIPLE_3_NAME]
<!-- مثال: III. الاختبار أولاً (NON-NEGOTIABLE) -->
[PRINCIPLE_3_DESCRIPTION]
<!-- مثال: التطوير الموجه بالاختبار (TDD) إلزامي: كتابة الاختبارات → موافقة المستخدم → فشل الاختبارات → ثم التنفيذ؛ دورة الألوان (Red-Green-Refactor) مطبقة بصرامة -->

### [PRINCIPLE_4_NAME]
<!-- مثال: IV. اختبار التكامل (Integration Testing) -->
[PRINCIPLE_4_DESCRIPTION]
<!-- مثال: مجالات التركيز التي تتطلب اختبارات تكامل: اختبارات عقود المكتبة الجديدة، تغييرات العقود، الاتصال بين الخدمات (Inter-service communication)، المخططات المشتركة (Shared schemas) -->

### [PRINCIPLE_5_NAME]
<!-- مثال: V. قابلية الملاحظة (Observability)، VI. الإصدارات والتغييرات الجذرية (Versioning & Breaking Changes)، VII. البساطة (Simplicity) -->
[PRINCIPLE_5_DESCRIPTION]
<!-- مثال: الإدخال/الإخراج النصي يضمن قابلية تصحيح الأخطاء (Debuggability)؛ التسجيل المنظم (Structured logging) مطلوب؛ أو: تنسيق MAJOR.MINOR.BUILD؛ أو: ابدأ بسيطاً، مبادئ YAGNI -->

## [SECTION_2_NAME]
<!-- مثال: قيود إضافية، متطلبات الأمان، معايير الأداء، إلخ. -->

[SECTION_2_CONTENT]
<!-- مثال: متطلبات حزمة التقنيات (Technology stack)، معايير الامتثال، سياسات النشر (Deployment policies)، إلخ. -->

## [SECTION_3_NAME]
<!-- مثال: سير عمل التطوير (Development Workflow)، عملية المراجعة (Review Process)، بوابات الجودة (Quality Gates)، إلخ. -->

[SECTION_3_CONTENT]
<!-- مثال: متطلبات مراجعة الكود (Code review)، بوابات الاختبار، عملية الموافقة على النشر، إلخ. -->

## الحوكمة (Governance)
<!-- مثال: الدستور يحل محل جميع الممارسات الأخرى؛ التعديلات تتطلب توثيقاً، موافقة، وخطة انتقال (Migration plan) -->

[GOVERNANCE_RULES]
<!-- مثال: يجب أن تتحقق جميع طلبات السحب/المراجعات (PRs/reviews) من الامتثال؛ يجب تبرير التعقيد؛ استخدم [GUIDANCE_FILE] للحصول على إرشادات تطوير وقت التشغيل (Runtime development guidance) -->

**الإصدار (Version)**: [CONSTITUTION_VERSION] | **تاريخ التصديق (Ratified)**: [RATIFICATION_DATE] | **آخر تعديل (Last Amended)**: [LAST_AMENDED_DATE]
<!-- مثال: الإصدار: 2.1.1 | تاريخ التصديق: 2025-06-13 | آخر تعديل: 2025-07-16 -->
