# Site DNA — Phase 08 Scoring Rubric & Benchmark Dimensions

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 08 — Competitor Intelligence  

---

## 1. Six-Dimension Scoring Model

The competitor intelligence scoring engine computes scores across 6 core strategic dimensions (0–100 scale):

| Dimension ID | Dimension Name (EN) | Dimension Name (AR) | Weight | Core Focus |
|---|---|---|---|---|
| `feature_completeness` | Feature Completeness | شمولية المزايا والوظائف | 25% | Observed core and secondary feature presence vs competitor benchmark |
| `ux_visual_parity` | UX & Visual Parity | تكافؤ التجربة والهوية البصرية | 20% | Navigation clarity, responsive layout, aesthetic polish, and design tokens |
| `positioning_differentiation` | Positioning Differentiation | وضوح التموضع والتمايز | 20% | Core value proposition clarity, USP articulation, and target persona focus |
| `pricing_transparency` | Pricing Transparency | شفافية التسعير والخطط | 15% | Clear tiers, transparent billing intervals, and friction-free purchase paths |
| `technical_baseline` | Technical Baseline | الأساس التقني والأداء | 10% | Core Web Vitals, mobile readiness, crawlability, and security headers |
| `strategic_defensibility` | Strategic Defensibility | الحصانة الاستراتيجية والثقة | 10% | Social proof, enterprise certifications, integrations, and brand authority |

---

## 2. Guardrails & Score Withholding

- **Exploratory / Non-Direct Guardrail**: If all compared competitor websites are classified as `indirect`, `adjacent`, or `not_comparable`, the aggregate `overall_score` is intentionally withheld (`None`) to prevent misleading scores, while individual dimension scores remain accessible for directional analysis.
- **Evidence Threshold**: Individual dimensions require at least one verified evidence item to compute a score; unassessed dimensions default to `None` rather than assuming a failing score.
