# Site DNA — Phase 05 UX/UI Scoring Rubric & Evaluation Framework

## 1. Rubric Architecture Overview

The Site DNA UX/UI Scoring Rubric evaluates websites across **6 distinct dimensions** with a total normalized weight of 100%. Every deduction is directly tied to validated evidentiary findings.

```
Total Score = ∑ (Dimension Score × Dimension Weight) / ∑ (Active Weights)
```

| Dimension | Default Weight | Key Focus Areas |
|---|:---:|---|
| **1. Navigation & Information Architecture** | 20% | Navigation depth, orphan pages, ambiguous anchor texts, duplicate labels |
| **2. Interactive Controls & CTA Clarity** | 20% | Primary CTA salience, standalone click targets (≥ 24×24px), unlabeled controls |
| **3. Mobile Experience & Responsiveness** | 20% | Horizontal overflow, mobile menu collapse, touch targets (≥ 44×44px / 48×48px) |
| **4. Basic Accessibility (WCAG AA)** | 15% | Heading hierarchy (H1-H6), image alt attributes, icon button labels, contrast |
| **5. Content Usability & Arabic RTL** | 15% | RTL declaration (`dir="rtl"`), scanability index, paragraph lengths |
| **6. Forms Usability & Task Support** | 10% | Input field labels, placeholder-only fields, submit buttons, zero-forms neutrality |

---

## 2. Dimension Scoring Rules & Deductions

### Dimension 1: Navigation & Information Architecture (Weight: 20%)
- **Base Score:** 100
- **Deductions:**
  - Orphan pages detected: -15 pts per orphan page (max -30 pts).
  - Excessive navigation depth (> 3 clicks from seed): -10 pts.
  - Ambiguous link texts (`اضغط هنا`, `click here`, `more`): -5 pts per instance (max -20 pts).
  - Duplicate destination labels with conflicting targets: -5 pts per instance.
- **Floor:** 0

### Dimension 2: Interactive Controls & CTA Clarity (Weight: 20%)
- **Base Score:** 100
- **Deductions:**
  - Absence of a clear primary CTA on key conversion pages: -20 pts.
  - Interactive targets below WCAG 2.2 min ($< 24\times 24$ px): -5 pts per element (max -30 pts).
  - Unlabeled interactive controls (missing accessible name): -5 pts per element (max -20 pts).
  - Confusing or clustered button affordances: -10 pts.
- **Floor:** 0

### Dimension 3: Mobile Experience & Responsiveness (Weight: 20%)
- **Base Score:** 100
- **Deductions:**
  - Unintended horizontal overflow (viewport scroll): -30 pts.
  - Clipped or obscured elements on mobile viewport: -10 pts per instance (max -25 pts).
  - Touch targets below mobile ergonomic target ($< 48\times 48$ px): -3 pts per target (max -25 pts).
  - Failure to collapse navigation into mobile menu: -20 pts.
- **Floor:** 0

### Dimension 4: Basic Accessibility (WCAG AA) (Weight: 15%)
- **Base Score:** 100
- **Deductions:**
  - Heading hierarchy skips (e.g. H1 directly to H3): -10 pts per level skip (max -25 pts).
  - Images missing `alt` attributes: -5 pts per image (max -25 pts).
  - Icon-only buttons lacking accessible names / ARIA: -5 pts per button (max -20 pts).
  - Insufficient text contrast against background: -5 pts per occurrence (max -20 pts).
- **Floor:** 0

### Dimension 5: Content Usability & Arabic RTL (Weight: 15%)
- **Base Score:** 100
- **Deductions:**
  - Arabic content present without `dir="rtl"` declaration: -30 pts.
  - Unbroken "wall of text" paragraphs (> 100 words without breaks): -10 pts per paragraph (max -30 pts).
  - Poor scanability index (< 50/100): -15 pts.
  - Content density mismatch or cluttered text layout: -10 pts.
- **Floor:** 0

### Dimension 6: Forms Usability & Task Support (Weight: 10%)
- **Base Score:** 100 (when forms exist)
- **Zero-Forms Neutral Mode:**
  - When a crawled website has 0 forms (e.g. static informational, landing, or documentation site), Dimension 6 is marked `status = "not_assessed"` and assigned a weight of 0%.
  - The remaining 5 dimensions are re-normalized to 100% total weight:
    $$\text{Total Score} = \frac{\sum_{i \in \text{active}} \text{Score}_i \times \text{Weight}_i}{\sum_{i \in \text{active}} \text{Weight}_i}$$
  - **Zero penalty** is assessed for absent forms on informational websites.
- **Deductions (when forms exist):**
  - Form fields missing explicit `<label>` tags: -10 pts per field (max -30 pts).
  - Form fields relying solely on `placeholder` as label: -5 pts per field (max -20 pts).
  - Missing or disabled primary submit button: -25 pts.
  - Missing field-level error prevention hints: -10 pts.
- **Floor:** 0

---

## 3. Severity & Priority Mapping

Findings are classified into 4 severity levels and automatically mapped to actionable recommendation priorities:

| Severity | Description | Recommendation Priority | Target Resolution SLA |
|---|---|:---:|---|
| **CRITICAL** | Severe usability blocker (e.g. horizontal scroll on mobile, broken form submission, missing dir="rtl" on Arabic site) | **P1** | Immediate |
| **HIGH** | Major friction (e.g. missing primary CTA, orphan core page, touch targets < 24px) | **P1** | High |
| **MEDIUM** | Noticeable usability degradation (e.g. ambiguous links, touch targets < 48px, heading skips) | **P2** | Normal |
| **LOW** | Minor polish or aesthetic suggestion (e.g. paragraph length optimization, minor spacing) | **P3** | Low |
