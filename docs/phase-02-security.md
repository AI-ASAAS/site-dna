# Site DNA — Phase 02 Security Architecture & Hardening
## SSRF Prevention, DNS Rebinding Defenses & XML Security

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Document:** Security Specification  
**Version:** 0.1.0 (Phase 02)  

---

## 1. Threat Model & Security Posture

As a website intelligence and crawling platform, Site DNA accepts arbitrary public URLs from users or external systems. This exposes the crawler to critical network attacks if unmitigated:

1. **Server-Side Request Forgery (SSRF):** Attacker directs crawler to private VPC networks, internal microservices (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`), or cloud metadata endpoints (`169.254.169.254`).
2. **DNS Rebinding (TOCTOU):** Attacker registers a domain whose DNS resolves to a public IP during preflight validation, but changes to `127.0.0.1` when the HTTP client initiates socket connection.
3. **Redirect Bypass:** Attacker hosts a public domain that issues a 302 redirect pointing to `http://169.254.169.254/latest/meta-data/` or internal admin endpoints.
4. **XML External Entity (XXE) Injection:** Malicious sitemaps containing `<!DOCTYPE ... <!ENTITY ... SYSTEM "file:///etc/passwd">` attempting file disclosure or billion-laughs entity expansion.
5. **Denial of Service (Resource Exhaustion):** Infinite redirect loops, massive response bodies (decompression bombs, continuous streams), or thousands of sitemap URLs.

---

## 2. Implemented Defense Mechanisms

### 2.1 Connection-Time IP Pinning (Defense-in-Depth against DNS Rebinding)
To eliminate Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding, preflight checks alone are deemed insufficient.
Site DNA injects a custom `httpcore.AsyncNetworkBackend` (`SSRFProtectedBackend`) directly into the connection pool:

```python
class SSRFProtectedBackend(httpcore._backends.anyio.AnyIOBackend):
    async def connect_tcp(self, host: str, port: int, ...):
        verified_ips = resolve_and_validate_host(host)
        # Directly connect to the verified public IP
        return await super().connect_tcp(verified_ips[0], port, ...)
```

- When initiating the TCP handshake, the socket connects directly to `verified_ips[0]`.
- For TLS connections, the SNI (`server_hostname`) remains the original hostname, ensuring full certificate validation.
- Every individual TCP connection (initial request and subsequent redirects) triggers this socket-level check.

### 2.2 Prohibited IP and Hostname Ranges
The validator blocks:
- Loopback addresses: `127.0.0.0/8`, `::1`
- Private networks: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- Link-local networks: `169.254.0.0/16`, `fe80::/10`
- Multicast & broadcast: `224.0.0.0/4`, `ff00::/8`, `255.255.255.255`
- Cloud metadata services: `169.254.169.254`, `100.100.100.200`, `metadata.google.internal`
- IPv4-mapped IPv6 representations: e.g. `::ffff:127.0.0.1` (automatically unwrapped and evaluated as IPv4).

### 2.3 Strict Scheme and Port Enforcement
- Schemes: Only `http` and `https` allowed. Non-web schemes (`file:`, `gopher:`, `ftp:`, `data:`, `javascript:`) raise `SecurityValidationError`.
- Ports: Only ports 80 and 443 are allowed. Non-standard ports (e.g. 22, 3306, 8080, 8443) are rejected to prevent port-scanning of internal subnets.
- Credentials: URLs containing `user:pass@host` are rejected immediately.

### 2.4 Streaming Size Limits & Timeout Ceilings
- Response bytes are checked via `Content-Length` headers and actively enforced during stream consumption (`aiter_bytes`).
- If downloaded bytes exceed `max_html_bytes` (3 MB default, 10 MB hard ceiling), download is immediately aborted with `ResponseTooLargeError`.
- Timeouts: Connect timeout (10s), Read timeout (15s), Total crawl session budget (90s).

### 2.5 Safe XML Parsing with defusedxml
All sitemap parsing uses `defusedxml.ElementTree`:
- Disallows DTD entity expansion.
- Disallows external entity loading.
- Limits nested depth to prevent exponential entity explosion.

### 2.6 Protected API Route Access
The `POST /api/v1/discovery` endpoint enforces three successive security gates:
1. `DISCOVERY_API_ENABLED=true` must be explicitly configured.
2. In development, requests must originate from loopback (`127.0.0.1`, `::1`, `localhost`).
3. If `DISCOVERY_API_TOKEN` is configured, requests must supply a valid `Authorization: Bearer <token>` header.
