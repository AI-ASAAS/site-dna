# Site DNA — Phase 08 Operational Limitations & Scope Boundaries

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 08 — Competitor Intelligence Limitations  

---

## 1. Scope & Crawl Depth Boundaries

1. **Finite Page Sample**: Crawling is capped at 5 pages per competitor website. Features present behind user authentication, in subdomains, or deep in product documentation may not be observed in the collected sample.
2. **Dynamic / Single Page Applications**: Highly dynamic SPAs requiring complex authenticated multi-step user workflows may only expose public marketing text during automated crawls.
3. **Paywalls & Geoblocking**: Competitor content behind paywalls, CAPTCHAs, or region-specific geolocation blocks may restrict extraction to public fallback meta tags.

---

## 2. Pricing Comparison Nuances

1. **Unpublished / Contact Sales**: Many enterprise B2B SaaS platforms do not publish numerical pricing. These are explicitly recorded as `contact_sales` or `not_published` and are never coerced into arbitrary numerical estimates.
2. **Currency Fluctuations**: Differing currencies (USD vs SAR vs EUR) are flagged as non-comparable unless explicit live FX normalization is configured.
3. **Packaging Heterogeneity**: Seat-based vs usage-based vs flat-rate pricing structures represent distinct economic models and are marked with comparability caveats.

---

## 3. Boundary with Future Phases (Phases 09–12)

Phase 08 focuses strictly on **direct competitor benchmarking and empirical observation**.
- **Phase 09 (Market Positioning)**: Macro-market trends and whitespace market positioning remain planned and disabled.
- **Phase 10 (Conversion Rate Optimization)**: Deep funnel micro-copy A/B testing remains planned and disabled.
- **Phase 11 (Security & Compliance)**: Deep regulatory compliance audits remain planned and disabled.
- **Phase 12 (Executive Synthesis)**: Cross-agent holistic multi-quarter business roadmaps remain planned and disabled.
