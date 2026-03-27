# stock-news-sync — GitHub Copilot Instructions

This repository is a Korean/English AI investment briefing platform.
Always respond to the developer in **Korean** when asked questions or writing comments.

## Project Stack

- Frontend: Next.js 16.1.5 (App Router), React 19, TypeScript 5, Tailwind CSS v4
- Backend: Python 3.11, AWS Lambda (ap-northeast-2)
- Database: Supabase PostgreSQL + Realtime
- AI/LLM: Groq + Google Gemini via OpenAI SDK (base_url swap)
- CI/CD: GitHub Actions → S3 → Lambda / Vercel

## Commit Message Format

All commit messages MUST follow this format with Korean descriptions:

```
[Feat]: 새로운 기능 추가
[Fix]: 버그 수정
[Docs]: 문서 수정 (README.md, CLAUDE.md 등)
[Style]: 코드 포맷팅, 변경 없는 UI 수정
[Refactor]: 코드 리팩토링
[Test]: 테스트 코드 추가 및 수정
[Chore]: 빌드 태스크, 패키지 매니저 수정
```

Example: `[Fix]: litellm → openai SDK로 교체 (Lambda 250MB 제한 초과 해결)`

## Security Rules

- **NEVER hardcode API keys** in source code or commit history.
  Always use environment variables: `os.environ.get('KEY')` (Python) or `process.env.KEY` (TypeScript).
- Secrets are managed via `backend/.env` (local) and GitHub Secrets (CI/CD).
- Required backend secrets: `GROQ_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- Required frontend secrets: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` is backend-only — NEVER expose to frontend bundles.

## Lambda Size Constraint

- AWS Lambda has a **250 MB deployment package limit**.
- **Do NOT suggest** LiteLLM, transformers, torch, or any large ML packages.
- Use the OpenAI SDK with `base_url` overriding to connect Groq and Gemini:

```python
# Groq
client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
# Gemini
client = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
```

- When adding a package to `requirements.txt`, always verify its installed size first.

## Lambda Deployment

- Lambda deployment is ONLY done via GitHub Actions (`sync.yml`).
- **Never suggest** running `aws lambda update-function-code` directly.
- Deployment flow: `git push → PR merge → GitHub Actions → S3 upload → Lambda update`
