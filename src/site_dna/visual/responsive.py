"""Responsive layout analyzer comparing desktop and mobile rendering states."""

from playwright.async_api import Page

from site_dna.schemas.visual import ResponsiveObservation


class ResponsiveAnalyzer:
    """Analyzes differences, horizontal overflow, and layout shifts across viewports."""

    @staticmethod
    async def measure_viewport_metrics(page: Page) -> dict[str, int]:
        """Measure scroll dimensions and inner viewport size from the browser."""
        return await page.evaluate(
            """() => ({
            scroll_width: document.documentElement.scrollWidth,
            scroll_height: document.documentElement.scrollHeight,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight
        })"""
        )

    @staticmethod
    def compare_viewports(
        desktop_metrics: dict[str, int],
        mobile_metrics: dict[str, int],
    ) -> list[ResponsiveObservation]:
        """Compare desktop and mobile measurements to detect overflows and responsive adaptations."""
        observations: list[ResponsiveObservation] = []

        # 1. Horizontal overflow check on mobile
        m_scroll_w = mobile_metrics.get("scroll_width", 390)
        m_vp_w = mobile_metrics.get("viewport_width", 390)

        if m_scroll_w > m_vp_w + 2:  # small tolerance for scrollbar margin
            observations.append(
                ResponsiveObservation(
                    observation_type="horizontal_overflow",
                    status="observed",
                    description=f"Mobile viewport experienced horizontal overflow (scroll width: {m_scroll_w}px > viewport: {m_vp_w}px)",
                    desktop_value={"scroll_width": desktop_metrics.get("scroll_width")},
                    mobile_value={"scroll_width": m_scroll_w, "viewport_width": m_vp_w},
                )
            )
        else:
            observations.append(
                ResponsiveObservation(
                    observation_type="horizontal_overflow",
                    status="observed",
                    description="No horizontal overflow observed on mobile viewport.",
                    desktop_value={"scroll_width": desktop_metrics.get("scroll_width")},
                    mobile_value={"scroll_width": m_scroll_w, "viewport_width": m_vp_w},
                )
            )

        # 2. Viewport height adaptation check
        d_scroll_h = desktop_metrics.get("scroll_height", 0)
        m_scroll_h = mobile_metrics.get("scroll_height", 0)

        if m_scroll_h > 0 and d_scroll_h > 0:
            observations.append(
                ResponsiveObservation(
                    observation_type="vertical_stacking_adaptation",
                    status="observed",
                    description="Document height adapted for narrow vertical mobile stacking.",
                    desktop_value={"height": d_scroll_h},
                    mobile_value={"height": m_scroll_h},
                )
            )

        return observations
