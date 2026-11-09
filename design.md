# CloneGuard Design System

**Purpose:** A consistent, dark-mode design system for the CloneGuard Streamlit app (scam-call checker). Restyles the existing 128-widget UI to match a bento-grid, security-terminal aesthetic — no widget additions/removals, CSS-only.

**How to use:** Treat this as the single source of truth. Every page (`Check a call`, `Spoken verdict`, `Enroll a voice`, `Self-test`, `Incident log`) must implement the tokens, components, and responsive rules below. Paste the CSS block into `st.markdown(..., unsafe_allow_html=True)` at app start; configure `.streamlit/config.toml` per Section 6.

---

## 1. Design Tokens

### Color (hex + rgb)

| Token | Hex | RGB | Use |
|-------|-----|-----|-----|
| `--bg-page` | `#07080d` | `7,8,13` | Page background |
| `--bg-card` | `#0b0d15` | `11,13,21` | Card/surface face |
| `--bg-surface` | `#161a2b` | `22,26,43` | Tooltip, popover, dropdown |
| `--border-dim` | `rgba(255,255,255,0.10)` | — | Card border, dividers |
| `--border-bright` | `rgba(accent-rgb,0.6)` | — | Focus ring, active accent border |
| `--text-primary` | `#ffffff` | `255,255,255` | Headings, primary labels |
| `--text-secondary` | `#e2e8f0` | `226,232,240` | Body text |
| `--text-muted` | `#94a3b8` | `148,163,184` | Captions, secondary info |
| `--text-dim` | `#64748b` | `100,116,139` | Placeholder, disabled |

**Accent palette (as `r,g,b` for rgba math):**

| Name | Hex | RGB | Role |
|------|-----|-----|------|
| `--accent-indigo` | `#818cf8` | `129,140,248` | Primary actions, links |
| `--accent-cyan` | `#22d3ee` | `34,211,238` | Info, URLs, live dots |
| `--accent-emerald` | `#34d399` | `52,211,153` | Success, ✓ marks, low-risk |
| `--accent-fuchsia` | `#e879f9` | `232,121,249` | Terminal `$` prompt, warnings |
| `--accent-amber` | `#fbbf24` | `251,191,36` | Caution band, attention |

### Typography

```css
/* Primary mono: Martian Mono (Google Fonts) — terminal, numbers, code */
@import url('https://fonts.googleapis.com/css2?family=Martian+Mono:wght@400;500;700&display=swap');

:root {
  --font-mono: 'Martian Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono-stack: var(--font-mono);
  --font-sans-stack: var(--font-sans);
}

/* Scale (rem) */
--fs-xs: 0.75rem;   /* 12px — labels, badges */
--fs-sm: 0.875rem;  /* 14px — captions */
--fs-base: 1rem;    /* 16px — body */
--fs-lg: 1.125rem;  /* 18px — emphasized body */
--fs-xl: 1.25rem;   /* 20px — subheadings */
--fs-2xl: 1.5rem;   /* 24px — section titles */
--fs-3xl: 2rem;     /* 32px — page title */
--fs-4xl: 3rem;     /* 48px — hero numbers */

/* Weights */
--fw-normal: 400;
--fw-medium: 500;
--fw-semibold: 600;
--fw-bold: 700;

/* Tabular numbers on ALL numeric readouts */
.tabular-nums { font-variant-numeric: tabular-nums; font-family: var(--font-mono); }
```

### Spacing Scale

`4 / 8 / 12 / 16 / 24 / 32` (px) → map to `--space-1` … `--space-6`

| Token | Value | Use |
|-------|-------|-----|
| `--space-1` | `4px` | Icon gaps, inline tight |
| `--space-2` | `8px` | Button padding Y, form gaps |
| `--space-3` | `12px` | Card inner padding (compact) |
| `--space-4` | `16px` | Card padding (standard), grid gap |
| `--space-5` | `24px` | Card padding (comfortable), section gap |
| `--space-6` | `32px` | Page section spacing |

