# CloneGuard Design System v2

**Purpose:** Matrix/opencode theme for the CloneGuard Streamlit app (scam-call checker). **v2 entirely replaces v1's glow-card/terminal/accent-rainbow dark theme.** Nav changed from radio to real buttons (no emojis), palette strict: black, white, grayscale, matrix green only. CSS-only restyle.

**How to use:** Single source of truth. Every page (`Check a call`, `Spoken verdict`, `Enroll a voice`, `Self-test`, `Incident log`) implements tokens, components, responsive rules below. Paste the CSS block into `st.markdown(..., unsafe_allow_html=True)` at app start; configure `.streamlit/config.toml` per Section 6.

---

## 1. Design Tokens

### Color (monochrome + matrix green only)

| Token | Value | Use |
|-------|-------|-----|
| `--bg-page` | `#000000` | Page background |
| `--bg-card` | `#0a0a0a` | Surface/card (subtle lift) |
| `--text-primary` | `#ffffff` | Display headings, primary labels |
| `--text-secondary` | `#e5e5e5` | Body text |
| `--text-muted` | `#9ca3af` | Captions, metadata (WCAG AA on black: 7.0:1) |
| `--text-dim` | `#6b7280` | Placeholder, disabled |
| `--accent-green` | `#2eff6a` | **Primary accent (opencode matrix theme: rainGreen)** — primary buttons, active nav, focus rings, links, spinner, progress, success alerts, checkbox/radio accents |
| `--accent-green-dim` | `#1cc24b` | Dim/hover state for primary |
| `--accent-green-hi` | `#62ff94` | Hi/active state for primary |
| `--hairline` | `rgba(255,255,255,0.12)` | Separators, borders, nav hover underline |

**LEGAL COLORS ONLY (whitelist):** `#000000 #0a0a0a #ffffff #e5e5e5 #9ca3af #6b7280`, any `rgba(255,255,255,x)`, and greens `#2eff6a #1cc24b #62ff94` (+ their rgba forms). Everything else in app.py CSS = violation.

**Dot-grid background (signature motif):**
```css
background:
  radial-gradient(circle, white 1px, transparent 1px)
  0 0 / 20px 20px repeat;
opacity: 0.15;
```

### Typography

```css
/* Chakra Petch (display + body) + Martian Mono (numbers only) — single request */
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@300;400;500;600;700&family=Martian+Mono:wght@400;500&display=swap');

:root {
  --font-display: 'Chakra Petch', system-ui, -apple-system, Segoe UI, sans-serif;
  --font-body:    'Chakra Petch', system-ui, -apple-system, Segoe UI, sans-serif;
  --font-mono:    'Martian Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}

/* Display scale — giant thin uppercase */
--fs-display: clamp(2.5rem, 8vw, 6.5rem);   /* 40px → 104px */
--fs-h1:      clamp(1.75rem, 4.5vw, 3.25rem);      /* 28px → 52px */
--fs-h2:      clamp(1.25rem, 3vw, 2.25rem);      /* 20px → 36px */
--fs-body:    1rem;                          /* 16px */
--fs-caption: 0.875rem;                      /* 14px */
--fs-small:   0.875rem;                      /* 14px */

/* Weights */
--fw-light:    700;   /* display headings — ensured 700 */
--fw-regular:  500;   /* body — 500 minimum */
--fw-medium:   600;   /* emphasis / labels / captions */
--fw-semibold: 700;   /* active nav, strong */

/* Display rule: uppercase + tracking-wide + leading-none */
.display { font-family: var(--font-display); font-weight: var(--fw-light); text-transform: uppercase; letter-spacing: 0.05em; line-height: 1; }
.caption  { font-family: var(--font-body);   font-size: var(--fs-caption); line-height: 1.25; color: var(--text-muted); max-width: 250px; }
.small-caps { font-family: var(--font-body); font-size: var(--fs-small); font-weight: var(--fw-medium); text-transform: lowercase; letter-spacing: 0.08em; color: var(--text-muted); }
.data-readout { font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-size: var(--fs-h1); font-weight: var(--fw-medium); color: var(--text-primary); }
```

### FONT SWEEP RULE

Chakra Petch on 100% of elements via broad hammer rule early in sheet; Martian Mono re-asserted AFTER hammer on numeric/code targets only (metrics, dataframes, tables, code blocks, `.data-readout`, tabular-nums selectors). Result: Chakra Petch everywhere except numbers/code = Martian Mono. No font SIZE changes (title clamp/caption 14px/body 16px rules stay as-is).

