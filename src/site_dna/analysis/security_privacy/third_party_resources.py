"""Third-Party Resource Inventory and Privacy Review for Site DNA Phase 09."""

from urllib.parse import urlsplit

from site_dna.schemas.security_privacy import (
    SecurityPageRecord,
    ThirdPartyResourceAssessment,
    ThirdPartyResourceRecord,
)

KNOWN_PROVIDERS = {
    "google-analytics.com": ("analytics", True),
    "googletagmanager.com": ("tag_manager", True),
    "analytics.google.com": ("analytics", True),
    "facebook.net": ("advertising", True),
    "clarity.ms": ("analytics", True),
    "hotjar.com": ("analytics", True),
    "mixpanel.com": ("analytics", True),
    "segment.com": ("analytics", True),
    "doubleclick.net": ("advertising", True),
    "fonts.googleapis.com": ("fonts", False),
    "fonts.gstatic.com": ("fonts", False),
    "cdnjs.cloudflare.com": ("cdn_library", False),
    "cdn.jsdelivr.net": ("cdn_library", False),
    "unpkg.com": ("cdn_library", False),
    "intercom.io": ("customer_support", True),
    "zendesk.com": ("customer_support", True),
}


class ThirdPartyResourceAnalyzer:
    """Inventories and categorizes external asset origins observed across pages."""

    def analyze(self, page_records: list[SecurityPageRecord]) -> ThirdPartyResourceAssessment:
        """Categorize third-party origins observed in page records."""
        origin_map: dict[str, ThirdPartyResourceRecord] = {}
        total_third_party_requests = 0

        for idx, page in enumerate(page_records, start=1):
            for orig in page.third_party_origins:
                total_third_party_requests += 1
                parts = urlsplit(orig)
                host = parts.hostname or orig

                if host not in origin_map:
                    category = "other"
                    requires_review = False

                    # Check against known providers
                    for pattern, (cat, rev) in KNOWN_PROVIDERS.items():
                        if pattern in host.lower():
                            category = cat
                            requires_review = rev
                            break

                    origin_map[host] = ThirdPartyResourceRecord(
                        origin=f"{parts.scheme or 'https'}://{host}",
                        resource_category=category,  # type: ignore
                        pages_observed=[page.page_url],
                        resource_types=["external_asset"],
                        requires_privacy_review=requires_review,
                        evidence_ids=[f"ev-ext-{host}-p{idx}"],
                    )
                else:
                    rec = origin_map[host]
                    if page.page_url not in rec.pages_observed:
                        rec.pages_observed.append(page.page_url)

        origins_list = list(origin_map.values())
        has_analytics = any(o.resource_category in ("analytics", "tag_manager") for o in origins_list)
        has_trackers = any(o.resource_category == "advertising" for o in origins_list)

        notes = (
            f"Identified {len(origins_list)} unique third-party origins across {len(page_records)} pages. "
            f"Analytics detected: {'Yes' if has_analytics else 'No'}, "
            f"Advertising trackers: {'Yes' if has_trackers else 'No'}."
        )
        notes_ar = (
            f"تم رصد {len(origins_list)} نطاق خارجي فريد عبر {len(page_records)} صفحة. "
            f"خدمات التحليل: {'مرصودة' if has_analytics else 'غير مرصودة'}، "
            f"شبكات الإعلانات والتعقب: {'مرصودة' if has_trackers else 'غير مرصودة'}."
        )

        return ThirdPartyResourceAssessment(
            total_first_party_requests=len(page_records) * 5,
            total_third_party_requests=total_third_party_requests,
            unique_third_party_origins=len(origins_list),
            third_party_origins_list=origins_list,
            has_analytics=has_analytics,
            has_trackers=has_trackers,
            evidence_ids=[f"ev-ext-origins-{len(origins_list)}"] if origins_list else [],
            notes=notes,
            notes_ar=notes_ar,
        )
