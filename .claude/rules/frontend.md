---
paths:
  - "components/**"
  - "app/**"
  - "pages/**"
  - "src/components/**"
  - "src/app/**"
  - "**/*.tsx"
---

# Frontend Design Rules

- Use shadcn/ui components from `@/components/ui/*`. Don't reinvent buttons, inputs, dialogs.
- Use `cn()` from `@/lib/utils` for conditional Tailwind classes.
- Every interactive component MUST handle: hover, focus, active, disabled, loading, error states.
- Mobile-first: write base styles for mobile, add `sm:`, `md:`, `lg:` for larger screens.
- Spacing: use Tailwind's spacing scale (multiples of 4px). No arbitrary values unless necessary.
- Colors: use semantic tokens (primary, muted, destructive) not raw colors (blue-500).
- Touch targets: minimum 44x44px on mobile (min-h-11 min-w-11 or p-3 on buttons).
- Accessibility: semantic HTML, aria-labels on icon buttons, keyboard navigation, focus-visible rings.
- Dark mode: use `class` strategy. Test both modes.
- Transitions: `transition-colors duration-150` on interactive elements.
- No inline styles. No `style={{}}`. Only Tailwind classes.
