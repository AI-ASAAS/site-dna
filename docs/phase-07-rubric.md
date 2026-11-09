# Site DNA — Phase 07: Technical SEO & Website Performance Scoring Rubric

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**System:** Site DNA  
**Phase:** 07 — Technical SEO & Website Performance Intelligence

---

## 1. Overview & Mathematical Formulation

The Site DNA Technical SEO scoring engine uses a deterministic, explainable 6-dimension evaluation model totaling **100%**.

$$\text{Overall Score} = \sum_{i=1}^{6} (S_i \times W_i)$$

Where $S_i \in [0, 100]$ is the raw dimension score and $W_i$ is the dimension weight.

---

## 2. Six-Dimension Rubric Breakdown

| Dimension Index | Dimension Name (Arabic / English) | Weight ($W_i$) | Core Evaluated Signals |
|---|---|---|---|
| **D1** | **إمكانية الزحف والاكتشاف الداخلي**<br>(Crawlability & Internal Discovery) | **20%** | Robots.txt availability, disallow rules, broken internal links (4xx/5xx), sitemap presence and validity, crawl depth $> 4$. |
| **D2** | **إشارات الفهرسة والروابط المعيارية**<br>(Indexability & Canonical Signals) | **20%** | `noindex` directives, `X-Robots-Tag`, canonical tag presence, self-referencing vs cross-page, canonical conflicts (pointing to noindex or 404). |
| **D3** | **البيانات الوصفية للرأس**<br>(Technical Metadata) | **15%** | HTML `<title>` presence and length (optimal 60-70 chars), meta description presence, duplicate titles across pages, HTML `lang` attribute. |
| **D4** | **البيانات المنظمة والمخططات**<br>(Structured Data & Schema.org) | **10%** | JSON-LD syntax validity, presence of recognized `@type`, completeness of required Google Rich Result properties (e.g. `Organization`, `Article`, `Product`). |
| **D5** | **SEO الجوال وتصيير جافاسكربت**<br>(Mobile & JavaScript SEO) | **15%** | Viewport meta configuration (`width=device-width`), horizontal overflow detection, parity between server-rendered HTML and client-rendered DOM (CSR content gap). |
| **D6** | **الأداء وسرعة التحميل**<br>(Performance & Core Web Vitals) | **20%** | Laboratory Largest Contentful Paint (LCP), Cumulative Layout Shift (CLS), resource payload bounds, server status codes. |

---

## 3. Explicit Deduction & Penalty Rules

### D1: Crawlability & Internal Discovery (Base: 100)
- Missing `robots.txt`: **-5 pts**
- Missing XML sitemap: **-6 pts**
- Broken internal links found: **-15 pts per link** (capped at 40 pts)
- Crawl depth $> 4$: **-5 pts**

### D2: Indexability & Canonical Signals (Base: 100)
- Missing `<link rel="canonical">`: **-3 pts per page** (capped at 15 pts)
- Conflicting canonical (pointing to 4xx or `noindex` page): **-10 pts**
- Canonical pointing to external domain (without explicit annotation): **-5 pts**

### D3: Technical Metadata (Base: 100)
- Missing `<title>`: **-15 pts per page**
- Title exceeds 70 characters: **-3 pts per page**
- Duplicate titles across crawled pages: **-8 pts**
- Missing `<meta name="description">`: **-3 pts per page**
- Missing `html lang` attribute: **-3 pts per page**

### D4: Structured Data (Base: 100)
- JSON-LD syntax error (invalid JSON string): **-25 pts**
- Missing `@type` field in structured object: **-10 pts**
- Missing required Google Rich Result properties: **-5 pts per incomplete schema**
- *Note:* If no structured data is present on the site, D4 receives a neutral baseline of 100 with an advisory finding rather than severe structural penalization.

### D5: Mobile & JavaScript SEO (Base: 100)
- Missing `<meta name="viewport">`: **-30 pts**
- Improper viewport configuration: **-15 pts**
- Horizontal overflow detected: **-15 pts**
- Critical content rendered purely by client-side JS (CSR): **-8 pts**

### D6: Performance & Core Web Vitals (Base: 100)
- Simulated LCP $> 4000\text{ ms}$ (Poor): **-25 pts**
- Simulated LCP between $2500\text{ ms}$ and $4000\text{ ms}$ (Needs Improvement): **-15 pts**
- Measured CLS $> 0.25$ (Poor): **-20 pts**
- Measured CLS between $0.10$ and $0.25$ (Needs Improvement): **-10 pts**
- Server HTTP 5xx errors: **-40 pts**

---

## 4. Overall Score Bands & Interpretation

- **90.0 – 100.0 (Excellent / ممتاز):** Production-ready technical foundation; fully accessible to search engine crawlers with clean canonical signals and fast response times.
- **75.0 – 89.9 (Good / جيد):** Solid foundation with minor non-blocking issues (e.g. meta description lengths or missing XML sitemap declarations).
- **50.0 – 74.9 (Needs Improvement / يحتاج تحسين):** Substantial technical impediments (such as missing canonicals, viewport configuration flaws, or slow LCP).
- **0.0 – 49.9 (Critical Failure / حرج):** Severe architectural failures (broken internal links, redirect loops, unparsable JSON-LD, or client-only rendering without SSR).
