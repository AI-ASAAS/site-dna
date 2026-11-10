"""Visual identity model defined for Phase 4."""

from typing import Literal

from pydantic import BaseModel, Field

from site_dna.models.common import FileRef


class ColorUsage(BaseModel):
    """Per-context usage counters for a color sample."""

    text: int = 0
    background: int = 0
    border: int = 0
    svg: int = 0
    button: int = 0
    link: int = 0


class ColorRecord(BaseModel):
    """Observed color with ranking metadata (facts only)."""

    hex: str
    count: int = 0
    weight: float = 0.0
    share: float = 0.0
    usages: ColorUsage = Field(default_factory=ColorUsage)
    source: Literal["computed"] = "computed"


class ColorRoleRecord(BaseModel):
    """Heuristically assigned color role (inferred, not a fact)."""

    hex: str
    count: int = 0
    weight: float = 0.0
    share: float = 0.0
    usages: ColorUsage = Field(default_factory=ColorUsage)
    source: Literal["inferred"] = "inferred"


class ColorRoles(BaseModel):
    """Role assignments derived from the observed color palette."""

    background: list[ColorRoleRecord] = Field(default_factory=list)
    text: list[ColorRoleRecord] = Field(default_factory=list)
    primary: list[ColorRoleRecord] = Field(default_factory=list)
    secondary: list[ColorRoleRecord] = Field(default_factory=list)
    other: list[ColorRoleRecord] = Field(default_factory=list)
    roles_method: str | None = None


class ColorsAnalysis(BaseModel):
    """Observed palette plus inferred roles."""

    all: list[ColorRecord] = Field(default_factory=list)
    roles: ColorRoles = Field(default_factory=ColorRoles)


class FontFamilyRecord(BaseModel):
    """Ranked font family with parsed fallback stack."""

    family: str
    weight: float = 0.0
    primary: bool = False
    fallbacks: list[str] = Field(default_factory=list)
    loaded: bool = False


class HeadingStyle(BaseModel):
    """Computed style for a heading level."""

    color: str | None = None
    font_size: str | None = None
    font_weight: str | None = None
    font_family: str | None = None
    line_height: str | None = None
    letter_spacing: str | None = None
    text_transform: str | None = None


class TypographyAnalysis(BaseModel):
    """Typography evidence collected from the rendered page."""

    font_families: list[FontFamilyRecord] = Field(default_factory=list)
    font_sizes: dict[str, int] = Field(default_factory=dict)
    font_weights: dict[str, int] = Field(default_factory=dict)
    heading_styles: dict[str, HeadingStyle] = Field(default_factory=dict)


class VisualIdentity(BaseModel):
    """Visual identity evidence for the scanned site."""

    colors: ColorsAnalysis = Field(default_factory=ColorsAnalysis)
    typography: TypographyAnalysis = Field(default_factory=TypographyAnalysis)
    screenshot: FileRef | None = None
    css_variables: dict[str, str] = Field(default_factory=dict)
    sampled_elements: int = 0
    truncated_sampling: bool = False
