# 환경 변수 레퍼런스

> 최종 업데이트: 2026-03-03

## backend/.env (로컬 개발)

```env
GROQ_API_KEY=...
GEMINI_API_KEY=...
TAVILY_API_KEY=...
FIREBASE_SERVICE_ACCOUNT=<JSON 문자열 또는 파일 경로>
FIREBASE_DATABASE_URL=https://stock-news-sync-default-rtdb.firebaseio.com
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...   # service_role 키 (Lambda 전용, 프론트엔드 금지)
NAVER_CLIENT_ID=...             # Naver Developers 애플리케이션 Client ID (검색 API)
NAVER_CLIENT_SECRET=...         # Naver Developers 애플리케이션 Client Secret
```

## frontend/.env.local (로컬 개발)

```env
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=stock-news-sync
NEXT_PUBLIC_FIREBASE_DATABASE_URL=...
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=...
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...   # anon 키 (RLS 보호, 프론트엔드 공개 안전)
```

## GitHub Secrets (Lambda 배포 시 자동 주입)

```
GROQ_API_KEY
GEMINI_API_KEY
TAVILY_API_KEY
FIREBASE_SERVICE_ACCOUNT
FIREBASE_DATABASE_URL
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
NAVER_CLIENT_ID
NAVER_CLIENT_SECRET
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
```

## 보안 주의사항

- `SUPABASE_SERVICE_ROLE_KEY`: Lambda(backend) 전용. 프론트엔드 코드에 절대 포함 금지.
- `NEXT_PUBLIC_*` 접두사: 클라이언트 번들에 포함됨. 민감 정보 사용 금지.
- API 키 하드코딩 절대 금지 — 코드/커밋에 포함 시 즉시 로테이션 필요.
