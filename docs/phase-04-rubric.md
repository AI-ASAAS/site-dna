# Site DNA — Phase 04 Visual Identity Scoring Rubric
## Explainable, Evidence-Backed Brand & Interface Scoring Framework

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Project:** Site DNA  
**Phase:** 04 — Visual Identity Analysis  
**Standard:** WCAG 2.1 Contrast Principles, ASAAS AI Design System Guidelines  

---

## 1. Principles of Explainable Scoring

The Site DNA scoring engine adheres to five strict integrity rules:
1. **Evidence-Backed Deductions:** Every point deduction must be anchored to at least one specific, validated finding (`finding_id`) referencing real source evidence (`evidence_id`).
2. **No Default Zeroes:** If a dimension lacks sufficient evidence (e.g. cross-page consistency on a single-page site), it is marked `not_assessed` or `insufficient_evidence` and excluded from the normalized score calculation, rather than penalized with zero.
3. **Layer Separation:** Deterministic measurements (e.g. contrast ratio, font size ratio, color count) are clearly separated from AI qualitative assessments.
4. **Transparent Normalization:** The overall score (0–100) is computed only when at least 3 of the 5 dimensions meet minimum evidence coverage thresholds.
5. **No Business Outcome Guarantees:** Scores reflect observable interface quality and design consistency; they do not guarantee commercial conversion or marketing outcomes.

---

## 2. Dimension Weights and Objectives

| Dimension | Weight | Primary Objective | Key Evaluated Attributes |
|---|:---:|---|---|
| **1. Color System & Harmony** | 20% | Evaluate palette clarity, functional color roles, and contrast. | Dominant palette, CTA accent distinction, neutral surfaces, WCAG text/background contrast. |
| **2. Typography & Readability** | 20% | Evaluate text scale, legibility, and typographic hierarchy. | Font families ($\le 3$ ideal), heading/body size ratio ($\ge 1.4$), line heights, Arabic RTL readability. |
| **3. Visual Hierarchy** | 20% | Evaluate visual priority, headline emphasis, and CTA prominence. | Headline prominence, primary CTA visual distinction, section boundaries, whitespace balance. |
| **4. Cross-Page & Component Consistency** | 25% | Evaluate repeatability of UI components across pages. | Header, navigation, buttons, cards, corner radii, footer uniformity across crawled pages. |
| **5. Responsive Visual Consistency** | 15% | Evaluate visual continuity and layout stability between viewports. | Desktop-to-mobile brand fidelity, absence of horizontal overflow, mobile font/touch scaling. |

**Total Weighted Maximum:** 100%

---

## 3. Detailed Scoring Bands & Anchors

Each dimension starts at a baseline of **100 points** and applies bounded deductions based on validated findings:

### 3.1 Color System & Harmony (Weight: 20%)
- **90–100 (Exemplary):** Clear primary, secondary, and neutral palette; high text contrast ($\ge 4.5:1$); distinct CTA accent.
- **75–89 (Good):** Cohesive colors with minor inconsistency (e.g. 2 slightly different button hues or mild border contrast issue).
- **55–74 (Fair):** Excessive unrelated colors ($> 6$ saturated hues), indistinct CTA button color, or low text contrast in secondary sections.
- **0–54 (Poor):** Severe contrast failures on body/heading text, chaotic color usage with no functional hierarchy.
- **Deductions:**
  - Critical text contrast failure on primary content: -15 pts per occurrence (max -30).
  - Indistinct CTA accent (CTA color matches secondary body text): -10 pts.
  - Excessive palette fragmentation ($> 8$ distinct accent hues without purpose): -10 pts.

### 3.2 Typography & Readability (Weight: 20%)
- **90–100 (Exemplary):** Well-defined type scale (H1:body ratio $\ge 1.6$), 1–2 font families, comfortable line height (1.4–1.7), excellent Arabic RTL support.
- **75–89 (Good):** Legible typography with minor scale flattening (H1:body ratio 1.3–1.5) or slightly tight line height.
- **55–74 (Fair):** Weak differentiation between headings and paragraphs, $> 3$ disparate font families, or missing line-height causing crowded text.
- **0–54 (Poor):** Tiny illegible text ($< 12px$), distorted font weights, or broken RTL text flow.
- **Deductions:**
  - Weak heading/body scale differentiation (ratio $< 1.3$): -12 pts.
  - Excessive font families ($> 3$ unrelated stacks): -10 pts.
  - Arabic text rendered without RTL alignment or proper direction: -15 pts.
  - Line height $< 1.2$ on multi-line text: -8 pts.

### 3.3 Visual Hierarchy (Weight: 20%)
- **90–100 (Exemplary):** Immediate clarity of primary message; hero headline stands out; primary CTA is unambiguously prominent; clean whitespace.
- **75–89 (Good):** Good hierarchy with minor visual competition (e.g. secondary banner competing slightly with hero headline).
- **55–74 (Fair):** Cluttered layout, primary CTA hard to spot within 3 seconds, or uniform visual weight across diverse sections.
- **0–54 (Poor):** No discernable visual anchor; headlines, links, and text blend into an undifferentiated block.
- **Deductions:**
  - Missing or weak primary call-to-action distinction: -12 pts.
  - Visual competition between hero and secondary elements: -8 pts.
  - Inconsistent section spacing or cramped container padding: -6 pts.

### 3.4 Cross-Page & Component Consistency (Weight: 25%)
- **Status `not_assessed`:** If only 1 page was crawled/analyzed, this dimension is explicitly marked `not_assessed` and its weight is proportionally redistributed to the remaining 4 dimensions.
- **90–100 (Exemplary):** Pixel-perfect header/footer persistence, uniform button padding/radius, consistent card designs across pages.
- **75–89 (Good):** Consistent layout with small variance (e.g. button corner radius shifts from 6px to 8px across two subpages).
- **55–74 (Fair):** Substantial component drift (e.g. different header layout or completely different button styles on subpages).
- **0–54 (Poor):** Disconnected pages appearing as separate, unrelated websites.
- **Deductions:**
  - Inconsistent button styling for identical actions across pages: -10 pts.
  - Header or navigation structure jumps between pages: -15 pts.
  - Mismatched card or container visual treatments: -8 pts.

### 3.5 Responsive Visual Consistency (Weight: 15%)
- **90–100 (Exemplary):** Seamless visual brand preservation on mobile; zero horizontal overflow; readable font scales; touch-friendly buttons ($\ge 44px$).
- **75–89 (Good):** Good mobile adaptation with minor styling changes (e.g. card padding slightly too generous on narrow viewports).
- **55–74 (Fair):** Mobile horizontal overflow observed (`scrollWidth > viewportWidth`), or buttons scale down below touch usability.
- **0–54 (Poor):** Severe mobile breakage, content clipped offscreen, or unreadable scaled-down desktop rendering.
- **Deductions:**
  - Horizontal overflow detected on mobile viewport: -20 pts.
  - Text scales below 13px on mobile body: -10 pts.
  - Mobile touch target height $< 36px$: -10 pts.

---

## 4. Overall Score Calculation

Let $S_i$ be the score of assessed dimension $i$, and $W_i$ its configured weight:
$$\text{Overall Score} = \frac{\sum_{i \in \text{Assessed}} (S_i \times W_i)}{\sum_{i \in \text{Assessed}} W_i}$$

If fewer than 3 dimensions have sufficient evidence, `overall_score` returns `null` with an explicit notice of insufficient coverage.
