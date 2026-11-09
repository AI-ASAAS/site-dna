# Site DNA — Phase 05 Scope, Boundaries & Technical Limitations

## 1. System Scope & Boundaries

Site DNA Phase 05 provides automated, evidence-grounded usability intelligence. Understanding its intended boundaries is essential for proper operational use.

---

## 2. Technical Boundaries

### 1. Static vs. Dynamic State Auditing
- **Audited Scope:** The system evaluates pages as rendered during Phase 03's headless browser capture (desktop at 1920×1080 and mobile at 390×844).
- **Limitation:** Complex multi-step dynamic workflows that require multi-stage user credentials (e.g. 2FA authentication, multi-page checkout wizards, or dynamic canvas applications) are analyzed only up to their initial public state.

### 2. Automated vs. Human Usability Testing
- **Audited Scope:** Deterministic heuristics, structural standards, and visual perception using Gemini 3.6 Flash.
- **Limitation:** Automated auditing cannot replace qualitative user testing with real human participants (e.g., emotional affinity, comprehension testing of complex copy, or qualitative user preferences).

### 3. Automated WCAG Accessibility Coverage
- **Audited Scope:** Machine-verifiable WCAG 2.1/2.2 AA rules:
  - Heading hierarchy linearity (H1 $\rightarrow$ H2 $\rightarrow$ H3).
  - Presence of non-empty `alt` attributes on `<img>` tags.
  - Presence of accessible names (`aria-label`, button text) on interactive controls.
  - High-level text and background contrast indicators.
- **Limitation:** Full WCAG AA/AAA certification requires assistive technology user trials (e.g., screen reader traversal with JAWS/NVDA, manual switch control evaluation, cognitive accessibility reviews).

### 4. Zero-Forms Neutrality
- **Behavior:** The engine detects whether a site contains forms. If no forms are present (common for informational, media, or single-page sites), the Forms dimension is excluded from weighting rather than penalized.
- **Limitation:** The engine cannot know whether a site *should* have had a contact form if one was never designed or linked.

### 5. Single Viewport Profile Pair
- **Audited Scope:** Desktop (1920×1080) and Mobile (390×844).
- **Limitation:** Intermediate viewports (tablets 768×1024, ultra-wide 3840×2160) are not rendered unless explicitly configured in Phase 03 visual capture requests.
