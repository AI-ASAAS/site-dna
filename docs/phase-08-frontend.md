# Site DNA — Phase 08 Frontend Integration & UI Components

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 08 — Competitor Intelligence UI  

---

## 1. Visual Design & Asaas Kit Compliance

The frontend integration strictly adheres to the Asaas visual kit:
- **Design Tokens**: Warm sand background (`#fcfbf9` / `#161412`), gold accents (`#c5a880`), dark ink text (`#1a1815` / `#f0eee6`), and liquid glass card styling (`glass-card` with 12px blur, subtle border).
- **Typography**: Thmanyah font family across headings and UI text with native Arabic RTL support.
- **Responsive Layout**: Zero horizontal overflow, fluid grid systems, mobile-adaptive navigation.

---

## 2. Integrated Views & Pages

1. **`NewAnalysis.tsx`**:
   - `competitor_intelligence` moved to active available stages.
   - Dynamic competitor URL input fields (1–3 URLs with add/remove buttons, placeholder examples, and validation).
   - Automatically attaches `competitor_urls` to submission payload.

2. **`Dashboard.tsx`**:
   - Platform readiness cards updated to reflect Phases 01–08 active (`status === 'ready'`).
   - Phase 08 agent card prominently displayed as "جاهز للتشغيل" with green status indicator.
   - Subtitle clearly announces "المراحل 01–08 جاهزة للتشغيل الكامل • المراحل 09–12 مهيأة معمارياً ومخطط إطلاقها".

3. **`CompetitorIntelligenceView.tsx`**:
   - **Executive Header**: Benchmark score card, site counts, relevance categories, and date.
   - **Company Profiles**: Side-by-side comparative cards with business summaries, target audiences, and primary offerings.
   - **Searchable Feature Parity Matrix**: Interactive filterable matrix displaying provenance badges (`observed_present`, `observed_absent_in_inspected_scope`, `claimed`, `not_found_in_sample`).
   - **Pricing Comparison**: Tiers, currencies, billing intervals, and explicit non-comparability safeguards for unstandardized plans.
   - **Positioning & Messaging**: Value propositions, tones of voice, and main CTA strategies side by side.
   - **Strategic Gaps & Opportunities**: Prioritized P1, P2, P3 cards with estimated impact, effort, and validation requirements.
   - **6-Dimension Score Breakdown**: Visual progress bars and radar representation for the 6 core dimensions.

4. **`AnalysisMonitor.tsx`**:
   - Competitor tab conditionally appears when `stages.competitor_intelligence` is part of the run.
   - Direct tab navigation between Overview, Visual, UX, Content, Technical SEO, and Competitor Intelligence.
