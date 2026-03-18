---
name: qa
description: 04번 Tech Lead PM의 QA 체크리스트를 실행합니다. 시크릿 노출 스캔, Firebase 인터페이스 일관성 검사, TypeScript any 타입 검사, Lambda 패키지 안전 검사를 수행합니다.
argument-hint: [scope: all|secret|interface|lint]
allowed-tools: Bash, Grep, Read
---

## QA 체크리스트 실행

`$ARGUMENTS`가 없거나 `all`이면 아래 모든 단계를 실행한다.
특정 scope가 지정된 경우(`secret`, `interface`, `lint`) 해당 단계만 실행한다.

---

### STEP 1 — 시크릿 노출 스캔 (scope: secret / all)

`backend/`와 `frontend/` 디렉터리에서 아래 패턴을 Grep으로 검색한다.
단, `.env`, `serviceAccount.json`, `.env.local` 파일은 제외한다.

검사 패턴:
- Groq API 키: `gsk_[a-zA-Z0-9]{20,}`
- Google API 키: `AIza[a-zA-Z0-9_-]{20,}`
- Tavily API 키: `tvly-[a-zA-Z0-9]{20,}`
- AWS 액세스 키: `AKIA[A-Z0-9]{16}`

결과:
```
[시크릿 스캔] ✅ 이상 없음
또는
[시크릿 스캔] ❌ 발견: {파일명}:{줄번호}
```

---

### STEP 2 — Firebase 인터페이스 일관성 (scope: interface / all)

**2-1. `/feed/` RTDB 경로 일치 확인**
`backend/services/db_service.py`와 `frontend/` 디렉터리에서 Firebase ref 경로를 추출하여 `/feed/` 경로 일치 여부를 비교한다.

**2-2. `ref.set()` 사용 여부**
`backend/services/db_service.py`에서 주석이 아닌 `ref.set(` 패턴 존재 여부를 검사한다.

**2-3. Firebase 초기화 이중 방지 가드**
`backend/`에서 `firebase_admin.initialize_app` 호출 전 `if not firebase_admin._apps:` 가드 존재 여부를 확인한다.

**2-4. `onValue` cleanup 확인**
`frontend/` 에서 `onValue`가 사용된 파일마다 같은 파일 내 `return () =>` 또는 `off(` cleanup이 존재하는지 확인한다.

**2-5. TypeScript `any` 타입 검사**
`frontend/**/*.{ts,tsx}` 파일에서 `: any`, `as any`, `<any>` 패턴을 검색한다.

결과:
```
[인터페이스 일관성]
  RTDB 경로:            ✅ / ❌
  ref.set() 없음:       ✅ / ❌
  초기화 가드:          ✅ / ❌
  onValue cleanup:      ✅ / ❌
  TypeScript any:       ✅ / ❌
```

---

### STEP 3 — 프론트엔드 Lint (scope: lint / all)

`frontend` 디렉터리에서 `npm run lint`를 실행한다.
에러 0개면 Pass, 에러 발생 시 항목과 위치를 목록으로 출력한다.

---

### STEP 4 — Lambda 패키지 안전 검사 (scope: all)

`backend/requirements.txt`를 Read로 읽어 금지 패키지 포함 여부를 확인한다.
금지 패키지: `litellm`, `anthropic`, `torch`, `tensorflow`

---

### 최종 요약 출력

모든 단계 완료 후 아래 형식으로 출력한다:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[QA 결과] — 04번 Tech Lead PM 연계용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
시크릿 스캔:         ✅ / ❌
Firebase 일관성:     ✅ / ❌
TypeScript any:      ✅ / ❌
프론트엔드 Lint:     ✅ Pass / ❌ Fail
Lambda 패키지:       ✅ / ❌
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
판정: 전체 통과 → /commit-kr 으로 커밋 초안 생성 후 02번에 전달
      항목 실패 → 해당 에이전트에 수정 지시 후 재실행
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
