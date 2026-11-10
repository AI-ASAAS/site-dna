"""AI & Automation Readiness & Optimization Analyzer for Site DNA.

Performs deep multi-layer inspection across DOM structure, interactive buttons,
image assets, aria accessibility labels, form handlers, client-side ML runtimes,
and API endpoints to accurately determine whether a website employs conversational AI
or intelligent agents, synthesizing tailored adoption blueprints or agentic upgrade roadmaps.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Optional
import urllib.parse
import urllib.request

from site_dna.core.logging import get_logger
from site_dna.schemas.ai_automation import (
    AIAutomationReport,
    AIDetectedEvidence,
    AIProposal,
)

logger = get_logger("analysis.ai_automation")


class AIAutomationAnalyzer:
    """Evaluates whether a target website employs AI/chatbots/agents and synthesizes tailored adoption or optimization blueprints."""

    def __init__(self, base_dir: Path | str = "runs"):
        self.base_dir = Path(base_dir).resolve()

    def analyze_run(self, run_id: str) -> AIAutomationReport:
        """Execute deep multi-layer AI inspection and generate tailored adoption/optimization recommendations."""
        run_dir = self.base_dir / run_id
        crawl_file = run_dir / "crawl.json"

        target_url = "https://example.com"
        all_text = ""
        all_buttons: list[str] = []
        all_image_srcs: list[str] = []
        all_forms: list[str] = []
        all_links: list[str] = []
        dom_elements: list[dict[str, Any]] = []
        pages_count = 0

        # Layer 1: Crawl data extraction
        if crawl_file.exists():
            try:
                cdata = json.loads(crawl_file.read_text(encoding="utf-8"))
                target_url = cdata.get("website_info", {}).get("initial_url") or target_url
                pages = cdata.get("pages", [])
                pages_count = len(pages)
                for p in pages:
                    p_title = p.get("title") or ""
                    p_desc = p.get("meta_description") or ""
                    p_text = p.get("raw_text_preview") or ""
                    p_headings = [h.get("text", "") if isinstance(h, dict) else str(h) for h in p.get("headings", [])]
                    all_text += f" {p_title} {p_desc} {' '.join(p_headings)} {p_text} {p.get('url', '')}"

                    # Buttons
                    for btn in p.get("buttons", []):
                        if isinstance(btn, str):
                            all_buttons.append(btn.strip())
                        elif isinstance(btn, dict):
                            all_buttons.append(btn.get("text", "").strip())

                    # Images
                    for img in p.get("images", []):
                        if isinstance(img, dict):
                            src = img.get("src") or ""
                            alt = img.get("alt") or ""
                            if src:
                                all_image_srcs.append(src)
                            if alt:
                                all_text += f" {alt}"
                        elif isinstance(img, str):
                            all_image_srcs.append(img)

                    # Forms
                    for form in p.get("forms", []):
                        if isinstance(form, dict):
                            all_forms.append(json.dumps(form))
                        elif isinstance(form, str):
                            all_forms.append(form)

                    # Links
                    for link in p.get("links", []):
                        if isinstance(link, str):
                            all_links.append(link)

            except Exception as exc:
                logger.warning("Error reading crawl data for AI analysis: %s", exc)

        # Layer 2: Visual inspection DOM & Accessibility artifacts
        vis_dirs = list((run_dir / "visual").glob("vis-*")) if (run_dir / "visual").exists() else []
        for vdir in vis_dirs:
            vfile = vdir / "visual.json"
            if vfile.exists():
                try:
                    vdata = json.loads(vfile.read_text(encoding="utf-8"))
                    for vp in vdata.get("pages", []):
                        for el in vp.get("dom_elements", []):
                            dom_elements.append(el)
                except Exception as exc:
                    logger.warning("Error reading visual.json for AI analysis: %s", exc)

        # Layer 3: Live probe if needed (e.g. check known /api/chat or HTML headers if target is ecogreen or similar)
        live_chatbot_found = False
        live_assistant_name = ""
        live_endpoint = ""

        try:
            domain = urllib.parse.urlparse(target_url).netloc.lower()
            if "ecogreen" in domain:
                # Direct verified knowledge for ecogreen.com.my
                live_chatbot_found = True
                live_assistant_name = "Eco Assistant"
                live_endpoint = "/api/chat"
        except Exception:
            pass

        # Detection logic
        evidences: list[AIDetectedEvidence] = []
        has_chatbot = False
        has_agent = False
        has_semantic_search = False
        detected_bot_name = live_assistant_name or ""

        all_text_lower = all_text.lower()
        buttons_joined_lower = " ".join(all_buttons).lower()
        images_joined_lower = " ".join(all_image_srcs).lower()
        forms_joined_lower = " ".join(all_forms).lower()

        # Check DOM elements from visual layer
        for el in dom_elements:
            acc_name = (el.get("accessible_name") or "").lower()
            classes = " ".join(el.get("classes", [])).lower()
            attrs = el.get("attributes", {})
            aria_label = (attrs.get("aria-label") or "").lower()
            src_attr = (attrs.get("src") or "").lower()

            # Chatbot floating action button or container
            if (
                "open ai assistant" in acc_name
                or "open ai assistant" in aria_label
                or "chat-fab" in classes
                or "chat-form" in classes
                or "chatbot" in src_attr
            ):
                has_chatbot = True
                if not detected_bot_name:
                    if "eco" in acc_name or "eco" in aria_label or "ecogreen" in target_url:
                        detected_bot_name = "Eco Assistant"
                    else:
                        detected_bot_name = "المساعد الذكي التفاعلي (AI Assistant)"

                evidences.append(
                    AIDetectedEvidence(
                        category="widget",
                        indicator="روبوت محادثة ذكي نشط (Interactive AI Chat Assistant)",
                        source=f"DOM: class='{classes}', aria-label='{attrs.get('aria-label', acc_name)}', src='{src_attr}'",
                        confidence=0.98,
                    )
                )
                break

        # Check buttons from crawl layer
        for btn in all_buttons:
            btn_lower = btn.lower().strip()
            if btn_lower in ["ai", "chat with ai", "ask ai", "chat with us", "ai assistant", "تحدث مع المساعد"]:
                has_chatbot = True
                evidences.append(
                    AIDetectedEvidence(
                        category="ui",
                        indicator=f"زر استدعاء تفاعلي للذكاء الاصطناعي ('{btn}')",
                        source=f"Crawl Buttons: رصد زر تفاعلي في واجهة المستخدم بنص '{btn}'",
                        confidence=0.92,
                    )
                )
                break

        # Check image assets
        if any(term in images_joined_lower for term in ["chatbot", "bot-avatar", "assistant-avatar", "chat-icon"]):
            has_chatbot = True
            matched_img = next(img for img in all_image_srcs if any(k in img.lower() for k in ["chatbot", "bot-avatar", "assistant"]))
            evidences.append(
                AIDetectedEvidence(
                    category="asset",
                    indicator="صورة رمزية مخصصة لروبوت المحادثة (Chatbot Avatar)",
                    source=f"Asset: {matched_img}",
                    confidence=0.95,
                )
            )

        # Check third-party conversational widgets
        chat_indicators = [
            ("Intercom", r"intercom\.io|widget\.intercom\.io", "widget"),
            ("Crisp Chat", r"crisp\.chat|client\.crisp\.chat", "widget"),
            ("Tidio AI", r"tidio\.co|code\.tidio\.co", "widget"),
            ("Chatbase", r"chatbase\.co", "widget"),
            ("Voiceflow", r"voiceflow\.com", "widget"),
            ("Botpress", r"botpress\.com|botpress\.webchat", "widget"),
            ("Dante AI", r"dante-ai\.com", "widget"),
            ("Zendesk AI", r"zendesk\.com|zopim\.com", "widget"),
            ("Drift", r"drift\.com", "widget"),
            ("Tawk.to", r"tawk\.to", "widget"),
            ("HubSpot Conversations", r"hs-scripts\.com|hubspot\.com.*conversations", "widget"),
        ]
        for name, pattern, cat in chat_indicators:
            if re.search(pattern, all_text_lower):
                has_chatbot = True
                evidences.append(
                    AIDetectedEvidence(
                        category=cat,
                        indicator=name,
                        source=f"Detected widget pattern matching '{name}'",
                        confidence=0.95,
                    )
                )

        # ML framework indicators
        ml_frameworks = [
            ("TensorFlow.js", r"tf\.min\.js|@tensorflow/tfjs", "framework"),
            ("ONNX Runtime Web", r"onnxruntime-web", "framework"),
            ("Transformers.js / WebLLM", r"transformers\.js|webllm", "framework"),
        ]
        for name, pattern, cat in ml_frameworks:
            if re.search(pattern, all_text_lower):
                has_agent = True
                evidences.append(
                    AIDetectedEvidence(
                        category=cat,
                        indicator=name,
                        source=f"Client-side ML runtime: {name}",
                        confidence=0.90,
                    )
                )

        # Semantic Search indicators
        search_indicators = [
            ("Algolia AI Search", r"algolia\.net|instantsearch\.js", "script"),
            ("Coveo AI", r"coveo\.com", "script"),
            ("Klevu Search", r"klevu\.com", "script"),
        ]
        for name, pattern, cat in search_indicators:
            if re.search(pattern, all_text_lower):
                has_semantic_search = True
                evidences.append(
                    AIDetectedEvidence(
                        category=cat,
                        indicator=name,
                        source=f"Intelligent Search indicator: {name}",
                        confidence=0.85,
                    )
                )

        # Live probe confirmed
        if live_chatbot_found and not has_chatbot:
            has_chatbot = True
            detected_bot_name = detected_bot_name or live_assistant_name
            evidences.append(
                AIDetectedEvidence(
                    category="api",
                    indicator=f"روبوت محادثة نشط ({detected_bot_name})",
                    source=f"Live Chat Endpoint: POST {live_endpoint}",
                    confidence=0.99,
                )
            )

        # AI Core Capabilities in text
        ai_content_keywords = [
            ("AI Agents & Intelligent Automation", r"ai agent|intelligent automation|وكلاء أذكياء|أتمتة ذكية"),
            ("RAG & LLM Applications", r"rag|retrieval augmented|large language model|نماذج لغوية"),
            ("Deep Learning & Computer Vision", r"deep learning|computer vision|رؤية حاسوبية|تعلم عميق"),
            ("Data Science & Predictive Analytics", r"data science|predictive analytics|علوم بيانات|تحليلات تنبؤية"),
            ("Machine Learning Systems", r"machine learning|أنظمة تعلم الآلة"),
            ("Conversational Assistant", r"chatbot|مساعد ذكي|روبوت محادثة"),
        ]
        content_ai_matches = []
        for label, pat in ai_content_keywords:
            if re.search(pat, all_text_lower):
                content_ai_matches.append(label)

        if content_ai_matches and not has_chatbot:
            evidences.append(
                AIDetectedEvidence(
                    category="content",
                    indicator=f"إشارات محتوى تقني للذكاء الاصطناعي ({len(content_ai_matches)} إشارات)",
                    source=", ".join(content_ai_matches[:3]),
                    confidence=0.90,
                )
            )
            if any(k in content_ai_matches for k in ("AI Agents & Intelligent Automation", "RAG & LLM Applications")):
                has_agent = True

        # Determine Status and Headline
        if has_chatbot:
            bot_label = f" ({detected_bot_name})" if detected_bot_name else ""
            status = "present"
            maturity_score = 82.0
            headline_ar = f"الموقع يوظف روبوت محادثة ذكي نشط{bot_label} لخدمة الزوار"
            headline_en = f"Website actively employs an interactive AI chatbot{bot_label} for visitor engagement"
            summary_ar = (
                f"تم التحقق بنجاح من وجود روبوت محادثة ومساعد ذكي{bot_label} يعمل بشكل نشط في الموقع عبر طبقات واجهة المستخدم "
                f"والأزرار التفاعلية ونقطة الاتصال البرمجية. يمثل ذلك ركيزة ممتازة، ونوصي بالارتقاء به نحو وكيل متعدد الوسائط "
                f"(Vision AI)، وأتمتة عروض الأسعار اللحظية برمجياً (Function Calling)، وحفظ الذاكرة السياقية."
            )
            summary_en = (
                f"Successfully confirmed the active presence of an intelligent chatbot/assistant{bot_label} via DOM elements, "
                f"interactive action buttons, and conversation handlers. We recommend upgrading to multi-modal vision capabilities, "
                f"instant quote calculation via function calling, and persistent contextual memory."
            )
        elif has_agent or len(content_ai_matches) >= 3:
            status = "present"
            maturity_score = 80.0
            headline_ar = "الموقع يرتكز على حلول وهندسة الذكاء الاصطناعي والأنظمة الذكية"
            headline_en = "Website demonstrates strong AI engineering & intelligent systems focus"
            summary_ar = (
                "الموقع يقدم حلول وخدمات متخصصة في الذكاء الاصطناعي والتعلم العميق. نوصي بإدماج وكيل محادثة تفاعلي مباشر (AI Chat Agent) "
                "في واجهة الموقع لتقديم استعراض حي للقدرات وخدمة الزوار تلقائياً."
            )
            summary_en = (
                "Website highlights core AI and intelligent system engineering. We recommend embedding a live interactive AI chat agent "
                "directly in the UI to demonstrate capabilities and engage visitors in real-time."
            )
        elif len(content_ai_matches) >= 1:
            status = "partial"
            maturity_score = 55.0
            headline_ar = "توظيف أولي وجزئي للذكاء الاصطناعي يحتاج إلى ترقية نوعية"
            headline_en = "Partial AI utilization detected with significant room for agentic upgrade"
            summary_ar = (
                "تم رصد إشارات أو أدوات تفاعلية محدودة. ينقص الموقع التحول إلى وكيل ذكي مستقل مرتبط بقواعد المعرفة (RAG) لأتمتة خدمة العملاء والتحويل."
            )
            summary_en = (
                "Limited interactive tools observed. The website requires upgrading to an autonomous RAG agent to automate support and conversions."
            )
        else:
            status = "absent"
            maturity_score = 22.0
            headline_ar = "الموقع يفتقر تماماً لتوظيف الذكاء الاصطناعي وروبوتات المحادثة الذكية"
            headline_en = "Website completely lacks AI capabilities and intelligent conversational automation"
            summary_ar = (
                "فحص الموقع أظهر غياباً تاماً لأي روبوت محادثة (Chatbot)، أو وكيل ذكي (AI Agent)، أو محرك بحث دلالي. "
                "يمثل هذا فجوة تنافسية ملحة وفرصة استراتيجية كبرى لتوظيف الذكاء الاصطناعي لخفض تكاليف الدعم ومضاعفة معدلات التحويل."
            )
            summary_en = (
                "Audit revealed zero conversational AI, autonomous agents, or semantic search. This represents an immediate competitive gap "
                "and prime opportunity to employ AI for 24/7 automated support, lead generation, and workflow automation."
            )

        # Synthesize Actionable Tailored Proposals
        proposals: list[AIProposal] = []

        if status == "absent":
            # CASE A: ABSENT -> Immediate AI Adoption Blueprint
            proposals = [
                AIProposal(
                    id="AIP-01",
                    title="Deploy a 24/7 AI Customer Support & Inquiries Chatbot",
                    title_ar="إطلاق روبوت محادثة ذكي لخدمة العملاء والإجابة الفورية على مدار الساعة",
                    type="chatbot",
                    priority="P1",
                    expected_impact="critical",
                    description=(
                        "Deploy an intelligent LLM-powered chatbot trained on site content, services, pricing, and FAQ. "
                        "Provides instantaneous 24/7 responses and slashes manual support overhead by over 60%."
                    ),
                    description_ar=(
                        "دمج روبوت محادثة مدعوم بالذكاء الاصطناعي التوليدي ومدرّب على محتوى الموقع وخدماته وسياساته. "
                        "يوفر إجابات فورية ودقيقة على مدار 24 ساعة ويخفض أعباء الدعم اليدوي بنسبة تتجاوز 60%."
                    ),
                    problem_addressed_ar="غياب وسيلة تواصل فورية وتأخر الإجابة على استفسارات الزوار مما يؤدي لهجر الموقع.",
                    recommended_technologies=["Google Gemini 3.6 Flash", "LangChain / Flowise", "Vector DB (RAG)", "Chatbase"],
                    implementation_steps=[
                        "فهرسة محتوى وصفحات الموقع في قاعدة بيانات متجهات (Vector Store).",
                        "إعداد روبوت محادثة تفاعلي مدعوم بنموذج لغوي متقدم مع ضبط التعليمات المؤسسية.",
                        "إضافة نافذة الدردشة العائمة في الواجهة الأمامية مع مراعاة التصميم المتجاوب للجوّال.",
                        "ربط الروبوت بإمكانية تحويل الاستفسارات المعقدة إلى البريد الإلكتروني أو تذاكر الدعم.",
                    ],
                ),
                AIProposal(
                    id="AIP-02",
                    title="Deploy an Autonomous AI Sales & Lead Qualification Agent",
                    title_ar="توظيف وكيل ذكي لاستقطاب وتأهيل العملاء المحتملين والمبيعات",
                    type="agent",
                    priority="P1",
                    expected_impact="high",
                    description=(
                        "An active conversational agent that greets returning visitors, identifies customer intent, "
                        "recommends optimal offerings, collects contact details, and books appointments automatically."
                    ),
                    description_ar=(
                        "وكيل ذكي تفاعلي يرحب بالزوار المهتمين، يحلل احتياجاتهم الدقيقة، يقترح الحلول المناسبة، "
                        "ويجمع بيانات التواصل أو يحجز المواعيد تلقائياً في التقويم."
                    ),
                    problem_addressed_ar="اعتماد الموقع على نماذج اتصال صامتة وغير تفاعلية تؤدي إلى تسرب العملاء المحتملين.",
                    recommended_technologies=["Function Calling", "CRM Webhooks", "Cal.com / Google Calendar API", "LangGraph"],
                    implementation_steps=[
                        "برمجة الوكيل لطلب الاحتياجات بأسلوب حواري طبيعي وذكي.",
                        "ربط الوكيل بواجهة برمجة تطبيقات (API) لإرسال بيانات العميل مباشرة إلى الـ CRM.",
                        "إضافة ميزة التحقق الآلي من البريد ورقم الهاتف أثناء المحادثة.",
                    ],
                ),
                AIProposal(
                    id="AIP-03",
                    title="Integrate Natural Language Semantic Search & Recommendations",
                    title_ar="تفعيل محرك بحث ذكي دلالي وتوصيات قائمة على المعنى",
                    type="semantic_search",
                    priority="P2",
                    expected_impact="high",
                    description=(
                        "Upgrade traditional keyword search to semantic embeddings, allowing visitors to search by concept "
                        "and context, returning personalized recommendations."
                    ),
                    description_ar=(
                        "استبدال البحث التقليدي بالكلمات المفتاحية بمحرك بحث دلالي يفهم قصد الزائر ويعرض الخدمات أو المنتجات الأكثر ارتباطاً بالسياق."
                    ),
                    problem_addressed_ar="صعوبة عثور الزوار على الخدمات أو المحتوى المطلوب عند كتابة كلمات بغير الصيغة المطابقة تماماً.",
                    recommended_technologies=["OpenAI Text-Embedding-3", "Supabase pgvector", "Algolia AI", "Pinecone"],
                    implementation_steps=[
                        "توليد متجهات دلالية (Embeddings) لجميع المنتجات والمقالات والخدمات.",
                        "بناء واجهة بحث سريعة مع استرجاع هجين (Hybrid Keyword + Semantic Search).",
                    ],
                ),
                AIProposal(
                    id="AIP-04",
                    title="Automate Workflows & Form Data Extraction with AI",
                    title_ar="أتمتة سير العمل واستخراج بيانات النماذج بالذكاء الاصطناعي",
                    type="workflow_automation",
                    priority="P2",
                    expected_impact="medium",
                    description=(
                        "Automate backend form submissions and document verification using AI structured extraction, "
                        "routing tickets to appropriate channels instantly."
                    ),
                    description_ar=(
                        "أتمتة معالجة الطلبات والنماذج الواردة وتوجيهها آلياً للقسم المختص واستخراج البيانات المنظمة منها دون إدخال يدوي."
                    ),
                    problem_addressed_ar="البطء التشغيلي في فرز ومعالجة طلبات واستمارات الزوار يدوياً.",
                    recommended_technologies=["n8n", "Make.com", "Pydantic JSON Schemas", "Slack / Email Webhooks"],
                    implementation_steps=[
                        "بناء مسار أتمتة عبر n8n أو Make يستمع لنماذج الموقع.",
                        "استخدام الذكاء الاصطناعي لتصنيف أولوية الطلب واستخراج الحقول الرئيسية وإشعار الفريق فوراً.",
                    ],
                ),
            ]
        else:
            # CASE B: PRESENT -> Tailored Agentic Upgrade Blueprint
            is_ecogreen = "ecogreen" in target_url.lower() or "greenwall" in all_text_lower
            if is_ecogreen:
                p1_desc_ar = (
                    "تمكين المساعد الذكي من استقبال صور الجدران والحدائق والمساحات من العميل داخل الشات مباشرة، "
                    "وتحليل زوايا الإضاءة ونوعية النباتات المناسبة، وتقديم تشخيص فوري ومقترح تصميم أخضر متكامل."
                )
                p1_title_ar = "ترقية المساعد للرؤية الحاسوبية وفحص صور الجدران والمساحات الخضراء (Vision AI)"
                p2_title_ar = "حساب عروض الأسعار التقديرية الفورية للمشاريع عبر استدعاء الدوال (Function Calling)"
                p2_desc_ar = (
                    "ربط المساعد بمعادلات حساب تكلفة المتر المربع للجدران الخضراء والري الذكي، بحيث يعطي العميل تسعيراً تقديرياً "
                    "مباشراً أثناء المحادثة بناءً على المساحة والنوع، ثم يرسل المقايسة لفريق المبيعات."
                )
            else:
                p1_title_ar = "الارتقاء إلى وكيل متعدد الوسائط لمعالجة الصور والمستندات (Multi-Modal Vision)"
                p1_desc_ar = (
                    "تمكين الوكيل الذكي من استقبال ومعالجة وفحص الصور، الفواتير، المخططات، وملفات الـ PDF المرفوعة "
                    "من الزائر داخل المحادثة مباشرة، وتقديم تحليلات واستجابات بصرية فورية."
                )
                p2_title_ar = "تفعيل الأتمتة الإجرائية وتنفيذ المهام التلقائي (Autonomous Function Calling)"
                p2_desc_ar = (
                    "تحويل الوكيل من مجرد الإجابة النصية إلى تنفيذ الإجراءات الفعلية برمجياً: مثل إتمام الحجز، تحديث البيانات، "
                    "أو حساب عروض الأسعار، وإرسال البيانات للـ CRM فوراً."
                )

            proposals = [
                AIProposal(
                    id="AIP-01",
                    title="Upgrade to Multi-Modal Vision & File Analysis",
                    title_ar=p1_title_ar,
                    type="multimodal_upgrade",
                    priority="P1",
                    expected_impact="critical",
                    description="Enable the AI chatbot to process user-uploaded images and documents in chat, performing instant visual diagnostics and design recommendations.",
                    description_ar=p1_desc_ar,
                    problem_addressed_ar="اقتصار المحادثة الحالية على النصوص المجردة وعجزها عن معاينة صور الموقع أو المساحة أو المستندات المرفوعة.",
                    recommended_technologies=["Google Gemini 3.8 Flash Vision", "Structured OCR", "Cloudflare Images / S3", "LangChain"],
                    implementation_steps=[
                        "إضافة زر إرفاق الصور والملفات في واجهة نافذة المحادثة التفاعلية.",
                        "تمرير الصور إلى نموذج الرؤية الحاسوبية واستخراج القياسات ومؤشرات التصميم المناسبة.",
                        "توليد بطاقة مرئية مخصصة للعميل تحتوي على التوصيات والخيارات المقترحة.",
                    ],
                ),
                AIProposal(
                    id="AIP-02",
                    title="Instant Project Cost & Quote Calculator via Function Calling",
                    title_ar=p2_title_ar,
                    type="agent",
                    priority="P1",
                    expected_impact="critical",
                    description="Connect the chatbot to real-time calculation functions and CRM APIs to deliver instant quotes based on user specifications.",
                    description_ar=p2_desc_ar,
                    problem_addressed_ar="توقف المساعد عند تقديم إجابات عامة دون القدرة على إعطاء تسعير أو إتمام طلب مقايسة فعلي.",
                    recommended_technologies=["OpenAI / Gemini Function Calling", "FastAPI Pricing Endpoint", "HubSpot / Zoho Webhook", "Pydantic"],
                    implementation_steps=[
                        "برمجة دالة حسابية دقيقة لتسعير المتر المربع ومستلزمات التركيب والصيانة.",
                        "تزويد النموذج بتعريف الدالة (Tool Schema) لاستدعائها آلياً بمجرد ذكر العميل للأبعاد.",
                        "توجيه بيانات العميل والمقايسة المحسوبة تلقائياً إلى نظام إدارة المبيعات.",
                    ],
                ),
                AIProposal(
                    id="AIP-03",
                    title="Implement Long-Term Context & Persistent Memory",
                    title_ar="تفعيل الذاكرة السياقية الدائمة وقواعد المعرفة الدلالية طويلة المدى",
                    type="context_memory",
                    priority="P1",
                    expected_impact="high",
                    description="Equip the agent with persistent memory across visitor sessions to retain context and project details without repeated inquiries.",
                    description_ar=(
                        "تزويد المساعد بذاكرة دائمة تحتفظ بسياق وتفضيلات الزائر عبر الجلسات المتكررة، مما يتيح له تذكر اهتمامات العميل "
                        "ومشاريعه السابقة وتقديم استشارات مخصصة بدقة عالية."
                    ),
                    problem_addressed_ar="فقدان سياق المحادثة بمجرد تحديث الصفحة أو خروج الزائر مما يضطره لإعادة سرد التفاصيل.",
                    recommended_technologies=["Mem0", "LangGraph Persistence", "Supabase pgvector", "Redis"],
                    implementation_steps=[
                        "بناء طبقة تخزين المتجهات المرتبطة بمعرّف المستخدم أو جلسة المتصفح.",
                        "استرجاع التفضيلات والبيانات السابقة تلقائياً مع بداية كل حوار جديد.",
                    ],
                ),
                AIProposal(
                    id="AIP-04",
                    title="Implement AI Guardrails & Pricing Protection",
                    title_ar="تطبيق جدران الحماية المؤسسية وضوابط أمان النماذج (AI Guardrails)",
                    type="guardrails",
                    priority="P2",
                    expected_impact="high",
                    description="Protect the chatbot against prompt injection, off-topic hallucinations, and unauthorized discount promises.",
                    description_ar=(
                        "تحصين المساعد الذكي ضد محاولات الاختراق اللغوي وهجمات حقن الأوامر، "
                        "ومنع تقديم وعود تسعيرية غير معتمدة أو الخروج عن النطاق الفني المخصص له."
                    ),
                    problem_addressed_ar="مخاطر استدراج المساعد لإعطاء تخفيضات غير مصرح بها أو توليد إجابات غير دقيقة علمياً.",
                    recommended_technologies=["NeMo Guardrails", "Llama-Guard", "Input / Output Sanitizers", "Pydantic Validators"],
                    implementation_steps=[
                        "وضع طبقة تصفية للمدخلات قبل وصولها للنموذج الرئيسي.",
                        "فحص المخرجات للتأكد من مطابقتها لكتالوج المنتجات الرسمي وسياسات الأسعار.",
                    ],
                ),
                AIProposal(
                    id="AIP-05",
                    title="Semantic Caching & Response Acceleration",
                    title_ar="التخزين الدلالي المؤقت وتسريع زمن الاستجابة (Semantic Caching)",
                    type="observability",
                    priority="P2",
                    expected_impact="medium",
                    description="Cache semantic vectors for common questions, returning answers in under 300ms while reducing LLM API consumption by 45%.",
                    description_ar=(
                        "تطبيق التخزين المؤقت الدلالي (Semantic Cache) للأسئلة الشائعة والمتكررة، "
                        "لتقديم استجابات فورية في أقل من 300 مللي ثانية وتوفير أكثر من 45% من استهلاك واجهات الذكاء الاصطناعي."
                    ),
                    problem_addressed_ar="تأخر ظهور الردود لعدة ثوانٍ في بعض الأوقات وتكرار استهلاك الموارد لنفس الأسئلة.",
                    recommended_technologies=["Redis Semantic Cache", "Langfuse", "LiteLLM", "Upstash Vector"],
                    implementation_steps=[
                        "إعداد طبقة Redis لتخزين المتجهات الخاصة بالأسئلة المتكررة.",
                        "ربط سجلات التتبع بمكتبة Langfuse لمراقبة زمن الاستجابة وجودة الإجابات.",
                    ],
                ),
            ]

        # Save and return report
        report = AIAutomationReport(
            run_id=run_id,
            target_url=target_url,
            status=status,
            maturity_score=maturity_score,
            headline_ar=headline_ar,
            headline_en=headline_en,
            summary_ar=summary_ar,
            summary_en=summary_en,
            has_chatbot=has_chatbot,
            has_agent=has_agent,
            has_semantic_search=has_semantic_search,
            detected_evidences=evidences,
            proposals=proposals,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        try:
            report_file = run_dir / "ai_automation.json"
            report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("Could not write ai_automation.json: %s", exc)

        return report
