# Site DNA — Phase 10: Limitations & Operational Boundaries

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Engine:** Site DNA Accessibility Engine  

---

## 1. Automated vs. Human Assessment Boundaries

In alignment with international accessibility engineering best practices:
- **Coverage Horizon:** Fully automated heuristics can reliably detect approximately 30% to 40% of potential WCAG barriers (e.g., contrast calculations, missing labels, missing `alt` attributes, zoom disablement in viewport).
- **Cognitive & Semantic Horizon:** The remaining 60% to 70% requires subjective human review (e.g., whether an alternative text accurately conveys the artistic emotion of an image, whether error messages are clear and helpful, whether sequential tasks cause cognitive fatigue).
- **Explicit Classification:** Site DNA explicitly categorizes all findings into 5 verified statuses:
  1. `confirmed_failure` (Deterministic violation confirmed by DOM/CSS math).
  2. `passed_specific_check` (Passed the specific automated rule evaluated).
  3. `potential_issue` (Heuristic indicator detected; requires contextual verification).
  4. `manual_review_required` (Cannot be decided without human evaluation; task generated).
  5. `not_assessed` / `not_applicable` (Feature or element absent from audited sample).

---

## 2. Regulatory & Legal Non-Certification Disclaimer

> **تنبيه قانوني وتنظيمي:**  
> يُعد هذا التدقيق تقييماً استشارياً وتقنياً مبنياً على أدلة برمجية وبصرية مستخرجة آلياً، ولا يُعتبر شهادة مطابقة قانونية رسمية أو ترخيصاً بالامتثال لمعايير إمكانية الوصول في أي اختصاص قضائي محلي أو دولي. يجب استكمال هذه النتائج بمراجعة واختبار يدوي مع مستخدمين ذوي إعاقة وباستخدام التقنيات المساعدة المعتمدة.
