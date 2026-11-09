# Site DNA — Phase 10: Methodology & WCAG-EM 2.0 Evaluation Framework

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Engine:** Site DNA Accessibility Engine  
**Methodology:** W3C WCAG-EM 2.0 (Website Accessibility Conformance Evaluation Methodology)  

---

## 1. Five-Step Evaluation Lifecycle

Site DNA adapts the international WCAG-EM standard for automated and AI-assisted workflows:

### Step 1: Define Evaluation Scope
- Identifies the target website, root domain, and previous crawl run ID.
- Targets W3C WCAG 2.2, Levels A and AA conformance criteria.
- Defines baseline user agent environment (modern desktop and responsive mobile viewports).

### Step 2: Explore Target Environment
- Reuses raw crawl metadata, status codes, HTML trees, and screenshot artifacts from Phase 01–03.
- Catalogs unique URL patterns, template families, dynamic interactions, and interactive widgets.

### Step 3: Select Representative Page Sample (WCAG-EM Section 3)
The engine automatically extracts up to 8 representative pages using stratified sampling:
1. **Primary Landing / Home Page:** Global navigation, branding, main footer.
2. **Contact / Feedback Page:** Form controls, input validation, labels.
3. **Product / Service / Detail Page:** Rich content, images, headings, pricing tables.
4. **Authentication / Account Page:** Login forms, password fields, security elements.
5. **Dynamic / Interactive View:** Modals, carousels, tabs, or menus.
6. **Error / 404 State:** Error handling, search fallbacks, navigation recovery.
7. **Legal / Policy Page:** Long-form typography, disclosure tables.
8. **Supplementary High-Traffic Page:** Randomly selected content node.

### Step 4: Deterministic Audit & Multi-Heuristic Rules
- Executes 17 specialized analyzers in parallel over the representative sample.
- Evaluates 25+ automated WCAG 2.2 criteria.
- Verifies contrast ratios using relative luminance math (`(L1 + 0.05) / (L2 + 0.05)`).
- Maps all findings into explicit severity tiers (`critical`, `serious`, `moderate`, `minor`).

### Step 5: Manual Review Generation & Synthesis
- Segregates checks that require human cognitive judgment into structured `manual_review_tasks`.
- Examples: Alternative text contextual accuracy (1.1.1), audio captions (1.2.2), cognitive load and instructions clarity (3.3.2).
- CrewAI agent synthesizes the executive summary and remediation roadmap using `gemini/gemini-3.6-flash`.
