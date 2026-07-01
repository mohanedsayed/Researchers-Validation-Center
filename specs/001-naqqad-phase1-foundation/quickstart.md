# دليل البدء السريع (Quickstart)

لتهيئة وتشغيل بيئة التطوير المحلية لمنصة "نقّاد" - المرحلة الأولى:

1. **نسخ ملف البيئة**:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **تشغيل حاويات Docker الأساسية**:
   يقوم هذا بتشغيل قاعدة البيانات (PostgreSQL)، و Redis، ومحاكي S3 (LocalStack).
   ```bash
   docker-compose up -d db redis localstack
   ```

3. **تشغيل وتنزيل نموذج Ollama**:
   ```bash
   docker-compose up -d ollama
   docker-compose exec ollama ollama pull qwen2.5:7b
   ```

4. **تشغيل الواجهة الخلفية ومهام الخلفية (Celery)**:
   ```bash
   docker-compose up -d backend worker beat
   ```

5. **تطبيق هجرات قاعدة البيانات (Migrations)**:
   ```bash
   docker-compose run --rm backend alembic upgrade head
   ```

الآن، واجهة برمجة التطبيقات (API) تعمل على `http://localhost:8000`، ويمكنك التحقق من توثيق Swagger التلقائي عبر `http://localhost:8000/docs`.
