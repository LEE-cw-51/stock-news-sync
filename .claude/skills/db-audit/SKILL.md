---
name: db-audit
description: 05번 DB Management Agent의 DB 감사 체크리스트를 실행합니다. Firebase RTDB 경로 일관성, Supabase RLS 커버리지, 심볼 키 정규화, DB 보안 감사를 수행합니다.
argument-hint: [scope: all|firebase|supabase|security]
allowed-tools: Read, Grep, Glob
---

## DB 감사 실행

`$ARGUMENTS`가 없거나 `all`이면 아래 모든 단계를 실행한다.
특정 scope가 지정된 경우(`firebase`, `supabase`, `security`) 해당 단계만 실행한다.

---

### STEP 1 — Firebase RTDB 경로 일관성 (scope: firebase / all)

**1-1. 백엔드 경로 추출**
`backend/services/db_service.py`를 Read로 읽어 Firebase reference 경로를 모두 추출한다.
`/feed/` 로 시작하는 경로 목록을 작성한다.

**1-2. 프론트엔드 타입 정의 확인**
`frontend/lib/types.ts`를 Read로 읽어 Firebase 데이터 구조 타입 정의를 추출한다.

**1-3. 경로 일치 비교**
백엔드에서 쓰는 경로와 프론트엔드 타입이 일치하는지 비교한다.
불일치 경로가 있으면 목록으로 출력한다.

**1-4. `ref.set()` 사용 여부**
`backend/services/db_service.py`에서 주석이 아닌 `ref.set(` 패턴 존재 여부를 Grep으로 검사한다.

결과:
```
[Firebase 감사]
  RTDB 경로 일치:      ✅ / ❌ (불일치: {경로 목록})
  ref.set() 없음:      ✅ / ❌
```

---

### STEP 2 — Supabase RLS 커버리지 (scope: supabase / all)

**2-1. 스키마 파일 읽기**
`backend/db/supabase_schema.sql`을 Read로 읽어 모든 테이블 목록과 RLS 활성화 여부를 추출한다.

**2-2. RLS 미적용 테이블 탐지**
`ENABLE ROW LEVEL SECURITY`가 없는 테이블을 목록으로 추출한다.

**2-3. stock_history 이슈 확인**
`stock_history` 테이블의 RLS 상태를 명시적으로 확인한다.
(현재 알려진 이슈: RLS 미적용 — anon 쓰기 차단 정책 부재)

**2-4. watchlist RLS 정책 검증**
`watchlist` 테이블의 RLS 정책이 SELECT/INSERT/DELETE 모두 적용되어 있는지 확인한다.

**2-5. 인덱스 효율성 확인**
`watchlist(user_id)` 단독 인덱스 존재 여부를 확인한다.
(현재 알려진 이슈: `idx_watchlist_user_id` 미생성)

결과:
```
[Supabase 감사]
  RLS 적용 테이블:     {목록}
  RLS 미적용 테이블:   {목록} ← 리스크 등급 포함
  stock_history RLS:   ✅ / ❌ (Medium 리스크)
  watchlist RLS:       ✅ / ❌
  watchlist 인덱스:    ✅ / ❌
```

---

### STEP 3 — 심볼 키 정규화 일관성 (scope: all)

**3-1. db_service.py 변환 로직 추출**
`backend/services/db_service.py`에서 `.` → `_` 변환 패턴을 Grep으로 추출한다.

**3-2. market_service.py 동일 패턴 확인**
`backend/services/market_service.py`에서 동일한 키 정규화 로직이 사용되는지 확인한다.

**3-3. tickers.py 확인**
`backend/config/tickers.py`를 Read로 읽어 `.KS`, `-USD` 등 특수 문자가 포함된 티커 목록을 확인한다.

결과:
```
[심볼 키 정규화]
  변환 규칙 일관성:    ✅ / ❌
  특수 문자 티커 목록: {목록}
  미처리 케이스:       {있으면 목록}
```

---

### STEP 4 — DB 보안 감사 (scope: security / all)

**4-1. service_role 키 프론트엔드 노출 확인**
`frontend/` 디렉터리에서 `SERVICE_ROLE`, `service_role` 패턴을 Grep으로 검색한다.
발견 시 Critical 이슈로 즉시 보고한다.

**4-2. NEXT_PUBLIC 키 백엔드 노출 확인**
`backend/` 디렉터리에서 `NEXT_PUBLIC_` 패턴을 Grep으로 검색한다.
(백엔드에서 NEXT_PUBLIC 키를 하드코딩하면 안 됨)

**4-3. 서비스 계정 JSON 하드코딩 확인**
`backend/` 디렉터리에서 `"type": "service_account"` 패턴을 Grep으로 검색한다.
`.env` 파일은 제외한다.

결과:
```
[보안 감사]
  service_role 프론트 노출:  ✅ 없음 / ❌ Critical
  NEXT_PUBLIC 백엔드 노출:   ✅ 없음 / ❌
  서비스 계정 하드코딩:      ✅ 없음 / ❌
```

---

### 최종 요약 출력

모든 단계 완료 후 아래 형식으로 출력한다:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[DB Audit 결과] — 05번 DB Management Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Firebase RTDB 경로 일치:    ✅ / ❌
ref.set() 없음:             ✅ / ❌
Supabase RLS 커버리지:      ✅ / ❌ ({미적용 테이블})
심볼 키 정규화 일관성:      ✅ / ❌
DB 보안 (키 노출):          ✅ / ❌
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 발견된 이슈
  {이슈 목록 — 리스크 등급 포함}

■ 권고 조치
  {조치 항목 목록}

판정: 전체 통과 → 04번 Tech Lead PM에게 보고
      이슈 발견 → 해당 항목 DDL 초안 작성 후 04번 승인 요청
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
