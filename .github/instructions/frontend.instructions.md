---
applyTo: "frontend/**/*.ts,frontend/**/*.tsx"
---

# Frontend Instructions — Next.js / TypeScript / Tailwind

## Next.js App Router Rules

- **Server Component by default**: All components are Server Components unless they require interactivity.
- Use `"use client"` ONLY when the component uses: `useState`, `useEffect`, `useRef`, event handlers, or browser APIs.
- Do NOT add `"use client"` to layout files or pure display components.

```tsx
// Good — Server Component (no directive needed)
export default function AISummaryCard({ summary }: Props) { ... }

// Good — Client Component (needs state/event)
"use client";
export default function AuthModal({ onClose }: Props) { ... }
```

## TypeScript Strict Mode

- **Never use `any` type**. Use `unknown` and narrow with type guards, or define explicit interfaces.
- Always define interfaces for component props, API responses, and shared data structures.
- Import types with `import type { ... }` where possible to reduce bundle size.

```tsx
// Bad
const data: any = await fetch(...);

// Good
const data: FeedData = await fetch(...).then(r => r.json());
```

## Tailwind CSS Only

- **No inline `style` attributes**. Use Tailwind utility classes exclusively.
- No CSS Modules, no styled-components, no emotion.

```tsx
// Bad
<div style={{ backgroundColor: 'black', padding: '1rem' }}>

// Good
<div className="bg-black p-4">
```

- Color palette in use: `slate-*` (backgrounds/borders), `blue-*` (primary), `emerald-*` (positive), `red-*` (negative), `indigo-*` (macro category).

## Supabase Client Patterns

- Import the shared client from `@/lib/supabase` — do NOT create new `createClient()` instances in components.
- **Always clean up subscriptions** on component unmount.

```tsx
// Realtime subscription cleanup pattern
useEffect(() => {
  const channel = supabase.channel('feed').on('postgres_changes', ...).subscribe();
  return () => { supabase.removeChannel(channel); };
}, []);
```

- `NEXT_PUBLIC_*` keys are safe for the browser bundle.
- `SUPABASE_SERVICE_ROLE_KEY` is backend-only — never import or reference in frontend code.

## Component File Organization

```
frontend/components/
├── auth/       — authentication modals
├── chart/      — TradingView widget wrappers
├── dashboard/  — market index cards
├── layout/     — Header, navigation
├── news/       — AISummaryCard, NewsCard, NewsFeedSection
└── portfolio/  — StockRow and watchlist UI
```

- One component per file, named identically to the export (PascalCase).
- Co-locate component-specific types at the top of the file if not shared.
- Shared types live in `frontend/lib/types.ts`.

## Key Shared Types (frontend/lib/types.ts)

- `FeedData` — top-level Supabase realtime payload
- `AISummaryStructured` — AI JSON response (`bullets`, `market_reaction`, `trend_insight`, `glossary_terms`, `flow_explanation`)
- `NewsItem` — `{ title, link, name, pubDate? }`
- `StockData`, `MarketValue`, `WatchlistItem`
