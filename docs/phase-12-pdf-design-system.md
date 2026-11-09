# Site DNA — Phase 12: PDF Design System & Typography

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 12 — Typography & Print Design System  

---

## 1. Typography: Official Thmanyah Typeface Family

Per official ASAAS AI brand guidelines, all generated reports strictly embed the official Thmanyah font family as base64 WOFF2 subsets inside `@font-face` rules:

| Font Family | Weights Embedded | Primary Usage |
| :--- | :--- | :--- |
| **`Thmanyah Sans`** | Light (300), Regular (400), Medium (500), Bold (700), Black (900) | Primary document body text, data tables, metrics, UI controls |
| **`Thmanyah Serif Display`** | Light (300), Regular (400), Medium (500), Bold (700), Black (900) | Main cover title, major section headings (H1, H2), scorecard numbers |
| **`Thmanyah Serif Text`** | Light (300), Regular (400), Medium (500), Bold (700), Black (900) | Executive narrative, introductory paragraphs, quotations |

### Base64 Inlining Advantage
By embedding font files directly as base64 WOFF2 strings inside the HTML string passed to Playwright Chromium:
- Zero external font requests occur during rendering.
- Offline and air-gapped PDF generation works with 100% fidelity.
- Chromium generates proper ToUnicode CMap mappings, making all Arabic text in the resulting PDF fully selectable and searchable.

---

## 2. ASAAS AI Official Brand Color Palette

| Token | Hex Value | Usage in PDF & UI |
| :--- | :--- | :--- |
| **`brand-ink`** | `#221f1f` | Primary text color, cover background accents, deep borders |
| **`brand-gold`** | `#ba9555` | Accent highlights, score medals, callout borders, badges |
| **`brand-sand`** | `#d8cfbd` | Secondary divider lines, subtle card backgrounds |
| **`brand-cream`** | `#ede7da` | Page background tint, table header rows |
| **`brand-pure-cream`**| `#f7f4ee` | Card surfaces, metric pill containers |
| **`brand-gold-glow`** | `rgba(186, 149, 85, 0.15)` | Glowing highlights around critical metric scorecards |

---

## 3. Paged Media & CSS Print Specification

- **Page Box:** `@page { size: A4 portrait; margin: 16mm 14mm 16mm 14mm; }`
- **Break Controls:**
  - `page-break-before: always;` enforced before major sections (Critical Issues, Roadmap, Evidence Catalog).
  - `page-break-inside: avoid;` enforced on all finding cards, recommendation rows, and metric boxes.
- **Direction:** `direction: rtl;` for Arabic reports, `direction: ltr;` for English reports.
- **Header/Footer:** Running header with ASAAS AI logo and document title; running footer with page counter and SHA-256 verification string.
