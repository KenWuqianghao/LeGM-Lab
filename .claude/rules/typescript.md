---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---

# TypeScript Rules

- Strict mode always. Never use `any` — use `unknown` and narrow, or proper generics.
- Prefer `interface` over `type` for object shapes (better error messages, extendable).
- Use `type` for unions, intersections, and utility types.
- Components: functional only, named exports, PascalCase naming.
- Hooks: extract custom hooks for reusable logic, prefix with `use`.
- Props: define interface above component, suffix with `Props` (e.g., `ButtonProps`).
- State management: React state/context for UI state, server state via TanStack Query or SWR.
- Use `bun` as package manager, not npm/yarn.
- Format with prettier. No manual formatting.
- Imports: prefer absolute imports with `@/` alias.
