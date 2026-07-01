# عقود واجهات برمجة التطبيقات (API Contracts)

## 1. المصادقة (Auth)

### تسجيل الدخول `POST /auth/login`
- **Request Body**: `{"email": "...", "password": "..."}`
- **Response (200 OK)**: `{"access_token": "...", "token_type": "bearer"}`

### التسجيل `POST /auth/register`
- **Request Body**: `{"email": "...", "password": "..."}`
- **Response (201 Created)**: `{"access_token": "...", "token_type": "bearer"}`

## 2. الجلسات والملفات (Sessions & Upload)

### إنشاء جلسة ورفع ملف `POST /sessions/upload`
- **Headers**: `Authorization: Bearer <token>`
- **Content-Type**: `multipart/form-data`
- **Form Data**: 
  - `file`: (Binary data - docx/txt/md)
  - `tone`: (String: constructive/forensic)
  - `report_depth`: (String)
- **Response (202 Accepted)**: `{"session_id": "<uuid>", "status": "parsing"}`

### جلب حالة الجلسة `GET /sessions/{session_id}`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**: `{"session_id": "<uuid>", "status": "completed", "expires_at": "..."}`

### جلب قطع النصوص `GET /sessions/{session_id}/chunks`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**: `{"chunks": [{"id": "...", "text": "...", "index": 0}]}`