### Spacing (generous whitespace scale)

`--space-1: 4px`, `--space-2: 8px`, `--space-3: 16px`, `--space-4: 24px`, `--space-5: 48px`, `--space-6: 80px`, `--space-7: 120px`

### Radius & Borders (minimal — editorial prefers square/hairline)

`--radius-sm: 4px` (buttons only), `--radius-none: 0` (cards, panels), `--border-w: 1px`, `--border-color: var(--hairline)`

---

## 2. Component Patterns (Streamlit-targeted CSS)

### 2.1 DotGridBackground

```css
.stApp {
  background-color: var(--bg-page);
  background-image: radial-gradient(circle, white 1px, transparent 1px);
  background-size: 20px 20px;
}
.stApp::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: -1;
  background: inherit; opacity: 0.15;
}
```

### 2.2 DisplayHeading (giant thin uppercase)

```css
.display-heading {
  font-family: var(--font-display); font-weight: var(--fw-light);
  font-size: var(--fs-display); line-height: 1; letter-spacing: 0.05em;
  text-transform: uppercase; color: var(--text-primary); margin: 0;
}
.display-heading--h1 { font-size: var(--fs-h1); }
.display-heading--h2 { font-size: var(--fs-h2); }
```

### 2.3 CaptionBlock (tiny muted side text)

```css
.caption-block {
  font-family: var(--font-body); font-size: var(--fs-caption);
  line-height: 1.25; color: var(--text-muted); max-width: 250px;
}
.caption-block--sm { font-size: var(--fs-small); max-width: 180px; }
```

### 2.4 NavButtons (real sidebar buttons, full width, primary for active)

```css
.nav-buttons { display: flex; flex-direction: column; gap: var(--space-2); padding: var(--space-2) 0; }
.nav-buttons button {
  display: block; width: 100%; text-align: left; padding: 0.4rem 0.75rem;
  border-radius: var(--radius-sm); font-family: var(--font-body);
  font-size: var(--fs-small); font-weight: var(--fw-medium);
  border: var(--border-w) solid transparent; background: transparent;
  color: var(--text-secondary); transition: opacity 0.2s, background 0.2s, border 0.2s;
}
.nav-buttons button:hover { background: rgba(255,255,255,0.05); border-color: var(--text-dim); }
.nav-buttons button[aria-current="page"] { background: var(--accent-green); color: var(--bg-page); border-color: var(--accent-green); }
.nav-buttons button[aria-current="page"]:hover { background: var(--accent-green-hi); opacity: 0.9; }
```

**No emojis in labels.** Labels = plain page names: "Check a call", "Spoken verdict", "Enroll a voice", "Self-test", "Incident log". "Choose a page:" caption rendered above buttons.

### 2.5 HairlineSeparator

```css
.hairline { height: 1px; background: var(--hairline); border: 0; margin: var(--space-4) 0; }
.hairline--short { width: 60px; margin-left: 0; }
```

### 2.6 SmallCapsMeta

```css
.meta-line { font-family: var(--font-body); font-size: var(--fs-small); font-weight: var(--fw-medium); text-transform: lowercase; letter-spacing: 0.08em; color: var(--text-muted); }
```

### 2.7 Wordmark/Logo (bold-italic top-left)

```css
.wordmark {
  font-family: var(--font-display); font-weight: var(--fw-semibold);
  font-style: italic; font-size: var(--fs-body); color: var(--text-primary);
  text-transform: lowercase; letter-spacing: 0.05em;
}
```

### 2.8 DataReadout (mono numbers only)

```css
.data-readout { font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-size: var(--fs-h1); font-weight: var(--fw-medium); color: var(--text-primary); line-height: 1.1; }
.data-readout--sm { font-size: var(--fs-h2); }
.data-readout__label { font-family: var(--font-body); font-size: var(--fs-caption); font-weight: var(--fw-medium); text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); margin-top: var(--space-1); }
```

### 2.9 VerticalSideLabel (rotated 90deg right edge)

```css
.side-label {
  position: fixed; right: 0; top: 50%; transform: translateY(-50%) rotate(90deg);
  font-family: var(--font-body); font-size: var(--fs-caption); font-weight: var(--fw-medium);
  text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-dim);
  white-space: nowrap; pointer-events: none; z-index: 100;
}
```

### 2.10 EmptyStateCTA (Spoken verdict page)

