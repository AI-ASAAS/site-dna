# Site DNA — Phase 03 Security Architecture
## Browser Isolation, Egress Filtering & SSRF Prevention

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Project:** Site DNA  
**Phase:** 03 — Visual & Evidence Collection  
**Status:** Validated  

---

## 1. Security Philosophy & Threat Model

In Phase 03, Site DNA launches real headless Chromium browser processes to render external web pages. Untrusted web content can present substantial security risks:
- **Server-Side Request Forgery (SSRF):** Malicious pages attempting to make the browser query local services (`127.0.0.1`, `localhost`), internal VPC networks (`10.0.0.0/8`, `192.168.0.0/16`), or cloud metadata endpoints (`169.254.169.254`).
- **Local File Exfiltration:** Malicious pages embedding `file://` resources or attempting to read server disk paths.
- **Resource Exhaustion & Denial of Service:** Pages with infinite loops, infinite scrolling, or massive image canvas elements designed to crash browser memory.
- **Credential & PII Scraping:** Scripts reading form inputs or storing private user data in extracted DOM structures.
- **Persistent Channel Hijacking:** WebSockets (`ws://`, `wss://`) or Server-Sent Events holding connections open to internal systems.

Site DNA treats **all external web content as untrusted input data, never as executable code or administrative instructions**.

---

## 2. Browser Process Isolation

### 2.1 Chromium Sandbox Preservation
- The Chromium operating system sandbox is **strictly retained**.
- The flag `--no-sandbox` is **strictly prohibited** in all production and test environments.
- Chromium runs as a sandboxed subprocess with minimal privileges.

### 2.2 Hardened Chromium Flags
The browser is launched with process-level isolation arguments:
- `--disable-dev-shm-usage`: Prevents shared memory exhaustion on containerized and virtualized hosts.
- `--disable-extensions`: Disables all browser extension loading and execution.
- `--disable-background-networking`: Disables background update checks, metrics reporting, and unsolicited connections.
- `--disable-sync`: Disables account synchronization.
- `--no-first-run`: Skips initial configuration workflows.
- `--mute-audio`: Prevents audio hardware allocation.

---

## 3. Network Egress Filtering & SSRF Prevention

All network traffic initiated by the browser (including navigations, iframes, stylesheets, scripts, images, and fonts) is intercepted by `BrowserSecurityPolicy` using Playwright's `context.route("**/*")`.

### 3.1 Prohibited Schemes
- Disallows `file:`, `ftp:`, `javascript:`, `chrome:`, `view-source:`, and any custom protocol.
- Only allows:
  - `http:` and `https:` (subject to strict IP and hostname validation)
  - `data:`, `blob:`, `about:blank` (non-network resources)

### 3.2 WebSocket and Streaming Blocking
- Resource types `websocket` and `eventsource` are immediately aborted with code `blockedbyclient`.
- Prevents bi-directional socket tunnels or streaming backdoors.

### 3.3 Hostname & Cloud Metadata Defense
- Requests to known cloud metadata endpoints are immediately aborted with code `accessdenied`:
  - `169.254.169.254` (AWS, GCP, Azure, OpenStack)
  - `100.100.100.200` (Alibaba Cloud)
  - `metadata.google.internal` (GCP)
  - `*.internal` (Private cloud domains)

### 3.4 IP Address Validation & Private Network Blocking
- For every hostname in an HTTP/HTTPS request, DNS resolution is performed via `resolve_and_validate_host`.
- Every resolved IPv4 and IPv6 address is checked against `is_ip_forbidden`:
  - Loopback (`127.0.0.0/8`, `::1`)
  - Private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Link-local and multicast ranges
  - IPv4-mapped IPv6 representations (`::ffff:127.0.0.1`, `::ffff:169.254.169.254`)
- If any resolved IP belongs to a forbidden range, the request is aborted immediately with `accessdenied`.

---

## 4. DOM and Data Extraction Sanitization

- **No Form Input Values:** The DOM extraction script filters attributes through an explicit allow-list (`['href', 'src', 'alt', 'role', 'type', 'dir', 'lang', 'target', 'action', 'method', 'aria-label']`). Attributes like `value`, `name`, `password`, `token`, and `cookie` are never collected.
- **Dialog Auto-Dismissal:** All browser dialogs (`window.alert`, `window.confirm`, `window.prompt`) are trapped and dismissed automatically (`dialog.dismiss()`) to avoid script blocking.
- **Maximum Height Ceiling:** Full-page screenshots enforce a strict upper bound (`visual_max_page_height_px = 12000px`). Pages exceeding this limit are skipped or constrained to avoid memory overflow.
- **Path Traversal Protection:**
  - Page IDs are sanitized via `re.sub(r"[^a-zA-Z0-9_-]", "_", safe_page_id)`.
  - Storage paths strictly verify containment within the run's `pages/` directory.

---

## 5. API Access Security

The visual capture endpoint (`POST /api/v1/visual/capture`) is protected by a three-gate security check:
1. **Enabled Flag (`visual_api_enabled`):** Default `False`. Disabled endpoints return HTTP 403 Forbidden.
2. **Loopback Gate in Development:** Rejects any non-loopback requests (`127.0.0.1`, `localhost`, `testclient`) when `app_env=development`.
3. **Bearer Token Authentication:** If `visual_api_token` is configured, requests without a matching `Authorization: Bearer <token>` header receive HTTP 401 Unauthorized.