### Radius & Borders

| Token | Value | Use |
|-------|-------|-----|
| `--radius-sm` | `8px` | Buttons, badges, inputs |
| `--radius-md` | `12px` | Small cards, dropdowns |
| `--radius-lg` | `24px` | **Primary card radius (rounded-3xl)** |
| `--border-width` | `1px` | All borders |
| `--border-dim` | `rgba(255,255,255,0.10)` | Default card border |
| `--border-bright` | `rgba(var(--accent-rgb), 0.6)` | Focus, active, hover accent |

### Shadows / Glow

```css
/* Static subtle glow (replaces cursor-following React glow) */
--glow-static: radial-gradient(240px circle at 50% 0%, rgba(var(--accent-rgb), 0.08), transparent 70%);

/* Inner spotlight for cards */
--glow-inner: radial-gradient(200px circle at 50% 50%, rgba(var(--accent-rgb), 0.14), transparent 65%);

/* Faint grid overlay (page background) */
--grid-pattern: linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px);
background-size: 26px 26px;
```

---

## 2. Component Patterns

### 2.1 GlowCard (primary container)

```css
.glow-card {
  background: var(--bg-card);
  border: var(--border-width) solid var(--border-dim);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-5);
  position: relative;
  overflow: hidden;
  min-height: 200px; /* small */
  /* Static glow substitute */
  background-image: var(--glow-static), var(--glow-inner);
  background-blend-mode: normal, normal;
  transition: border-color var(--dur-fade), box-shadow var(--dur-fade);
}
.glow-card:hover {
  border-color: var(--border-bright);
  box-shadow: 0 0 0 1px var(--border-bright), 0 8px 32px rgba(0,0,0,0.4);
}
.glow-card:focus-within {
  border-color: var(--border-bright);
  box-shadow: 0 0 0 2px var(--border-bright);
}

/* Size variants */
.glow-card--tall   { min-height: 340px; }
.glow-card--large  { min-height: 420px; }
```

**Streamlit targeting:**
```css
/* Wrap st.container or st.expander content */
div[data-testid="stVerticalBlock"]:has(.glow-card) > div { ... }
```

### 2.2 TerminalPanel

```css
.terminal-panel {
  background: rgba(0,0,0,0.30);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  line-height: 1.6;
  color: var(--text-secondary);
  overflow-x: auto;
}
.terminal-line { margin: 2px 0; }
.terminal-prompt { color: var(--accent-fuchsia); }      /* $ */
.terminal-ok     { color: var(--accent-emerald); }      /* ✓ */
.terminal-info   { color: var(--text-muted); }          /* › */
.terminal-url    { color: var(--accent-cyan); }         /* ● */
.terminal-error  { color: var(--accent-amber); }
```

### 2.3 Data Readout (big number + label)

```css
.data-readout {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.data-readout__value {
  font-size: var(--fs-4xl);
  font-weight: var(--fw-bold);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  line-height: 1.1;
}
.data-readout__label {
  font-size: var(--fs-xs);
  font-weight: var(--fw-medium);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}
```

### 2.4 Nav Bar / Emoji Nav

```css
.nav-bar {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-dim);
  flex-wrap: wrap;
}
.nav-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: var(--fw-medium);
  color: var(--text-muted);
  text-decoration: none;
  transition: color var(--dur-fade), background var(--dur-fade);
}
.nav-item:hover, .nav-item[aria-current="page"] {
  color: var(--text-primary);
  background: rgba(255,255,255,0.05);
}
.nav-item[aria-current="page"]::before {
  content: ""; width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent-indigo);
  margin-right: var(--space-2);
}
```

