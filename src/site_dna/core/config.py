"""Application configuration management for Site DNA using Pydantic Settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Site DNA application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="Site DNA", description="Application name")
    app_env: str = Field(default="development", description="Environment: development, test, production")
    app_host: str = Field(default="127.0.0.1", description="Host to bind HTTP server")
    app_port: int = Field(default=8000, description="Port to bind HTTP server")

    # Primary API key configuration
    gemini_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Google Gemini API key from Google AI Studio (primary credential)",
    )

    gemini_model: str = Field(
        default="gemini-3.6-flash",
        description="Gemini model identifier (e.g. gemini-3.6-flash)",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )

    enable_live_llm_tests: bool = Field(
        default=False,
        description="Explicit opt-in flag for tests requiring live Gemini network calls",
    )

    # Website Intelligence MVP (Phases 1-9): scan configuration
    psi_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Google PageSpeed Insights API key (optional; unauthenticated calls are attempted)",
    )
    storage_dir: str = Field(
        default="storage",
        description="Directory for per-scan runtime artifacts (gitignored)",
    )
    allow_private_hosts: bool = Field(
        default=False,
        description="Allow private/loopback targets; only honored when APP_ENV=test",
    )
    scan_max_pages: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Default maximum pages per scan",
    )
    scan_max_depth: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Default maximum crawl depth per scan",
    )
    scan_max_broken_link_checks: int = Field(
        default=200,
        ge=0,
        le=5000,
        description="Default maximum broken-link checks per scan",
    )
    scan_request_timeout_seconds: float = Field(
        default=20.0,
        ge=1.0,
        le=120.0,
        description="Default HTTP request timeout for scans",
    )
    scan_page_timeout_seconds: float = Field(
        default=45.0,
        ge=1.0,
        le=300.0,
        description="Default browser page timeout for scans",
    )
    scan_psi_timeout_seconds: float = Field(
        default=90.0,
        ge=1.0,
        le=300.0,
        description="Default PageSpeed Insights timeout for scans",
    )
    scan_per_host_rps: float = Field(
        default=2.0,
        gt=0.0,
        le=50.0,
        description="Default per-host request rate (requests per second)",
    )
    scan_max_total_seconds: float = Field(
        default=300.0,
        ge=1.0,
        le=3600.0,
        description="Default wall-clock budget for a whole scan",
    )

    # Phase 02: Website Discovery & Crawler Configuration
    crawler_max_pages: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Default maximum pages to crawl per site run",
    )
    crawler_max_depth: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum crawl depth relative to root/seed page",
    )
    crawler_max_candidates: int = Field(
        default=200,
        ge=1,
        le=1000,
        description="Maximum candidates tracked in frontier",
    )
    crawler_max_concurrency: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Maximum concurrent HTTP requests per crawl session",
    )
    crawler_request_delay_seconds: float = Field(
        default=1.0,
        ge=0.0,
        le=30.0,
        description="Politeness delay between requests to the same origin",
    )
    crawler_connect_timeout_seconds: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="TCP/TLS connection timeout in seconds",
    )
    crawler_read_timeout_seconds: float = Field(
        default=15.0,
        ge=1.0,
        le=120.0,
        description="Response read timeout in seconds",
    )
    crawler_total_timeout_seconds: float = Field(
        default=90.0,
        ge=5.0,
        le=600.0,
        description="Total crawl execution budget in seconds",
    )
    crawler_max_redirects: int = Field(
        default=5,
        ge=0,
        le=10,
        description="Maximum redirects allowed per fetch",
    )
    crawler_max_html_bytes: int = Field(
        default=3145728,  # 3 MB
        ge=1024,
        le=10485760,  # 10 MB ceiling
        description="Maximum permitted HTML response size in bytes",
    )
    crawler_respect_robots: bool = Field(
        default=True,
        description="Whether to fetch and strictly enforce robots.txt",
    )
    crawler_user_agent: str = Field(
        default="SiteDNABot/0.1 (+https://site-dna.asaas.ai/bot)",
        description="Identifiable crawler User-Agent header",
    )
    discovery_api_enabled: bool = Field(
        default=False,
        description="Whether the POST /api/v1/discovery endpoint is enabled",
    )
    discovery_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token required for POST /api/v1/discovery access",
    )

    # Phase 03: Visual Evidence & Browser Rendering Configuration
    visual_capture_enabled: bool = Field(
        default=False,
        description="Whether live browser captures are enabled",
    )
    visual_browser: str = Field(
        default="chromium",
        description="Browser engine for visual rendering",
    )
    visual_headless: bool = Field(
        default=True,
        description="Whether to run browser in headless mode",
    )
    visual_desktop_width: int = Field(
        default=1440,
        ge=800,
        le=3840,
        description="Desktop viewport width in pixels",
    )
    visual_desktop_height: int = Field(
        default=900,
        ge=600,
        le=2160,
        description="Desktop viewport height in pixels",
    )
    visual_mobile_width: int = Field(
        default=390,
        ge=320,
        le=768,
        description="Mobile viewport width in pixels",
    )
    visual_mobile_height: int = Field(
        default=844,
        ge=480,
        le=1200,
        description="Mobile viewport height in pixels",
    )
    visual_mobile_dpr: float = Field(
        default=2.0,
        ge=1.0,
        le=3.0,
        description="Mobile device scale factor",
    )
    visual_max_pages: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum pages to capture visually per run",
    )
    visual_max_concurrency: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum concurrent browser pages",
    )
    visual_navigation_timeout_ms: int = Field(
        default=20000,
        ge=1000,
        le=60000,
        description="Navigation timeout in milliseconds",
    )
    visual_font_wait_timeout_ms: int = Field(
        default=5000,
        ge=500,
        le=15000,
        description="Timeout waiting for document.fonts.ready in milliseconds",
    )
    visual_capture_timeout_ms: int = Field(
        default=30000,
        ge=5000,
        le=120000,
        description="Total capture timeout per page in milliseconds",
    )
    visual_max_page_height: int = Field(
        default=12000,
        ge=1000,
        le=30000,
        description="Maximum full-page screenshot height in pixels",
    )
    visual_max_screenshot_bytes: int = Field(
        default=15000000,  # 15 MB
        ge=100000,
        le=50000000,
        description="Maximum allowed screenshot file size in bytes",
    )
    visual_max_dom_elements: int = Field(
        default=1000,
        ge=50,
        le=5000,
        description="Maximum DOM elements to extract per page",
    )
    visual_max_evidence_records: int = Field(
        default=5000,
        ge=100,
        le=20000,
        description="Maximum visual evidence records per run",
    )
    visual_respect_robots: bool = Field(
        default=True,
        description="Whether to respect robots.txt rules during visual capture",
    )
    visual_block_service_workers: bool = Field(
        default=True,
        description="Whether to block service workers during rendering",
    )
    visual_require_secure_network: bool = Field(
        default=True,
        description="Whether to enforce strict outbound network egress filtering",
    )
    visual_api_enabled: bool = Field(
        default=False,
        description="Whether the POST /api/v1/visual/capture endpoint is enabled",
    )
    visual_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for visual capture API access",
    )

    # Phase 04: Visual Identity Analysis Configuration
    visual_analysis_enabled: bool = Field(
        default=True,
        description="Whether AI visual identity analysis is enabled",
    )
    visual_analysis_model: str = Field(
        default="gemini-3.6-flash",
        description="Target Gemini model for visual identity analysis",
    )
    visual_analysis_max_pages: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum pages to include in visual identity analysis",
    )
    visual_analysis_max_images: int = Field(
        default=8,
        ge=1,
        le=30,
        description="Maximum screenshot images to pass to multimodal model",
    )
    visual_analysis_max_output_tokens: int = Field(
        default=2048,
        ge=256,
        le=8192,
        description="Maximum output tokens for visual identity model response",
    )
    visual_analysis_cache_enabled: bool = Field(
        default=True,
        description="Whether to cache visual identity model responses by hash",
    )
    visual_analysis_cache_dir: str = Field(
        default="runs/cache",
        description="Directory to persist model response cache entries",
    )
    visual_analysis_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts on transient model errors",
    )
    visual_analysis_max_findings: int = Field(
        default=30,
        ge=5,
        le=100,
        description="Maximum findings to generate per analysis",
    )
    visual_analysis_max_recommendations: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Maximum prioritized recommendations to generate",
    )
    visual_analysis_save_results: bool = Field(
        default=True,
        description="Whether to save analysis.json and report.md artifacts",
    )
    visual_analysis_api_enabled: bool = Field(
        default=False,
        description="Whether the POST /api/v1/analysis/visual-identity endpoint is enabled",
    )
    visual_analysis_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for visual analysis API access",
    )

    # Phase 05: UX/UI Intelligence & Usability Analysis Configuration
    ux_analysis_enabled: bool = Field(
        default=True,
        description="Whether UX/UI analysis engine is enabled",
    )
    ux_analysis_model: str = Field(
        default="gemini-3.6-flash",
        description="Official target Gemini model for UX/UI analysis",
    )
    ux_analysis_max_pages: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum pages to include in UX/UI analysis",
    )
    ux_analysis_max_images: int = Field(
        default=8,
        ge=1,
        le=30,
        description="Maximum screenshot images to pass to multimodal model for UX analysis",
    )
    ux_analysis_max_model_calls: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum model API calls permitted per UX analysis run",
    )
    ux_analysis_max_recommendations: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Maximum prioritized UX recommendations to generate",
    )
    ux_analysis_cache_enabled: bool = Field(
        default=True,
        description="Whether to cache UX/UI model responses by content hash",
    )
    ux_analysis_cache_dir: str = Field(
        default="runs/cache",
        description="Directory to persist UX model response cache entries",
    )
    ux_analysis_max_output_tokens: int = Field(
        default=2048,
        ge=256,
        le=8192,
        description="Maximum output tokens for UX/UI model response",
    )
    ux_analysis_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts on transient model errors",
    )
    ux_analysis_require_ai: bool = Field(
        default=True,
        description="Whether full completion strictly requires successful AI execution",
    )
    ux_interaction_tests_enabled: bool = Field(
        default=False,
        description="Whether safe browser interaction measurements are enabled",
    )
    ux_public_active_testing_enabled: bool = Field(
        default=False,
        description="Whether active state-changing testing on public websites is enabled (strictly False)",
    )
    ux_analysis_save_results: bool = Field(
        default=True,
        description="Whether to save analysis artifacts to disk",
    )
    ux_analysis_api_enabled: bool = Field(
        default=True,
        description="Whether the POST /api/v1/analysis/ux-ui endpoint is enabled",
    )
    ux_analysis_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for UX analysis API access",
    )

    # Phase 06: Content & Marketing Intelligence Analysis Configuration
    content_analysis_enabled: bool = Field(
        default=True,
        description="Whether Content & Marketing Intelligence analysis engine is enabled",
    )
    content_analysis_model: str = Field(
        default="gemini-3.6-flash",
        description="Official target Gemini model for content and marketing analysis",
    )
    content_analysis_max_pages: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum pages to include in content and marketing analysis",
    )
    content_analysis_max_model_calls: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum model API calls permitted per content analysis run",
    )
    content_analysis_max_recommendations: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Maximum prioritized content recommendations to generate",
    )
    content_analysis_max_rewrite_proposals: int = Field(
        default=8,
        ge=1,
        le=30,
        description="Maximum grounded copy rewrite proposals to generate",
    )
    content_analysis_max_output_tokens: int = Field(
        default=2048,
        ge=256,
        le=8192,
        description="Maximum output tokens for content model response",
    )
    content_analysis_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts on transient model errors",
    )
    content_analysis_cache_enabled: bool = Field(
        default=True,
        description="Whether to cache content model responses by content hash",
    )
    content_analysis_cache_dir: str = Field(
        default="runs/cache",
        description="Directory to persist content model response cache entries",
    )
    content_analysis_require_ai: bool = Field(
        default=True,
        description="Whether full completion strictly requires successful AI execution",
    )
    content_analysis_save_results: bool = Field(
        default=True,
        description="Whether to save analysis artifacts to disk",
    )
    content_analysis_api_enabled: bool = Field(
        default=True,
        description="Whether the POST /api/v1/analysis/content-marketing endpoint is enabled",
    )
    content_analysis_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for content analysis API access",
    )

    # Phase 07: Technical SEO, Performance & Core Web Vitals Configuration
    technical_seo_enabled: bool = Field(
        default=True,
        description="Whether Technical SEO analysis engine is enabled",
    )
    technical_seo_model: str = Field(
        default="gemini-3.6-flash",
        description="Official target Gemini model for Technical SEO analysis",
    )
    technical_seo_max_pages: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum pages to include in Technical SEO analysis",
    )
    technical_seo_max_model_calls: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum model API calls permitted per Technical SEO run",
    )
    technical_seo_max_recommendations: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Maximum prioritized Technical SEO recommendations to generate",
    )
    technical_seo_max_output_tokens: int = Field(
        default=2048,
        ge=256,
        le=8192,
        description="Maximum output tokens for Technical SEO model response",
    )
    technical_seo_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts on transient model errors",
    )
    technical_seo_cache_enabled: bool = Field(
        default=True,
        description="Whether to cache Technical SEO model responses by content hash",
    )
    technical_seo_cache_dir: str = Field(
        default="runs/cache",
        description="Directory to persist Technical SEO model response cache entries",
    )
    technical_seo_require_ai: bool = Field(
        default=True,
        description="Whether full completion strictly requires successful AI execution",
    )
    technical_seo_save_results: bool = Field(
        default=True,
        description="Whether to save analysis artifacts to disk",
    )
    technical_seo_api_enabled: bool = Field(
        default=True,
        description="Whether the POST /api/v1/analysis/technical-seo endpoint is enabled",
    )
    technical_seo_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for Technical SEO API access",
    )
    technical_seo_performance_enabled: bool = Field(
        default=False,
        description="Whether live browser performance measurements are enabled (bounded, disabled by default)",
    )
    technical_seo_external_metrics_enabled: bool = Field(
        default=False,
        description="Whether external PSI/CrUX metrics adapters are enabled (disabled by default)",
    )
    technical_seo_max_concurrency: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Maximum concurrency for technical measurements",
    )
    technical_seo_psi_enabled: bool = Field(
        default=False,
        description="Whether PageSpeed Insights API is enabled (disabled by default)",
    )
    technical_seo_crux_enabled: bool = Field(
        default=False,
        description="Whether Chrome UX Report API is enabled (disabled by default)",
    )

    # Phase 08: Competitor Intelligence Configuration
    competitor_analysis_enabled: bool = Field(
        default=True,
        description="Whether Competitor Intelligence analysis engine is enabled",
    )
    competitor_analysis_model: str = Field(
        default="gemini-3.6-flash",
        description="Official target Gemini model for competitor intelligence",
    )
    competitor_analysis_max_competitors: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Default maximum competitors per comparison run",
    )
    competitor_analysis_hard_max_competitors: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Hard upper limit of competitors per comparison run",
    )
    competitor_analysis_max_pages_per_site: int = Field(
        default=5,
        ge=1,
        le=15,
        description="Maximum crawl depth/pages per competitor website",
    )
    competitor_analysis_max_model_calls: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum LLM calls per competitor intelligence run",
    )
    competitor_analysis_max_recommendations: int = Field(
        default=12,
        ge=1,
        le=30,
        description="Maximum strategic recommendations to output",
    )
    competitor_analysis_cache_enabled: bool = Field(
        default=True,
        description="Whether to cache competitor intelligence model responses",
    )
    competitor_discovery_enabled: bool = Field(
        default=False,
        description="Whether automated competitor discovery is enabled (disabled by default)",
    )
    competitor_public_crawl_enabled: bool = Field(
        default=True,
        description="Whether external crawling of competitor URLs is permitted",
    )
    competitor_max_concurrent_origins: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Maximum concurrent competitor origins crawled",
    )
    competitor_analysis_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for Competitor Intelligence API access",
    )

    # Phase 09: Security, Privacy & Digital Trust Intelligence Configuration
    security_analysis_enabled: bool = Field(
        default=True,
        description="Whether Security, Privacy & Digital Trust analysis engine is enabled",
    )
    security_analysis_model: str = Field(
        default="gemini-3.6-flash",
        description="Official target Gemini model for security & privacy analysis",
    )
    security_analysis_max_pages: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum pages to assess for security and privacy posture",
    )
    security_analysis_max_model_calls: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum LLM calls per security analysis run",
    )
    security_analysis_max_recommendations: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Maximum security remediation recommendations to output",
    )
    security_analysis_cache_enabled: bool = Field(
        default=True,
        description="Whether to cache security analysis model responses",
    )
    security_analysis_require_ai: bool = Field(
        default=True,
        description="Whether AI interpretation is required for complete analysis",
    )
    security_analysis_passive_only: bool = Field(
        default=True,
        description="Strictly passive analysis only (no active vulnerability scanning/exploits)",
    )
    security_analysis_live_collection_enabled: bool = Field(
        default=False,
        description="Whether live collection is permitted beyond existing crawl artifacts",
    )
    security_analysis_max_concurrency: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum concurrent security tasks",
    )
    security_analysis_redact_secrets: bool = Field(
        default=True,
        description="Strictly redact cookies, auth tokens, and sensitive headers",
    )
    security_analysis_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for Security & Privacy API access",
    )

    # Phase 10: Web Accessibility, Inclusive Experience & WCAG 2.2 Intelligence
    accessibility_analysis_enabled: bool = Field(
        default=True,
        description="Whether Accessibility & Inclusive Experience analysis engine is enabled",
    )
    accessibility_analysis_model: str = Field(
        default="gemini-3.6-flash",
        description="Official target Gemini model for accessibility analysis",
    )
    accessibility_max_pages: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum representative pages to sample and evaluate for accessibility",
    )
    accessibility_max_model_calls: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum LLM calls per accessibility analysis run",
    )
    accessibility_max_recommendations: int = Field(
        default=12,
        ge=1,
        le=30,
        description="Maximum accessibility remediation recommendations to output",
    )
    accessibility_cache_enabled: bool = Field(
        default=True,
        description="Whether to cache accessibility analysis model responses",
    )
    accessibility_require_ai: bool = Field(
        default=True,
        description="Whether AI interpretation is required for complete analysis",
    )
    accessibility_browser_tests_enabled: bool = Field(
        default=False,
        description="Whether active browser keyboard/focus testing is enabled",
    )
    accessibility_public_interaction_enabled: bool = Field(
        default=False,
        description="Strictly bounded interaction on third-party public sites (default false for safety)",
    )
    accessibility_automated_rules_enabled: bool = Field(
        default=True,
        description="Whether automated accessibility rules (e.g., axe-core or rules adapter) are enabled",
    )
    accessibility_max_concurrency: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum concurrent accessibility evaluation tasks",
    )
    accessibility_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for Accessibility Intelligence API access",
    )

    # Phase 11: Strategic Intelligence, Cross-Agent Synthesis & Unified Action Roadmap
    strategic_intelligence_enabled: bool = Field(
        default=True,
        description="Whether Strategic Intelligence & Action Roadmap synthesis engine is enabled",
    )
    strategic_intelligence_model: str = Field(
        default="gemini-3.6-flash",
        description="Official target Gemini model for strategic synthesis (strictly gemini-3.6-flash)",
    )
    strategic_max_actions: int = Field(
        default=50,
        ge=5,
        le=200,
        description="Maximum prioritized implementation tasks in backlog",
    )
    strategic_max_model_calls: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum LLM calls per strategic synthesis run",
    )
    strategic_cache_enabled: bool = Field(
        default=True,
        description="Whether to cache strategic synthesis responses",
    )
    strategic_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Bearer token for Strategic Intelligence API access",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"Invalid log_level: {v}. Must be one of {valid_levels}")
        return upper

    @field_validator("app_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"app_port must be between 1 and 65535, got {v}")
        return v

    def get_effective_gemini_api_key(self) -> Optional[str]:
        """Resolve the effective Gemini API key following documented precedence rules."""
        if self.gemini_api_key and self.gemini_api_key.get_secret_value().strip():
            return self.gemini_api_key.get_secret_value().strip()

        fallback = os.getenv("GOOGLE_API_KEY", "").strip()
        if fallback:
            return fallback

        return None

    def is_gemini_configured(self) -> bool:
        """Check if a non-empty Gemini API key is available."""
        key = self.get_effective_gemini_api_key()
        return bool(key and len(key) > 5)

    def get_effective_discovery_token(self) -> Optional[str]:
        """Return discovery API token secret string value if set."""
        if self.discovery_api_token and self.discovery_api_token.get_secret_value().strip():
            return self.discovery_api_token.get_secret_value().strip()
        return None

    def get_effective_ux_token(self) -> Optional[str]:
        """Return UX analysis API token secret string value if set."""
        if self.ux_analysis_api_token and self.ux_analysis_api_token.get_secret_value().strip():
            return self.ux_analysis_api_token.get_secret_value().strip()
        return None

    def get_effective_content_token(self) -> Optional[str]:
        """Return content analysis API token secret string value if set."""
        if self.content_analysis_api_token and self.content_analysis_api_token.get_secret_value().strip():
            return self.content_analysis_api_token.get_secret_value().strip()
        return None

    def get_effective_seo_token(self) -> Optional[str]:
        """Return Technical SEO analysis API token secret string value if set."""
        if self.technical_seo_api_token and self.technical_seo_api_token.get_secret_value().strip():
            return self.technical_seo_api_token.get_secret_value().strip()
        return None

    def get_effective_competitor_model(self) -> str:
        """Return official AI model for competitor analysis."""
        return self.competitor_analysis_model

    def get_effective_competitor_token(self) -> Optional[str]:
        """Return Competitor Intelligence API token secret string value if set."""
        if self.competitor_analysis_api_token and self.competitor_analysis_api_token.get_secret_value().strip():
            return self.competitor_analysis_api_token.get_secret_value().strip()
        return None

    def get_effective_security_model(self) -> str:
        """Return official AI model for security & privacy analysis."""
        return self.security_analysis_model

    def get_effective_security_token(self) -> Optional[str]:
        """Return Security & Privacy API token secret string value if set."""
        if self.security_analysis_api_token and self.security_analysis_api_token.get_secret_value().strip():
            return self.security_analysis_api_token.get_secret_value().strip()
        return None

    def get_effective_accessibility_model(self) -> str:
        """Return official AI model for accessibility & inclusive experience analysis."""
        return self.accessibility_analysis_model

    def get_effective_accessibility_token(self) -> Optional[str]:
        """Return Accessibility Intelligence API token secret string value if set."""
        if self.accessibility_api_token and self.accessibility_api_token.get_secret_value().strip():
            return self.accessibility_api_token.get_secret_value().strip()
        return None

    def get_effective_strategic_model(self) -> str:
        """Return official AI model for Phase 11 strategic synthesis (strictly gemini-3.6-flash)."""
        return self.strategic_intelligence_model

    def get_effective_strategic_token(self) -> Optional[str]:
        """Return Strategic Intelligence API token secret string value if set."""
        if self.strategic_api_token and self.strategic_api_token.get_secret_value().strip():
            return self.strategic_api_token.get_secret_value().strip()
        return None

    def get_effective_psi_api_key(self) -> Optional[str]:
        """Return the PageSpeed Insights API key if configured."""
        if self.psi_api_key and self.psi_api_key.get_secret_value().strip():
            return self.psi_api_key.get_secret_value().strip()
        return None

    def private_hosts_allowed(self) -> bool:
        """Return True only when private hosts are allowed AND the app is in test mode."""
        return self.allow_private_hosts and self.app_env.strip().lower() == "test"

    def __repr__(self) -> str:
        """Sanitized string representation ensuring no credentials leak."""
        key_status = "configured" if self.is_gemini_configured() else "missing"
        psi_status = "configured" if self.get_effective_psi_api_key() else "missing"
        token_status = "configured" if self.get_effective_discovery_token() else "missing"
        return (
            f"Settings(app_name='{self.app_name}', app_env='{self.app_env}', "
            f"host='{self.app_host}:{self.app_port}', gemini_model='{self.gemini_model}', "
            f"gemini_api_key=[{key_status}], psi_api_key=[{psi_status}], "
            f"discovery_api_token=[{token_status}], storage_dir='{self.storage_dir}', "
            f"allow_private_hosts={self.allow_private_hosts}, "
            f"crawler_max_pages={self.crawler_max_pages}, log_level='{self.log_level}')"
        )


class ScanConfig(BaseModel):
    """Per-run configuration built from CLI flags and application settings."""

    input_url: str
    max_pages: int = 20
    max_depth: int = 2
    max_broken_link_checks: int = 200
    request_timeout: float = 20.0
    page_timeout: float = 45.0
    psi_timeout: float = 90.0
    per_host_rps: float = 2.0
    max_total_seconds: float = 300.0
    embed_images: bool = False
    output_dir: Optional[str] = None
    verbose: bool = False
    permission_attested: bool = False

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        input_url: str,
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None,
        max_broken_link_checks: Optional[int] = None,
        output_dir: Optional[str] = None,
        embed_images: bool = False,
        verbose: bool = False,
        permission_attested: bool = False,
    ) -> "ScanConfig":
        """Merge explicit CLI overrides with settings defaults."""
        return cls(
            input_url=input_url,
            max_pages=max_pages if max_pages is not None else settings.scan_max_pages,
            max_depth=max_depth if max_depth is not None else settings.scan_max_depth,
            max_broken_link_checks=(
                max_broken_link_checks
                if max_broken_link_checks is not None
                else settings.scan_max_broken_link_checks
            ),
            request_timeout=settings.scan_request_timeout_seconds,
            page_timeout=settings.scan_page_timeout_seconds,
            psi_timeout=settings.scan_psi_timeout_seconds,
            per_host_rps=settings.scan_per_host_rps,
            max_total_seconds=settings.scan_max_total_seconds,
            embed_images=embed_images,
            output_dir=output_dir,
            verbose=verbose,
            permission_attested=permission_attested,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
