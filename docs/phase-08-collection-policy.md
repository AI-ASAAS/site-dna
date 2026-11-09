# Site DNA — Phase 08 Collection Policy & Multi-Site Crawling Protocol

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 08 — Competitor Intelligence  

---

## 1. Multi-Site Crawl Budgets & Limits

To prevent resource exhaustion, avoid rate-limiting, and respect target web properties, Phase 08 enforces strict collection limits:

1. **Competitor Count**: Mode A default supports 1 primary website and 1–3 competitors (maximum hard ceiling: 5 sites total).
2. **Page Budget per Site**: Default 5 pages per site (home, pricing, features/solutions, about, contact/support).
3. **Total Page Cap per Run**: Hard ceiling of 25 pages across all compared sites.
4. **Timeout**: Maximum 30 seconds per page load, 120 seconds total crawl budget per competitor domain.

---

## 2. Page Priority Strategy

The collection coordinator prioritizes pages using targeted path scoring:
- **Priority 1 (Weight 100)**: Home / Landing (`/`, `/index.html`)
- **Priority 2 (Weight 90)**: Pricing & Plans (`/pricing`, `/plans`, `/أسعار`)
- **Priority 3 (Weight 80)**: Product & Features (`/features`, `/product`, `/solutions`, `/المميزات`)
- **Priority 4 (Weight 70)**: About & Company (`/about`, `/company`, `/عنا`, `/من-نحن`)
- **Priority 5 (Weight 60)**: Customers / Trust (`/customers`, `/reviews`, `/case-studies`)

Non-essential utility pages (terms, privacy policy, login, register, password resets) are deprioritized during competitor benchmarking.

---

## 3. Provenance & Scope Disclosure

Because crawler coverage is bounded to a finite sample of pages:
- Any feature not observed in the collected corpus is strictly marked as `not_found_in_sample` or `observed_absent_in_inspected_scope`.
- The engine NEVER claims a competitor completely lacks a capability across their entire company portfolio without explicit evidence; reports clearly note the inspected scope.