### 2.5 Badge / Live Dot

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  border-radius: 999px;
  font-size: var(--fs-xs);
  font-weight: var(--fw-semibold);
  font-family: var(--font-mono);
}
.badge--low    { background: rgba(52,211,153,0.15); color: var(--accent-emerald); }
.badge--caution{ background: rgba(251,191,36,0.15); color: var(--accent-amber); }
.badge--high   { background: rgba(232,121,249,0.15); color: var(--accent-fuchsia); }
.badge--info   { background: rgba(34,211,238,0.15); color: var(--accent-cyan); }

.live-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-emerald);
  animation: pulse var(--dur-pulse) ease-in-out infinite;
}
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
```

### 2.6 Buttons

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: var(--fw-semibold);
  font-family: var(--font-sans);
  border: var(--border-width) solid transparent;
  cursor: pointer;
  transition: all var(--dur-fade);
}
.btn--primary {
  background: var(--accent-indigo);
  color: #07080d;
}
.btn--primary:hover { background: #93a0f9; }
.btn--secondary {
  background: transparent;
  border-color: var(--border-dim);
  color: var(--text-secondary);
}
.btn--secondary:hover {
  border-color: var(--border-bright);
  background: rgba(255,255,255,0.05);
}
.btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--bg-page), 0 0 0 4px var(--border-bright);
}
```

---

## 3. Responsive Rules

| Breakpoint | Columns | Card Heights | Font Scale | Padding |
|------------|---------|--------------|------------|---------|
| **Phone** `< 640px` | 1 | small: 180px, tall: 300px, large: 360px | Base -1 step | `--space-3` |
| **Tablet** `640–1023px` | 2 | small: 200px, tall: 340px, large: 420px | Base | `--space-4` |
| **Laptop** `≥ 1024px` | 4 (bento) | small: 200px, tall: 340px, large: 420px | Base +1 for hero | `--space-5` |

**Streamlit grid approximation:**
```python
# Laptop: 4-column bento via st.columns(4)
# Tablet: 2-column via st.columns(2)
# Phone: 1-column (default)

# Use CSS media queries for card min-heights:
@media (max-width: 639px) {
  .glow-card { min-height: 180px; }
  .glow-card--tall { min-height: 300px; }
  .glow-card--large { min-height: 360px; }
}
@media (min-width: 640px) and (max-width: 1023px) {
  .glow-card { min-height: 200px; }
  .glow-card--tall { min-height: 340px; }
  .glow-card--large { min-height: 420px; }
}
@media (min-width: 1024px) {
  .glow-card { min-height: 200px; }
  .glow-card--tall { min-height: 340px; }
  .glow-card--large { min-height: 420px; }
}
```

**Page-specific layout notes:**

| Page | Laptop Layout | Phone Layout |
|------|---------------|--------------|
| Check a call | 4-col: upload | results | composite | evidence | Single stack |
| Spoken verdict | 2-col: text | controls | Stack |
| Enroll a voice | 2-col: form | voiceprints list | Stack |
| Self-test | 4-col: metrics cards | sweep table | hard cases | Stack |
| Incident log | 2-col: filters | table | Stack |

---

## 4. Motion & Accessibility

### Animation Tokens

| Token | Value | Use |
|-------|-------|-----|
| `--dur-pulse` | `1.6s` | Live dot, subtle breathing |
| `--dur-slide` | `0.3s` | Panel slide, drawer |
| `--dur-blink` | `1s steps(2)` | Terminal cursor (optional) |
| `--dur-ring` | `1.2s cubic-bezier(.4,0,.2,1)` | Focus ring expand |
| `--dur-fade` | `0.3s` | Hover, border, bg transitions |

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### WCAG Contrast Notes

- All text on `--bg-page`/`--bg-card` meets **AA (4.5:1)** for `--text-primary`/`--text-secondary`
- `--text-muted` on card: **3.2:1** — use only for non-essential captions
- Accent colors on dark: **AA Large (3:1)** for `--accent-cyan`, `--accent-emerald`, `--accent-fuchsia`, `--accent-amber`
- Focus rings: 3px solid `--border-bright` — visible on all backgrounds

---

## 5. Streamlit Implementation Notes

