# نماذج البيانات (Data Model)

هذا الملف يصف الكيانات الأساسية وعلاقاتها في قاعدة البيانات PostgreSQL، باستخدام مكتبة SQLAlchemy.

## 1. User (المستخدم)
- **id**: UUID (Primary Key)
- **email**: String (Unique, Not Null)
- **hashed_password**: String (Not Null)
- **language_preference**: String (Default: 'ar')
- **tier**: Enum (FREE, STARTER, PRO, SCHOLAR)
- **monthly_token_balance**: Integer (Default: 0)
- **credit_balance**: Integer (Default: 0)
- **byok_api_key**: String (Nullable - لاحقاً لميزة مفاتيح API الخاصة)
- **is_active**: Boolean (Default: True)
- **created_at**: DateTime

## 2. CritiqueSession (جلسة التقييم)
- **id**: UUID (Primary Key)
- **user_id**: UUID (Foreign Key -> User.id)
- **status**: Enum (UPLOADING, PARSING, QUEUED, CRITIQUING, COMPLETED, FAILED, EXPIRED)
- **tone**: Enum (CONSTRUCTIVE, FORENSIC)
- **report_depth**: Enum (EXECUTIVE, STANDARD, DEEP_AUDIT)
- **detected_language**: String (Nullable)
- **tokens_consumed**: Integer (Default: 0)
- **created_at**: DateTime
- **expires_at**: DateTime (تُحدد بـ 24 ساعة بعد الإنشاء)

## 3. UploadedFile (الملف المرفوع)
- **id**: UUID (Primary Key)
- **session_id**: UUID (Foreign Key -> CritiqueSession.id)
- **original_filename**: String (Not Null)
- **file_format**: String (docx, txt, md)
- **s3_key**: String (مسار الملف في S3 - يتم تشفير الملف محلياً قبل رفعه)
- **file_size_bytes**: Integer
- **created_at**: DateTime

## 4. Chunk (القطعة النصية)
- **id**: UUID (Primary Key)
- **session_id**: UUID (Foreign Key -> CritiqueSession.id)
- **paragraph_index**: Integer
- **text**: Text (النص المجزأ)
- **token_estimate**: Integer
- **critique_status**: String (Default: 'pending')
- **created_at**: DateTime

## العلاقات (Relationships)
- **User** يمتلك واحدة أو أكثر من **CritiqueSession** (1:N)
- **CritiqueSession** يمتلك بالضبط ملف واحد **UploadedFile** (1:1 أو 1:N في حال تعدد الملفات للجلسة، لكن الأفضل 1:N للاحتياط).
- **CritiqueSession** يمتلك عدة **Chunk** (1:N)
