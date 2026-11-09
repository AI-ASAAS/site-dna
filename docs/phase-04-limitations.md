# Site DNA — Phase 04 Limitations & Architectural Boundaries
## Known Constraints, Model Uncertainty & Scope Delimitations

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Project:** Site DNA  
**Phase:** 04 — Visual Identity Analysis  
**Date:** November 7, 2026  

---

## 1. Subjective Design Judgments vs. Objective Measurements

1. **Aesthetic Style vs. Usability:**
   A minimalist website (e.g. brutalist typography, monochrome palette, generous negative space) is not inherently inferior to a highly ornamented website. The AI Visual Identity Analyst is instructed never to penalize minimalism or unconventional design unless concrete evidence demonstrates impaired readability or ambiguous visual hierarchy.
2. **Interpretative Nature of Design Critique:**
   Statements regarding "brand harmony" or "visual elegance" are professional design interpretations, not mathematical constants. They are classified as `ai_interpretation` and never as `observed_measurement`.
3. **Absence of Stated Brand Guidelines:**
   In the absence of an official client brand manual, the system can only evaluate the **observed visual consistency** of the rendered artifact. It does not certify compliance with unseen internal brand specifications.

---

## 2. Multimodal AI & Model Uncertainty

1. **Vision Model Resolution Limits:**
   While `gemini-3.8-flash` processes high-resolution image inputs, fine micro-typography or tiny icon details in wide full-page screenshots may undergo resolution tiling. Critical text measurements must always be backed by deterministic DOM/CSS extraction records.
2. **Hallucination Prevention via Evidence Validation:**
   Generative AI models may occasionally synthesize plausible-sounding CSS properties or element IDs. Site DNA enforces a strict deterministic `EvidenceValidator` gate that discards or quarantines any finding whose referenced `evidence_id` or measurements cannot be reconciled with Layer A/B source data.
3. **No Marketing or Conversion Predictions:**
   The agent does not predict commercial conversion rate increases (e.g. "This change will boost sales by 15%"). All impact classifications (`high`, `medium`, `low`) reflect visual clarity and interface usability.

---

## 3. Data & Artifact Coverage Boundaries

1. **Single-Page Site Limitation:**
   When a site contains only one crawled page, cross-page consistency cannot be calculated. The system marks dimension 4 as `not_assessed` and explains this transparently in the final report.
2. **Font Stack vs. Rendered Glyphs:**
   The computed CSS `font-family` property lists the developer's prioritized font stack. Without local canvas glyph inspection, the system cannot verify whether a user's operating system fell back to a generic serif/sans-serif system font.
3. **Color Contrast on Complex Backgrounds:**
   Deterministic WCAG contrast calculation is restricted to elements where both foreground text and background colors are fully opaque and measurable. Transparent overlays, CSS linear gradients, and background image textures are flagged as `indeterminate_contrast` to avoid misleading scores.
4. **Height Ceilings:**
   Full-page screenshots enforce a strict upper bound of 12,000 pixels to prevent memory exhaustion on infinite-scroll pages.

---

## 4. Security & Network Isolation Boundaries

1. **Application-Level Interception:**
   Browser network isolation is enforced via Playwright's CDP `context.route` interception rather than an OS-level kernel firewall namespace. Arbitrary public-facing live crawl remains gated in development mode.
2. **Untrusted Data Boundaries:**
   All web page text, DOM contents, and screenshot images are treated strictly as untrusted data inputs. Website contents cannot inject system-level instructions into the agent.
