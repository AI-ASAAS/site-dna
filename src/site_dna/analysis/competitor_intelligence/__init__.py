"""Site DNA Phase 08 — Competitor Intelligence Analysis Module."""

from site_dna.analysis.competitor_intelligence.collection_coordinator import CompetitorCollectionCoordinator
from site_dna.analysis.competitor_intelligence.company_profiles import CompetitorProfileExtractor
from site_dna.analysis.competitor_intelligence.context_builder import CompetitorContextBuilder
from site_dna.analysis.competitor_intelligence.evidence_validator import CompetitorEvidenceValidator
from site_dna.analysis.competitor_intelligence.feature_comparison import FeatureMatrixBuilder
from site_dna.analysis.competitor_intelligence.gap_analyzer import CompetitiveGapAnalyzer
from site_dna.analysis.competitor_intelligence.messaging_comparison import MessagingComparator
from site_dna.analysis.competitor_intelligence.offering_analyzer import OfferingAnalyzer
from site_dna.analysis.competitor_intelligence.opportunities import OpportunityEngine
from site_dna.analysis.competitor_intelligence.positioning_analyzer import PositioningAnalyzer
from site_dna.analysis.competitor_intelligence.pricing_comparison import PricingComparator
from site_dna.analysis.competitor_intelligence.recommendations import CompetitorRecommendationEngine
from site_dna.analysis.competitor_intelligence.relevance import CompetitorRelevanceClassifier
from site_dna.analysis.competitor_intelligence.report_builder import CompetitorReportBuilder
from site_dna.analysis.competitor_intelligence.scoring import CompetitorScoringEngine
from site_dna.analysis.competitor_intelligence.service import CompetitorIntelligenceService
from site_dna.analysis.competitor_intelligence.technical_benchmark import TechnicalBenchmarkAnalyzer
from site_dna.analysis.competitor_intelligence.trust_comparison import TrustComparator
from site_dna.analysis.competitor_intelligence.ux_benchmark import UXBenchmarkAnalyzer
from site_dna.analysis.competitor_intelligence.visual_benchmark import VisualBenchmarkAnalyzer

__all__ = [
    "CompetitorContextBuilder",
    "CompetitorCollectionCoordinator",
    "CompetitorRelevanceClassifier",
    "CompetitorProfileExtractor",
    "OfferingAnalyzer",
    "FeatureMatrixBuilder",
    "PricingComparator",
    "PositioningAnalyzer",
    "MessagingComparator",
    "VisualBenchmarkAnalyzer",
    "UXBenchmarkAnalyzer",
    "TechnicalBenchmarkAnalyzer",
    "TrustComparator",
    "CompetitiveGapAnalyzer",
    "OpportunityEngine",
    "CompetitorEvidenceValidator",
    "CompetitorScoringEngine",
    "CompetitorRecommendationEngine",
    "CompetitorReportBuilder",
    "CompetitorIntelligenceService",
]