```python
# Single button added to empty state:
st.button(
    "Open Check a call",
    key="cta_open_check",
    on_click=lambda: st.session_state.update({"page": "Check a call"}),
)
```

Label exactly "Open Check a call". Only NEW widget added.

### 2.11 Alert Overrides (ALL Streamlit defaults overridden to palette)

- **Info** → grayscale: dark gray bg `#0a0a0a`, white text, gray border (`var(--text-muted)`)
- **Success** → matrix green: green-tinted bg `rgba(46,255,106,0.10)`, text `#2eff6a`, green border
- **Warning** → grayscale: gray border (`var(--text-dim)`), white text — amber/orange FORBIDDEN
- **Error** → grayscale: near-black bg `#050505`, white bold text, `#ffffff`-ish border — red FORBIDDEN
- Both modern `[data-testid="stAlert"]` and legacy `.stAlert/.stInfo/.stSuccess/.stWarning/.stError` selectors overridden
- Inner markdown/icon colors forced to palette
- `[data-testid="stException"]` also overridden

---

## 3. Responsive Rules

| Breakpoint | Display Size | Caption Position | Nav | Page Padding |
|------------|--------------|------------------|-----|--------------|
| **Phone** `< 640px` | `clamp(3.75rem, 14vw, 5rem)` | Stacked **below** heading | Stacked buttons | `--space-3` / `--space-4` |
| **Tablet** `640–1023px` | `clamp(4.5rem, 10vw, 7rem)` | Beside heading (2-col) | Horizontal, full | `--space-4` / `--space-5` |
| **Laptop** `≥ 1024px` | `clamp(6rem, 12vw, 10rem)` | Beside heading (2-col) | Horizontal, full | `--space-5` / `--space-6` |
| **Wide** `≥ 1440px` | `10rem` (max) | Beside heading, wider gutter | Horizontal, full | `--space-6` / `--space-7` |

**Streamlit approximation (single column default):**
```python
# Use st.container() for vertical stacking; st.columns([3,1]) for heading + caption beside on tablet+
# Media queries in CSS handle display font-size via clamp()
# Nav: render as horizontal links; on phone use st.selectbox or collapse via CSS @media (max-width: 639px) { .text-nav { display: none; } }
```

---

## 4. Motion & Accessibility

**Minimal motion (editorial = restrained):**
```css
.nav-buttons button { transition: opacity 0.2s ease, background-color 0.2s ease, border-color 0.2s ease; }
.hairline, .caption-block, .display-heading { transition: opacity 0.3s ease; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**WCAG Contrast (all on `#000000`):**
- White (`#ffffff`) — 21:1 ✓
- `--text-secondary` (`#e5e5e5`) — 18.5:1 ✓
- `--text-muted` (`#9ca3af`) — 7.0:1 ✓ (AA)
- `--text-dim` (`#6b7280`) — 4.5:1 ✓ (AA large only)
- `--hairline` (`rgba(255,255,255,0.12)`) — decorative only
- `--accent-green` (`#2eff6a`) — 4.8:1 ✓ (AA large)

---

## 5. Streamlit Implementation Notes

### CSS Injection (single block, BEFORE any `st.*` call)

```python
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@300;400;500;600;700&family=Martian+Mono:wght@400;500&display=swap');
/* Paste ALL tokens + components from Sections 1–2 here */
</style>
""", unsafe_allow_html=True)
```

### `.streamlit/config.toml`

```toml
[theme]
base = "dark"
primaryColor = "#2eff6a"
backgroundColor = "#000000"
secondaryBackgroundColor = "#0a0a0a"
textColor = "#e5e5e5"
font = "sans serif"
```

### Honest Gap Table (what Streamlit cannot do)

| Feature | Limitation | Substitute |
|---------|------------|------------|
| True CSS Grid bento layout | `st.columns` is flex-based, no grid-template-areas | `st.columns(n)` + media-query card heights |
| Rotated `VerticalSideLabel` on Streamlit elements | Fixed positioning on internal widgets is unreliable | Render as horizontal `.meta-line` in sidebar or footer |
| `st.dataframe` / `st.table` styling | Canvas-rendered; CSS cannot reach cell fonts | Use `st.markdown` with hand-crafted HTML table for mono numbers |
| Hairline separators on native widgets | Widget containers add padding/borders | Wrap in `st.container()` + custom CSS class |
| Dot-grid on `st.sidebar` | Separate iframe-ish context | Apply same background to `[data-testid="stSidebar"]` |

