"""RFC 9309 compliant robots.txt parser and policy enforcement engine."""

import re
from typing import Optional
from urllib.parse import urljoin, urlsplit

from site_dna.core.logging import get_logger
from site_dna.discovery.http_client import FetchError, HttpResponseData, SecureHttpClient

logger = get_logger("discovery.robots_policy")


class RobotsRule:
    """A single Allow or Disallow rule with pattern matching semantics."""

    def __init__(self, is_allow: bool, pattern: str):
        self.is_allow = is_allow
        self.pattern = pattern
        self.pattern_length = len(pattern)
        self.regex = self._compile_pattern(pattern)

    @staticmethod
    def _compile_pattern(pattern: str) -> re.Pattern:
        """Convert a robots.txt path pattern (with * and $) into a regular expression."""
        if not pattern:
            # An empty Disallow pattern means allow everything
            return re.compile(r"^.*")

        escaped = re.escape(pattern)
        # Unescape wildcard *
        regex_str = escaped.replace(r"\*", ".*")

        if regex_str.endswith(r"\$"):
            regex_str = regex_str[:-2] + "$"
        else:
            regex_str = regex_str

        # Matches must begin at start of path
        if not regex_str.startswith("^"):
            regex_str = "^" + regex_str

        return re.compile(regex_str)

    def matches(self, path: str) -> bool:
        """Check if target path matches this rule."""
        if not self.pattern:
            return False
        return bool(self.regex.match(path))


class RobotsGroup:
    """A grouping of rules belonging to one or more User-Agents."""

    def __init__(self, user_agents: list[str]):
        self.user_agents = [ua.lower() for ua in user_agents]
        self.rules: list[RobotsRule] = []
        self.crawl_delay: Optional[float] = None

    def matches_user_agent(self, user_agent: str) -> bool:
        ua_clean = user_agent.lower().split("/")[0].strip()
        for target in self.user_agents:
            if target == "*" or target in ua_clean or ua_clean in target:
                return True
        return False


class RobotsPolicy:
    """Parsed robots.txt policy providing RFC 9309 compliance."""

    def __init__(
        self,
        origin: str,
        is_present: bool = True,
        status_code: int = 200,
        fail_closed: bool = False,
    ):
        self.origin = origin
        self.is_present = is_present
        self.status_code = status_code
        self.fail_closed = fail_closed
        self.groups: list[RobotsGroup] = []
        self.sitemaps: list[str] = []
        self.global_crawl_delay: Optional[float] = None

    def is_allowed(self, url: str, user_agent: str = "SiteDNABot") -> bool:
        """Evaluate if url is allowed according to RFC 9309 longest-match rules."""
        if self.fail_closed:
            return False

        if not self.is_present:
            return True

        parts = urlsplit(url)
        path = parts.path or "/"
        if parts.query:
            path = f"{path}?{parts.query}"

        # Find best matching group for user-agent
        ua_token = user_agent.lower().split("/")[0].strip()
        matched_group: Optional[RobotsGroup] = None
        wildcard_group: Optional[RobotsGroup] = None

        for group in self.groups:
            if ua_token in group.user_agents:
                matched_group = group
                break
            if "*" in group.user_agents:
                wildcard_group = group

        selected_group = matched_group or wildcard_group
        if not selected_group or not selected_group.rules:
            return True

        # RFC 9309 section 2.2.2: Find matching rule with longest pattern length
        best_match: Optional[RobotsRule] = None

        for rule in selected_group.rules:
            if rule.matches(path):
                if best_match is None:
                    best_match = rule
                elif rule.pattern_length > best_match.pattern_length:
                    best_match = rule
                elif rule.pattern_length == best_match.pattern_length:
                    # In case of tie, Allow takes precedence over Disallow
                    if rule.is_allow:
                        best_match = rule

        if best_match is None:
            return True

        return best_match.is_allow

    def get_crawl_delay(self, user_agent: str = "SiteDNABot") -> Optional[float]:
        """Retrieve crawl delay for given user agent if specified."""
        ua_token = user_agent.lower().split("/")[0].strip()
        for group in self.groups:
            if ua_token in group.user_agents and group.crawl_delay is not None:
                return group.crawl_delay
        for group in self.groups:
            if "*" in group.user_agents and group.crawl_delay is not None:
                return group.crawl_delay
        return self.global_crawl_delay

    @classmethod
    def parse(cls, content: str, origin: str, status_code: int = 200) -> "RobotsPolicy":
        """Parse raw robots.txt text into a structured RobotsPolicy."""
        policy = cls(origin=origin, is_present=True, status_code=status_code)
        current_user_agents: list[str] = []
        current_group: Optional[RobotsGroup] = None

        for raw_line in content.splitlines():
            line = raw_line.strip()
            # Strip comments
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line:
                continue

            if ":" not in line:
                continue

            field, value = line.split(":", 1)
            field = field.strip().lower()
            value = value.strip()

            if field == "user-agent":
                if current_group is not None and current_group.rules:
                    policy.groups.append(current_group)
                    current_group = None
                    current_user_agents = []

                current_user_agents.append(value)
                if current_group is None:
                    current_group = RobotsGroup(current_user_agents)
                else:
                    current_group.user_agents.append(value.lower())

            elif field == "disallow":
                if current_group is None:
                    current_group = RobotsGroup(["*"])
                if value:
                    current_group.rules.append(RobotsRule(is_allow=False, pattern=value))

            elif field == "allow":
                if current_group is None:
                    current_group = RobotsGroup(["*"])
                if value:
                    current_group.rules.append(RobotsRule(is_allow=True, pattern=value))

            elif field == "crawl-delay":
                try:
                    delay = float(value)
                    if current_group is not None:
                        current_group.crawl_delay = delay
                    else:
                        policy.global_crawl_delay = delay
                except ValueError:
                    pass

            elif field == "sitemap":
                if value:
                    policy.sitemaps.append(value)

        if current_group is not None:
            policy.groups.append(current_group)

        return policy

    @classmethod
    async def fetch_policy(
        cls,
        client: SecureHttpClient,
        origin: str,
        user_agent: str = "SiteDNABot",
    ) -> "RobotsPolicy":
        """Fetch and parse /robots.txt from the given origin.

        Applies RFC 9309 status code rules:
        - 2xx: Parse rules.
        - 4xx (e.g. 404): Full access allowed (fail-open).
        - 5xx or network errors: Treat as inaccessible (fail-closed).
        """
        robots_url = urljoin(origin, "/robots.txt")
        try:
            resp: HttpResponseData = await client.fetch(robots_url, allow_xml=False, allow_plain_text=True)
            if resp.status_code == 200:
                logger.info("Successfully fetched robots.txt from %s", robots_url)
                return cls.parse(resp.text, origin=origin, status_code=200)
            elif 400 <= resp.status_code < 500:
                logger.info(
                    "Robots.txt returned %d at %s: allowing full access (fail-open)", resp.status_code, robots_url
                )
                return cls(origin=origin, is_present=False, status_code=resp.status_code, fail_closed=False)
            else:
                logger.warning("Robots.txt returned %d at %s: fail-closed access", resp.status_code, robots_url)
                return cls(origin=origin, is_present=False, status_code=resp.status_code, fail_closed=True)
        except FetchError as e:
            logger.warning("Failed to fetch robots.txt from %s (%s): defaulting to fail-closed", robots_url, e)
            return cls(origin=origin, is_present=False, status_code=500, fail_closed=True)
        except Exception as e:
            logger.warning("Unexpected error fetching robots.txt from %s (%s): fail-closed", robots_url, e)
            return cls(origin=origin, is_present=False, status_code=500, fail_closed=True)
