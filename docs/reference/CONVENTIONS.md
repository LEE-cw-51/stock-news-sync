# 코딩 컨벤션 & 커밋 규칙

> 최종 업데이트: 2026-03-03

## Python (Backend)

- **서비스 레이어 패턴**: 비즈니스 로직은 `services/` 내 함수로 분리
- **로깅**: `logging` 모듈 사용, `print()` 지양
- **Type hints**: 함수 시그니처에 타입 힌트 권장
- **에러 핸들링**: 개별 티커/API 실패는 `try/except`로 건너뜀 (전체 실행 중단 방지)
- **Firebase 쓰기**: `update()` 사용 (`set()` 금지 — 기존 데이터 덮어씌움 방지)

## TypeScript (Frontend)

- **App Router**: Server Component 기본, `"use client"` 필요한 경우만 명시
- **Strict mode**: `any` 타입 사용 금지
- **Tailwind**: 인라인 style 속성 지양, Tailwind 클래스만 사용
- **Firebase 구독**: `onValue()` 사용, 컴포넌트 언마운트 시 `off()` cleanup 필수

## 커밋 메시지 규칙

에이전트 커밋은 반드시 아래 한글 템플릿 사용 (02번 에이전트가 04번 QA 후 커밋):

```
[Feat]: 새로운 기능 추가
[Fix]: 버그 수정
[Docs]: 문서 수정 (README.md, CLAUDE.md 등)
[Style]: 코드 포맷팅, 변경 없는 UI 수정
[Refactor]: 코드 리팩토링
[Test]: 테스트 코드 추가 및 수정
[Chore]: 빌드 태스크, 패키지 매니저(requirements.txt, package.json 등) 수정
```

예시: `[Fix]: litellm → openai SDK로 교체 (Lambda 250MB 제한 초과 해결)`