---

## 6. Do / Don't (Anti-AI-Slop)

### Do

- Extreme type-scale contrast: giant display (300 weight) + tiny caption (12px)
- Generous whitespace; hairline rules (`1px`, `rgba(255,255,255,0.12)`)
- **One accent family only** (matrix green: `#2eff6a` primary, `#1cc24b` dim, `#62ff94` hi)
- Uppercase + `letter-spacing: 0.05em` + `line-height: 1` on all display headings
- Chakra Petch for all prose/headings; Martian Mono **only** for numeric readouts
- `prefers-reduced-motion` respected; opacity-only transitions
- **Real sidebar buttons** (full width, `type="primary"` for active, no emojis)
- **All Streamlit defaults overridden** — no leaked blues/reds/ambers
- **Text labels never overlap** (QA: check uploader/expander/buttons visually on all 5 pages)

### Don't

- ❌ Glow cards, radial accent gradients, glassmorphism/backdrop-blur
- ❌ Rainbow accent palettes (v1 had 6 accents — v2 has ONE family: matrix green)
- ❌ **Emoji nav** — nav labels are plain text only ("Check a call", not "🔍 Check a call"). Tab icon `🛡️` in `set_page_config` is fine.
- ❌ Any color outside the 4-family whitelist (black, white, grayscale, matrix green)
- ❌ **Un-overridden Streamlit defaults** — no blue `#0068c9`, amber `#fffc63`, red `#7d3326`, green `#29b06d`, blue `#83c9ff` anywhere
- ❌ Generic dark-theme-with-purple, decorative blobs, rounded-everything
- ❌ Raw hex outside `:root` tokens
- ❌ Adding/removing widgets or changing logic beyond approved changes (nav buttons replace radio; one CTA button on Spoken verdict empty state)

---

## 7. QA Checklist

- [ ] `Chakra Petch` + `Martian Mono` load (Network tab: single Google Fonts request)
- [ ] Dot-grid: `radial-gradient(circle, white 1px, transparent 1px)` at `20px 20px`, `opacity: 0.15`
- [ ] Display headings: `font-weight: 700`, `text-transform: uppercase`, `letter-spacing: 0.05em`, `line-height: 1`, `clamp(2.5rem, 8vw, 6.5rem)`
- [ ] Captions: `14px`, `#9ca3af`, `max-width: 250px`, stacked on phone / beside on laptop
- [ ] **Nav: 5 real sidebar buttons**, full width, muted inactive, matrix green active (`type="primary"`), `padding: 0.4rem 0.75rem`, no emojis
- [ ] **Text labels never overlap** (QA: check uploader/expander/buttons visually on all 5 pages)
- [ ] Empty-state CTA on Spoken verdict: "Open Check a call" button navigates to Check page
- [ ] Single accent family `#2eff6a`/`#1cc24b`/`#62ff94` used sparingly (active nav, primary buttons, focus, links, spinner, progress, success alerts, checkbox/radio accents)
- [ ] **Material icons render as glyph icons — no ligature words (upload, keyboard_arrow_right) visible as text anywhere**
- [ ] Hairline separators: `1px solid rgba(255,255,255,0.12)`
- [ ] `prefers-reduced-motion` disables all transitions
- [ ] Phone (320px): single column, display ~60px, captions stacked
- [ ] Laptop (1280px+): display ~160px, captions beside, generous padding
- [ ] `.streamlit/config.toml` `primaryColor = "#2eff6a"`
- [ ] **Palette audit:** grep for `#f43f5e`, `#ea580c`, `rgba(244,63,94` → 0 hits; `#2eff6a` ≥ 3; no hex outside whitelist
- [ ] **Font sweep:** `Archivo` = 0; broad `font-family` hammer present; Martian Mono re-asserted AFTER it; `@import` still first line
- [ ] **Banned words:** "AI-cloned voice"=0, "detects AI-cloned"=0, "deepfake"=0, `synthetic` EXACTLY 1
- [ ] No v1 tokens (`--glow-static`, `--accent-indigo`, `--radius-lg`, `Martian Mono` on headings) remain
- [ ] **Radio count = 0** (replaced by buttons)
- [ ] **Material icons render as glyph icons — no ligature words (upload, keyboard_arrow_right) visible as text anywhere**
- [ ] All 5 pages render with 0 exceptions; original content widgets preserved