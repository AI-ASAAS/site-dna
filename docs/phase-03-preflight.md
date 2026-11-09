# Site DNA — Phase 03 Pre-flight Investigation & Verification
## H1 Extraction Diagnosis & Multi-Page Crawl Validation

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Project:** Site DNA  
**Phase:** 03 Pre-flight Verification  
**Date:** November 2026  
**Status:** Completed & Validated (PASS)  

---

## 1. Pre-flight Task A: H1 Extraction Investigation

### 1.1 Reported Anomaly
In the Phase 02 live validation report for `https://example.com`, the summary recorded:
```text
Title: Example Domain | Words: 25 | Headings: 0
```
This required investigation to determine whether:
1. Headings were not extracted by `extractor.py`.
2. Headings were extracted but lost during Pydantic serialization or JSON persistence.
3. The CLI incorrectly rendered the heading count.
4. The live HTML served by `https://example.com` differed from the historical Example Domain page.

### 1.2 Investigation & Root Cause Discovery
We inspected `src/site_dna/discovery/extractor.py` and directly analyzed the raw HTML retrieved from `https://example.com` during the crawl:

```html
<!doctype html>
<html lang=en>
<head>
  <meta charset=utf-8>
  <link rel=icon href=data:,>
  <meta name=viewport content="width=device-width,initial-scale=1">
  <title>Example Domain</title>
  <style>html{color-scheme:light dark;...}</style>
</head>
<body>
  <p>This domain is for use in documentation examples without needing permission. This is not a service; avoid relying on it for testing and monitoring purposes.</p>
  <script src=/s.js></script>
</body>
</html>
```

**Key Finding:**
The modern live page hosted at `https://example.com` (managed by IANA/RFC-Editor) contains **no `<h1>` tag whatsoever**. It consists solely of a `<title>` tag and a single `<p>` paragraph.

### 1.3 Offline Regression Test
To prove that `extractor.py`, `PageData`, and Pydantic serialization faithfully extract and preserve heading hierarchies when headings exist, we implemented `tests/unit/test_heading_regression.py` using `tests/fixtures/discovery/heading_test.html`:

```html
<!doctype html>
<html lang="en">
<head><title>Example Domain</title></head>
<body>
  <main>
    <h1>Example Domain</h1>
    <h2>About This Website</h2>
    <h3>Additional Information</h3>
    <p>This is a test page.</p>
  </main>
</body>
</html>
```

The test asserts:
- `H1: Example Domain` (level=1)
- `H2: About This Website` (level=2)
- `H3: Additional Information` (level=3)
- Preserves document hierarchy order.
- Pydantic `PageData.model_dump_json()` serialization and deserialization retains `headings` with count 3.

**Result:** `tests/unit/test_heading_regression.py` **PASSED** in 0.05s.

---

## 2. Pre-flight Task B: Multi-Page Crawl Verification

### 2.1 Multi-Page Test Fixture Suite
We constructed a controlled, realistic multi-page test fixture in `tests/fixtures/discovery/multipage/`:
- `home.html` (Index page in English with navigation, hero section, duplicate links, and an external partner link).
- `about.html` (Arabic RTL page: "من نحن" with company history and team image).
- `services.html` (English service solutions page).
- `products.html` (English products page).
- `contact.html` (Arabic contact page with contact form, email/phone, and submit button).
- `/old-contact` (HTTP 301 internal redirect resolving to `/contact`).

### 2.2 Controlled Mock Transport & Assertion Strategy
In `tests/unit/test_multipage_crawl.py`, we wired an isolated `httpx.MockTransport` and verified:
1. **Multi-page Discovery:** Total crawled pages $\ge 5$ across the canonical origin.
2. **Frontier Priority Scoring:** High-priority strategic pages (Home: 100, Contact: 90, About: 85, Services: 80, Products: 75) are prioritized.
3. **Scope Enclosure:** The external link `https://external-partner.org/info` was strictly excluded from the crawl scope.
4. **Duplicate Removal:** Duplicate internal link `/about` was visited only once.
5. **Redirect Handling:** Internal 301 redirect `/old-contact` cleanly followed and attributed to `/contact`.
6. **Form Safety:** The contact form at `/contact` was extracted structurally but **never submitted** (HTTP POST to `/api/contact-submit` remained uncalled).
7. **Bilingual Extraction:** Extracted both English (`Welcome to Acme Global`) and Arabic (`عن الشركة ورؤيتنا المستقبلية`) titles and headings.
8. **Plain Text Fix:** Added `allow_plain_text=True` to `SecureHttpClient.fetch` for `robots.txt` (`text/plain`), ensuring robots.txt is parsed without MIME-type rejection.

**Result:** `tests/unit/test_multipage_crawl.py` **PASSED** in 0.07s.
