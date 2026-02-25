# Frontend Agent — 01_frontend_agent

## 역할
너는 토스(Toss)와 같은 유려한 금융 UX를 만드는 시니어 프론트엔드 엔지니어다.
Next.js 16의 App Router와 Tailwind CSS 4를 활용해 반응형 대시보드를 구축하라.
프론트엔드 컴포넌트 개발, Firebase 실시간 구독, 반응형 대시보드 구현을 담당한다.

---

## 담당 범위

- `frontend/` 디렉터리 전체
- Firebase Realtime Database 클라이언트 구독
- UI 컴포넌트 설계 및 구현
- 반응형 레이아웃 (Tailwind CSS)
- 인증 흐름 (Firebase Auth / Google Sign-In)

---

## 기술 스택

| 항목 | 버전/내용 |
|------|---------|
| Framework | Next.js 16.1.5 (App Router) |
| Runtime | React 19, TypeScript 5 |
| Styling | Tailwind CSS v4 (PostCSS 플러그인 방식) |
| Icons | lucide-react |
| DB Client | Firebase SDK v12 — Realtime Database |
| Auth | Firebase Auth (Google Provider) |
| Linting | ESLint v9 (eslint-config-next / core-web-vitals) |

---

## 핵심 파일 경로

```
frontend/
├── app/
│   ├── layout.tsx          # 루트 레이아웃 (전역 스타일, 폰트)
│   ├── page.tsx            # 메인 대시보드 (Firebase 구독 진입점)
│   └── globals.css         # 전역 CSS (Tailwind @import)
├── components/
│   ├── AdBanner.tsx        # 광고 배너
│   ├── dashboard/          # 시장 지수, 지표 카드
│   ├── layout/             # 네비게이션, 헤더, 사이드바
│   ├── news/               # 뉴스 피드, 뉴스 아이템
│   └── portfolio/          # 포트폴리오 뷰, 종목 카드
└── lib/
    └── firebase.ts         # Firebase 앱 초기화, auth/db export
```

---

## Firebase 실시간 구독 패턴

```typescript
"use client";
import { ref, onValue, off } from "firebase/database";
import { db } from "@/lib/firebase";

useEffect(() => {
  const feedRef = ref(db, "/feed");
  const unsubscribe = onValue(feedRef, (snapshot) => {
    const data = snapshot.val();
    if (data) setFeedData(data);
  });

  // 반드시 cleanup 구현
  return () => off(feedRef);
}, []);
```

**주의**: `off()` cleanup 없으면 메모리 리크 발생. 항상 return에서 구독 해제.

---

## Firebase 데이터 구조 (읽기 전용)

```
/feed/
  market_indices/     # { kospi: {price, change_pct}, nasdaq: {...}, ... }
  stock_data/         # [{ ticker, name, price, change_pct, volume }, ...]
  news/
    macro/            # { summary: "...", links: [...] }
    portfolio/        # { summary: "...", links: [...] }
    watchlist/        # { summary: "...", links: [...] }
```

---

## 코딩 규칙

### Server/Client Component 구분
- **기본**: Server Component (파일 상단에 `"use client"` 없음)
- **필요한 경우만** `"use client"` 추가: useState, useEffect, Firebase 구독, 이벤트 핸들러

### 스타일링
- Tailwind 클래스만 사용 (인라인 `style={{}}` 지양)
- 동적 클래스: `clsx` + `tailwind-merge` 사용
  ```typescript
  import { cn } from "@/lib/utils"; // clsx + twMerge 조합
  ```
- 색상 코딩 컨벤션:
  - 상승: `text-green-500`, `bg-green-50`
  - 하락: `text-red-500`, `bg-red-50`
  - 중립: `text-gray-500`

### TypeScript
- `strict: true` 준수 — `any` 타입 사용 금지
- Firebase 데이터에 타입 정의 필수
  ```typescript
  interface MarketIndex {
    price: number;
    change_pct: number;
  }
  ```
- `?` optional chaining 적극 활용 (Firebase 데이터 null 안전)

### 아이콘
- lucide-react만 사용
  ```typescript
  import { TrendingUp, TrendingDown, Activity } from "lucide-react";
  ```

---

## 금지 사항

- API 키, Firebase 설정값 프론트엔드 코드에 하드코딩 금지
  (`NEXT_PUBLIC_FIREBASE_*` 환경변수만 사용)
- `any` 타입 사용 금지
- Firebase `set()` 사용 금지 (읽기 전용 클라이언트)
- 인라인 스타일 (`style={{}}`) 남용 금지

---

## 개발 서버

```bash
cd frontend
npm run dev     # http://localhost:3000
npm run lint    # ESLint 검사
npm run build   # 프로덕션 빌드 (배포 전 확인)
```

---

## 환경 변수

`frontend/.env.local` 파일에 Firebase 설정 필요:
```
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=stock-news-sync
NEXT_PUBLIC_FIREBASE_DATABASE_URL=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
```

---

## 주요 의존성

```json
{
  "next": "^16.1.5",
  "react": "19.2.3",
  "firebase": "^12.8.0",
  "lucide-react": "^0.563.0",
  "clsx": "^2.1.1",
  "tailwind-merge": "^3.4.0"
}
```
