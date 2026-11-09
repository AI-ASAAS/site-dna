"""Structured data (Schema.org / JSON-LD) validation and audit engine."""

import json
from typing import Any

from site_dna.schemas.technical_seo import (
    StructuredDataAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)

# Common Google Rich Result schema requirements
SUPPORTED_SCHEMA_REQUIREMENTS: dict[str, list[str]] = {
    "organization": ["name", "url"],
    "website": ["name", "url"],
    "article": ["headline", "author", "datepublished"],
    "blogposting": ["headline", "author", "datepublished"],
    "product": ["name", "image"],
    "localbusiness": ["name", "address"],
    "faqpage": ["mainentity"],
    "breadcrumblist": ["itemlistelement"],
}


class StructuredDataAnalyzer:
    """Safely audits JSON-LD structured data syntax, schema types, and required field completeness."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
    ) -> tuple[StructuredDataAssessment, list[TechnicalSEOFinding]]:
        """Validate JSON-LD structured data entries without executing code or dereferencing external contexts."""
        if not pages:
            return StructuredDataAssessment(), []

        findings: list[TechnicalSEOFinding] = []
        total_schemas = 0
        valid_json = 0
        syntax_errors = 0
        schema_types_found: set[str] = set()
        missing_fields_list: list[dict[str, Any]] = []
        evidence_ids = pages[0].source_evidence_ids[:3]

        for p in pages:
            for item in p.structured_data:
                total_schemas += 1

                # Safe dict conversion / validation
                schema_dict: dict[str, Any] = {}
                if isinstance(item, dict):
                    schema_dict = item
                    valid_json += 1
                elif isinstance(item, str):
                    try:
                        # Enforce length limit on raw JSON string to prevent parsing DoS
                        if len(item) > 200_000:
                            syntax_errors += 1
                            continue
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            schema_dict = parsed
                            valid_json += 1
                        else:
                            syntax_errors += 1
                            continue
                    except Exception as exc:
                        syntax_errors += 1
                        findings.append(
                            TechnicalSEOFinding(
                                finding_id="TS-STR-SYNTAX",
                                title="خطأ بناء جملة في كود البيانات المنظمة JSON-LD (JSON-LD Syntax Error)",
                                category="structured_data",
                                description=f"تعذر تحليل نص JSON-LD لاحتوائه على خلل تركيبي: {str(exc)[:100]}",
                                page_url=p.requested_url,
                                source_excerpt=item[:100],
                                evidence_ids=p.source_evidence_ids[:2],
                                observation_type="observed",
                                severity="high",
                                confidence_category="measured",
                                potential_technical_impact="تجاهل محركات البحث للبيانات المنظمة تماماً وفقدان فرصة المقتطفات الغنية.",
                                recommended_action="تصحيح أخطاء الفواصل والأقواس في كود JSON-LD والتحقق منه بأداة فحص النتائج الغنية.",
                            )
                        )
                        continue

                # Type recognition
                stype = schema_dict.get("@type", "")
                if isinstance(stype, list) and stype:
                    stype = stype[0]
                if not isinstance(stype, str) or not stype.strip():
                    findings.append(
                        TechnicalSEOFinding(
                            finding_id="TS-STR-NOTYPE",
                            title="غياب حقل النوع @type في البيانات المنظمة (Missing @type Field)",
                            category="structured_data",
                            description=f"كائن JSON-LD يفتقر إلى تحديد نوع Schema عبر حقل @type في الصفحة: '{p.requested_url}'",
                            page_url=p.requested_url,
                            evidence_ids=p.source_evidence_ids[:2],
                            observation_type="observed",
                            severity="medium",
                            confidence_category="measured",
                            potential_technical_impact="تعذر تصنيف الكائن بواسطة روبوتات الفهرسة.",
                            recommended_action="تضمين نوع Schema صالح، مثل: '@type': 'Organization'.",
                        )
                    )
                    continue

                clean_type = stype.strip()
                schema_types_found.add(clean_type)
                lower_type = clean_type.lower()

                # Check required fields for supported Google rich result types
                req_fields = SUPPORTED_SCHEMA_REQUIREMENTS.get(lower_type)
                if req_fields:
                    dict_keys_lower = {str(k).lower(): k for k in schema_dict.keys()}
                    missing = [rf for rf in req_fields if rf not in dict_keys_lower]
                    if missing:
                        missing_fields_list.append(
                            {"page_url": p.requested_url, "type": clean_type, "missing": missing}
                        )
                        findings.append(
                            TechnicalSEOFinding(
                                finding_id=f"TS-STR-REQ-{clean_type.upper()}",
                                title=f"حقول أساسية مفقودة في مخطط {clean_type} (Missing Required Schema Fields)",
                                category="structured_data",
                                description=f"مخطط {clean_type} يفتقر إلى حقول يوصى بها لمحركات البحث: {', '.join(missing)}",
                                page_url=p.requested_url,
                                source_excerpt=json.dumps(schema_dict, ensure_ascii=False)[:120],
                                evidence_ids=p.source_evidence_ids[:2],
                                observation_type="derived",
                                severity="medium",
                                confidence_category="derived",
                                potential_technical_impact="عدم تأهل الصفحة للميزات والنتائج الغنية (Rich Results) في Google Search.",
                                recommended_action=f"إضافة الحقول المطلوبة ({', '.join(missing)}) داخل كائن JSON-LD.",
                            )
                        )

        assessment = StructuredDataAssessment(
            total_schemas_found=total_schemas,
            valid_json_count=valid_json,
            syntax_error_count=syntax_errors,
            schema_types=sorted(list(schema_types_found)),
            missing_required_fields=missing_fields_list,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
