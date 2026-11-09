# Site DNA — Phase 07.5: Design System & Visual Specification

## 1. Design Philosophy

The Site DNA frontend is built strictly following the **ASAAS AI Design System** guidelines. It delivers an enterprise-grade, high-trust user interface blending modern liquid-glass styling, sophisticated micro-interactions, and Arabic-first typography.

---

## 2. Brand Tokens & Color Palette

### 2.1 CSS Custom Properties (Light & Dark Theme)

The UI automatically respects system preferences and allows manual toggle between light and dark themes using `data-theme="dark"` / `data-theme="light"` on `document.documentElement`:

| Token | Light Theme | Dark Theme | Purpose |
|---|---|---|---|
| `--brand-ink` | `#111625` | `#F5F6F8` | Primary text and high-contrast headlines |
| `--brand-gold` | `#D4A359` | `#E5B869` | Accent, active focus rings, key metrics, brand CTA |
| `--brand-gold-tint` | `rgba(212,163,89,0.12)` | `rgba(229,184,105,0.16)` | Selected cards, subtle badges, active tabs |
| `--brand-sand` | `#F8F6F0` | `#161B26` | Card backgrounds, subtle borders, secondary panels |
| `--surface-base` | `#FAFAFB` | `#0C0F17` | Root application background |
| `--surface-card` | `rgba(255,255,255,0.78)` | `rgba(22,27,38,0.72)` | Liquid-glass cards with blur backdrop |
| `--border-subtle` | `rgba(17,22,37,0.08)` | `rgba(245,246,248,0.08)` | Dividers, card borders, table separators |
| `--border-glow` | `rgba(212,163,89,0.35)` | `rgba(229,184,105,0.45)` | Focused inputs, hovered cards |

---

## 3. Typography: Thmanyah Font Family

Typography is driven by the licensed **Thmanyah** font suite bundled directly within `src/asaas-ui/assets/fonts/`:

```css
@font-face {
  font-family: 'ThmanyahSans';
  src: url('./assets/fonts/thmanyahsans-Regular.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}
@font-face {
  font-family: 'ThmanyahSans';
  src: url('./assets/fonts/thmanyahsans-Medium.woff2') format('woff2');
  font-weight: 500;
  font-display: swap;
}
@font-face {
  font-family: 'ThmanyahSans';
  src: url('./assets/fonts/thmanyahsans-Bold.woff2') format('woff2');
  font-weight: 700;
  font-display: swap;
}
@font-face {
  font-family: 'ThmanyahSerifDisplay';
  src: url('./assets/fonts/thmanyahserifdisplay-Bold.woff2') format('woff2');
  font-weight: 700;
  font-display: swap;
}
```

- **Headlines & Big Metrics**: `ThmanyahSerifDisplay`, Bold, letter-spacing tight.
- **Body & Controls**: `ThmanyahSans`, Regular & Medium, line-height 1.6 for enhanced Arabic readability.
- **Code & Raw Data**: System monospace (`ui-monospace`, `SFMono-Regular`, `Consolas`).

---

## 4. Liquid-Glass Components & Visual Hierarchy

1. **Liquid-Glass Cards (`glass-card`)**:
   - Background: `var(--surface-card)`
   - Backdrop filter: `blur(16px)`
   - Border: `1px solid var(--border-subtle)`
   - Shadow: `0 8px 32px 0 rgba(0, 0, 0, 0.08)`
   - Transition: `box-shadow 0.25s ease, border-color 0.25s ease`

2. **Status Pills (`status-pill`)**:
   - `completed`: Emerald tint (`bg-emerald-500/10 text-emerald-600 border-emerald-500/20`)
   - `running`: Cyan tint with pulse dot (`bg-cyan-500/10 text-cyan-500 border-cyan-500/20`)
   - `queued`: Amber tint (`bg-amber-500/10 text-amber-500 border-amber-500/20`)
   - `failed`: Rose tint (`bg-rose-500/10 text-rose-500 border-rose-500/20`)
   - `planned`: Slate tint with lock icon (`bg-slate-500/10 text-slate-400 border-slate-500/20`)

3. **Buttons (`asaas-btn-primary`, `asaas-btn-secondary`)**:
   - Primary: Solid Gold gradient with Ink text, bold Thmanyah Sans, subtle glow on hover.
   - Secondary: Liquid-glass button with border-subtle and gold hover accent.

4. **Slide-Out Evidence Drawer (`evidence-drawer`)**:
   - Fixed side sheet with backdrop blur.
   - Smooth slide-in transition from right (RTL) or left (LTR).
   - Shows raw DOM node selectors, computed CSS values, bounding boxes, and screenshot crops.

---

## 5. Bidirectional (RTL / LTR) Architecture

- Default language: **Arabic (`ar`)** with `dir="rtl"`.
- Secondary language: **English (`en`)** with `dir="ltr"`.
- Seamless switching via `I18nProvider` which synchronizes `<html lang="..." dir="...">` dynamically.
- Logical CSS properties (`margin-inline-start`, `padding-inline-end`, `border-inline-start`) ensure zero visual breakage across directions.
- Tested and verified on 375px mobile screens with zero horizontal overflow (`scrollWidth === clientWidth`).