### Where CSS Goes

```python
# At top of app.py, before any st.* calls
st.markdown("""
<style>
/* Paste the full CSS from Sections 1–2 here */
/* Include @import for Martian Mono */
</style>
""", unsafe_allow_html=True)
```

### `.streamlit/config.toml`

```toml
[theme]
base = "dark"
primaryColor = "#818cf8"           # --accent-indigo
backgroundColor = "#07080d"        # --bg-page
secondaryBackgroundColor = "#0b0d15" # --bg-card
textColor = "#e2e8f0"              # --text-secondary
font = "sans serif"                # Body uses system-ui; mono via CSS
```

### Loading Martian Mono

```html
<!-- In the same <style> block or via st.components.v1.html -->
@import url('https://fonts.googleapis.com/css2?family=Martian+Mono:wght@400;500;700&display=swap');
```
Or preload for faster paint:
```html
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Martian+Mono:wght@400;500;700&display=swap" onload="this.rel='stylesheet'">
```

### What CANNOT Be Done in Streamlit (React → Streamlit Gap)

| React Feature | Streamlit Substitute |
|---------------|---------------------|
| Cursor-following glow border | Static radial glow (`--glow-static`, `--glow-inner`) on card hover/focus |
| Per-pixel grid mask | CSS `background-size: 26px 26px` repeating gradient |
| True bento grid (CSS Grid) | `st.columns(n)` + media-query card heights |
| Terminal blinking cursor | CSS animation on `::after` pseudo (optional, respects `prefers-reduced-motion`) |
| Framer Motion staggered entry | Single `fade-in` on `.glow-card` via `animation: fade var(--dur-fade)` |

**Honest assessment:** The security-terminal identity survives. The bento rhythm survives. The cursor-reactive "magic" becomes a tasteful static glow — acceptable for a local-first tool.

---

## 6. Do / Don't (Anti-Slop Rules)

### Do
- Use semantic tokens (`var(--accent-emerald)`) everywhere — never raw hex
- Apply `font-variant-numeric: tabular-nums` to **every** number (metrics, cosine, thresholds, dates)
- Keep terminal panel mono-only; no sans-serif leaks
- Reserve `--accent-fuchsia` for terminal `$` prompts and warnings only
- Use `glow-card` for every top-level section container
- Test at 320px, 768px, 1280px, 1920px

### Don't
- ❌ Purple/pink blob gradients anywhere (no `bg-gradient-to-br from-purple-500 via-pink-500`)
- ❌ Generic glassmorphism (`backdrop-filter: blur`) on everything — only terminal panel gets `rgba(0,0,0,0.30)`
- ❌ Emoji soup in headings — one emoji max per section, as nav icon only
- ❌ "AI-cloned voice" phrasing — use "synthetic" only in the Limitations expander sentence
- ❌ Mixing radius values — only `--radius-sm`, `--radius-md`, `--radius-lg`
- ❌ Adding widgets, removing widgets, changing logic — this is a **restyle only**

---

## 7. QA Checklist (Code Review)

- [ ] `Martian Mono` loads (check Network tab for Google Fonts request)
- [ ] All numbers render with tabular-nums (inspect computed `font-variant-numeric`)
- [ ] Page background is `#07080d`, cards are `#0b0d15`
- [ ] Hover on any card shows bright accent border (indigo by default)
- [ ] Focus-visible ring appears on tab navigation (3px, accent color)
- [ ] `prefers-reduced-motion` disables pulse, fade, slide
- [ ] Phone (320px): single column, cards ≥180px tall
- [ ] Tablet (768px): two columns, cards ≥200px tall
- [ ] Laptop (1280px): four columns where appropriate, cards ≥200px tall
- [ ] Terminal panel uses only mono font, fuchsia `$`, emerald `✓`, cyan `●`
- [ ] No raw hex colors in CSS except in `:root` token definitions
- [ ] `.streamlit/config.toml` matches Section 5 tokens