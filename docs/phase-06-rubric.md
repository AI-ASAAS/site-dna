# Site DNA — Phase 06: Content & Marketing Evaluation Rubric

**Project:** Site DNA — بصمة الموقع  
**Subsystem:** Content & Marketing Intelligence Scoring Engine  
**Version:** 1.0.0  

---

## 1. Overview & Principles

The Site DNA Content & Marketing scoring rubric evaluates website communication effectiveness across 7 distinct dimensions. Each dimension starts at a base score of 100 points, from which deductions are made based on verified findings and their severity levels.

```
Total Score = Sum(Dimension_Score * Weight)
```

The scoring engine is strictly **explainable**: every point deduction is traceable to a specific finding backed by observed DOM evidence.

---

## 2. Dimension Weights & Distribution

| Dimension Key | Dimension Title (Arabic) | Weight | Base Score |
|---|---|:---:|:---:|
| `value_proposition` | وضوح القيمة المقترحة (Value Proposition Clarity) | **20%** | 100.0 |
| `messaging_clarity` | وضوح ودقة الرسائل التسويقية (Messaging Clarity & Specificity) | **20%** | 100.0 |
| `service_content` | اكتمال شرح الخدمات والمنتجات (Product/Service Explanation) | **15%** | 100.0 |
| `cta_action` | وضوح عبارات اتخاذ الإجراء (CTA Copy & Action Clarity) | **15%** | 100.0 |
| `trust_claims` | الشفافية والمصداقية والادعاءات (Trust & Claim Transparency) | **10%** | 100.0 |
| `brand_voice` | نبرة الصوت واتساق الهوية (Brand Voice & Consistency) | **10%** | 100.0 |
| `audience_alignment` | ملاءمة المحتوى للجمهور المستهدف (Audience & Purpose Alignment) | **10%** | 100.0 |
| **Total** | — | **100%** | **100.0** |

---

## 3. Severity Deduction Scale

When a finding is identified within a dimension, points are deducted according to severity:

| Finding Severity | Point Deduction | Description & Impact |
|---|:---:|---|
| `critical` | **-25 points** | Fundamental communication failure (e.g. completely empty homepage, broken value proposition, deceptive claims). |
| `high` | **-15 points** | Major friction (e.g. generic greeting H1, missing primary CTA, unexplained service offering). |
| `medium` | **-8 points** | Noticeable weakness (e.g. excessive buzzwords, unverified absolute claims, missing contact info). |
| `low` | **-3 points** | Minor polish issue (e.g. generic secondary CTA, slight tone variance). |
| `info` | **0 points** | Informational observation with no negative scoring impact. |

*Floor Guarantee:* A dimension score cannot drop below **0.0**, and cannot exceed **100.0**.

---

## 4. Handling Neutral & Unassessed Dimensions

To ensure fair scoring across diverse website types (e.g., personal blogs, single-page landing pages, documentation portals):

1. **Missing Service Pages (`service_content`):**
   - If a website does not offer commercial products or services, the `service_content` dimension is marked `neutral` and assigned a default score of `100.0` with explanation: *"لم تُكتشف صفحات خدمات أو منتجات مستقلة (Neutral Evaluation)"*.
2. **Single-Page Websites (`consistency_analyzer`):**
   - Cross-page tone consistency is marked `not_assessed` and does not penalize single-page websites.

---

## 5. Score Interpretation Bands

| Score Range | Communication Health Band | Strategic Interpretation |
|:---:|---|---|
| **90.0 — 100.0** | **ممتاز (Excellent)** | الرسائل واضحة ومقنعة، القيمة المقترحة محددة بدقة، عبارات الإجراء محددة، والادعاءات موثقة. |
| **75.0 — 89.9** | **جيد جداً (Good)** | تواصل فعال مع بعض الفجوات الطفيفة في شرح الخدمات أو عبارات الحث الثانوية. |
| **60.0 — 74.9** | **متوسط (Moderate)** | وجود غموض في العنوان الرئيسي أو تكرار لعبارات عامة مبهمة، بحاجة إلى إعادة هيكلة الـ CTAs. |
| **40.0 — 59.9** | **ضعيف (Weak)** | صعوبة في فهم طبيعة النشاط، غياب الـ CTA الرئيسي، ادعاءات غير مدعومة تضعف الثقة. |
| **0.0 — 39.9** | **حرج (Critical)** | انعدام القيمة المقترحة، محتوى مبهم أو مضلل، غياب شبه كامل لمعلومات التواصل والخدمات. |
