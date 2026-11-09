"""Unit tests for IntelligentFrontier priority ordering, deduplication, and bounds."""

from site_dna.discovery.frontier import IntelligentFrontier, calculate_url_priority


def test_calculate_url_priority_ordering():
    p_home = calculate_url_priority("https://example.com/", depth=0)
    p_contact = calculate_url_priority("https://example.com/contact-us", depth=1)
    p_about = calculate_url_priority("https://example.com/about", depth=1)
    p_services = calculate_url_priority("https://example.com/services", depth=1)
    p_general = calculate_url_priority("https://example.com/terms", depth=1)

    assert p_home == 100
    assert p_contact == 90
    assert p_about == 85
    assert p_services == 80
    assert p_general < p_services


def test_calculate_url_priority_arabic_keywords():
    p_contact_ar = calculate_url_priority("https://example.com/اتصل-بنا", depth=1)
    p_about_ar = calculate_url_priority("https://example.com/من-نحن", depth=1)
    p_services_ar = calculate_url_priority("https://example.com/خدماتنا", depth=1)

    assert p_contact_ar == 90
    assert p_about_ar == 85
    assert p_services_ar == 80


def test_frontier_deduplication_and_depth_bounding():
    frontier = IntelligentFrontier(
        canonical_origin="https://example.com",
        max_depth=2,
        max_candidates=10,
    )

    # Adding seed
    assert frontier.add_candidate("https://example.com/", depth=0) is True

    # Duplicate should return False
    assert frontier.add_candidate("https://example.com/", depth=0) is False

    # Out of scope domain should return False
    assert frontier.add_candidate("https://other-site.com/about", depth=1) is False

    # Depth exceeded should return False
    assert frontier.add_candidate("https://example.com/deep/page", depth=3) is False

    # Add strategic candidates
    frontier.add_candidate("https://example.com/terms", depth=1)
    frontier.add_candidate("https://example.com/contact", depth=1)

    # First popped item must be the highest priority item (Home = 100)
    first = frontier.pop_next()
    assert first is not None
    assert first.url == "https://example.com/"

    # Second popped item must be Contact (90) before Terms (general)
    second = frontier.pop_next()
    assert second is not None
    assert second.url == "https://example.com/contact"
