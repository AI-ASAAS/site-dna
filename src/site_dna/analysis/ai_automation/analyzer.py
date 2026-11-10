"""AI & Automation Readiness & Optimization Analyzer for Site DNA."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Optional

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
        """Execute AI presence inspection and generate tailored adoption/optimization recommendations."""
        run_dir = self.base_dir / run_id
        crawl_file = run_dir / "crawl.json"

        target_url = "https://example.com"
        all_text = ""
        all_scripts = []
        all_headings = []
        pages_count = 0

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
                    all_headings.extend(p_headings)
                    all_text += f" {p_title} {p_desc} {' '.join(p_headings)} {p_text} {p.get('url', '')}"
                    for link in p.get("links", []):
                        all_text += f" {link}"
            except Exception as exc:
                logger.warning("Error reading crawl data for AI analysis: %s", exc)

        all_text_lower = all_text.lower()

        # 1. Detection Indicators
        evidences: list[AIDetectedEvidence] = []
        has_chatbot = False
        has_agent = False
        has_semantic_search = False

        # Chatbot widgets indicators
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
            ("Custom Interactive Chatbot", r"id=[\"']chat-widget|class=[\"']ai-assistant|aria-label=[\"']chatbot", "widget"),
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

        # AI & ML framework indicators
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

        # Content indicators: AI Services, AI Engineering, AI Products, RAG, Agents
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

        if content_ai_matches:
            evidences.append(
                AIDetectedEvidence(
                    category="content",
                    indicator=f"AI Core Capabilities ({len(content_ai_matches)} signals)",
                    source=", ".join(content_ai_matches[:3]),
                    confidence=0.92,
                )
            )
            if any(k in content_ai_matches for k in ("AI Agents & Intelligent Automation", "RAG & LLM Applications")):
                has_agent = True

        # 2. Determine Status and Maturity Score
        if has_chatbot and has_agent:
            status = "present"
            maturity_score = 88.0
            headline_ar = "الموقع يوظف تقنيات الذكاء الاصطناعي والوكلاء الأذكياء بنجاح"
            headline_en = "Website actively leverages AI technologies and intelligent agents"
            summary_ar = (
                "تم رصد توظيف متقدم للذكاء الاصطناعي والميزات الذكية في الموقع. نوصي بالارتقاء بالمنظومة نحو الوكلاء متعددي الوسائط "
                "(Multi-Modal)، وتفعيل الأتمتة الإجرائية، وتعزيز الذاكرة السياقية الدائمة لتعظيم العائد والإنتاجية."
            )
            summary_en = (
                "Advanced AI capabilities and intelligent agent patterns were identified. We recommend upgrading to multi-modal "
                "capabilities, autonomous action execution, and persistent contextual memory."
            )
        elif has_chatbot or has_agent or len(content_ai_matches) >= 2:
            status = "partial" if not (has_chatbot and has_agent) else "present"
            if len(content_ai_matches) >= 3:
                status = "present"
                maturity_score = 82.0
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
            else:
                maturity_score = 58.0
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
            maturity_score = 24.0
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

        # 3. Formulate Actionable Tailored Proposals
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
            # CASE B: PRESENT or PARTIAL -> Advanced AI Optimization & Agentic Blueprint
            proposals = [
                AIProposal(
                    id="AIP-01",
                    title="Upgrade to Multi-Modal AI Agent Capabilities (Vision & Documents)",
                    title_ar="الارتقاء إلى وكلاء متعددي الوسائط لمعالجة الصور والمستندات والصوت",
                    type="multimodal_upgrade",
                    priority="P1",
                    expected_impact="critical",
                    description=(
                        "Enable AI agents to accept, inspect, and reason over images, invoices, diagrams, and PDF files "
                        "uploaded by users directly in chat, delivering instantaneous visual diagnostics."
                    ),
                    description_ar=(
                        "تمكين الوكلاء الأذكياء من استقبال ومعالجة وفحص الصور، الفواتير، المخططات، وملفات الـ PDF المرفوعة "
                        "من الزائر داخل المحادثة مباشرة، وتقديم تحليلات واستجابات بصرية فورية."
                    ),
                    problem_addressed_ar="اقتصار التفاعل الذكي الحالي على النصوص المجردة وعجزه عن فهم المدخلات البصرية والمستندية.",
                    recommended_technologies=["Google Gemini 3.8 Flash Vision", "Whisper Audio API", "PyMuPDF", "LangChain"],
                    implementation_steps=[
                        "إضافة زر رفع الملفات والصور في واجهة الدردشة والمساعد التفاعلي.",
                        "تغذية الصور والمستندات مباشرة إلى النموذج متعدد الوسائط واستخراج النتائج الهندسية والتحليلية.",
                        "عرض بطاقات مرئية تفاعلية للنتائج داخل المحادثة.",
                    ],
                ),
                AIProposal(
                    id="AIP-02",
                    title="Implement Long-Term Persistent Context & Vector Memory",
                    title_ar="تفعيل الذاكرة السياقية الدائمة وقواعد المعرفة الدلالية طويلة المدى",
                    type="context_memory",
                    priority="P1",
                    expected_impact="high",
                    description=(
                        "Equip the agent with episodic and persistent semantic memory across sessions so returning visitors "
                        "are recognized and served with personalized context without repeating information."
                    ),
                    description_ar=(
                        "تزويد الوكيل بذاكرة دائمة تحتفظ بسياق وتفضيلات الزائر عبر الجلسات المتكررة، مما يتيح له تذكر اهتمامات العميل "
                        "ومشاريعه السابقة وتقديم تجربة مخصصة بدرجة استثنائية."
                    ),
                    problem_addressed_ar="فقدان السياق بعد انتهاء كل جلسة مما يضطر العميل لتكرار تفاصيله في كل زيارة.",
                    recommended_technologies=["Mem0", "LangGraph Persistence", "Supabase pgvector", "Redis"],
                    implementation_steps=[
                        "بناء طبقة تخزين المتجهات المرتبطة بمعرّف المستخدم أو الجلسة.",
                        "استرجاع سياق التفضيلات السابقة تلقائياً مع بداية كل محادثة جديدة.",
                    ],
                ),
                AIProposal(
                    id="AIP-03",
                    title="Autonomous Tool Calling & Action Execution Framework",
                    title_ar="تفعيل الأتمتة الإجرائية وتنفيذ المهام التلقائي (Autonomous Function Calling)",
                    type="agent",
                    priority="P1",
                    expected_impact="critical",
                    description=(
                        "Transition the AI from passive conversationalist to active executor: allowing the agent to trigger API calls, "
                        "initiate bookings, update records, and run backend calculations securely."
                    ),
                    description_ar=(
                        "تحويل الوكيل من مجرد الإجابة النصية إلى تنفيذ الإجراءات الفعلية برمجياً: مثل إتمام الحجز، تحديث البيانات، "
                        "استدعاء دوال الحسابات، أو إرسال التقارير بضوابط تحقق أمنية محكمة."
                    ),
                    problem_addressed_ar="توقف الذكاء الاصطناعي عند تقديم المشورة النصية وعجزه عن إنجاز العمل الفعلي نيابة عن المستخدم.",
                    recommended_technologies=["Structured Outputs", "Pydantic Tool Definitions", "FastAPI Endpoints", "OAuth2"],
                    implementation_steps=[
                        "تعريف الأدوات والمهام بصيغة OpenAPI / JSON Schemas للنموذج.",
                        "تنفيذ دوال المعالجة مع طلب تأكيد بشري مسبق (Human-in-the-loop) للعمليات الحساسة.",
                    ],
                ),
                AIProposal(
                    id="AIP-04",
                    title="Implement AI Guardrails & Prompt Sandboxing",
                    title_ar="تطبيق جدران الحماية المؤسسية وضوابط أمان النماذج (AI Guardrails)",
                    type="guardrails",
                    priority="P2",
                    expected_impact="high",
                    description=(
                        "Protect the AI agent against prompt injection, jailbreaks, data exfiltration, and out-of-scope discussions, "
                        "guaranteeing brand safety and regulatory compliance."
                    ),
                    description_ar=(
                        "تحصين الوكيل الذكي ضد محاولات الاختراق اللغوي (Jailbreak) وهجمات حقن الأوامر (Prompt Injection)، "
                        "ومنع تسريب التعليمات الداخلية أو الخروج عن النطاق المهني المعتمد."
                    ),
                    problem_addressed_ar="مخاطر استغلال الوكيل الذكي لتوليد محتوى غير لائق أو إفشاء أسرار تسعيرية أو تجارية.",
                    recommended_technologies=["NeMo Guardrails", "Llama-Guard", "Input / Output Sanitizers", "Pydantic Validators"],
                    implementation_steps=[
                        "وضع طبقة تصفية للمدخلات قبل وصولها للنموذج الرئيسي.",
                        "فحص المخرجات للتأكد من عدم وجود بيانات سرية أو ألفاظ غير مقبولة.",
                    ],
                ),
                AIProposal(
                    id="AIP-05",
                    title="LLM Observability, Latency Caching & Cost Optimization",
                    title_ar="مراقبة أداء النماذج والتخزين الدلالي المؤقت وخفض التكلفة",
                    type="observability",
                    priority="P2",
                    expected_impact="medium",
                    description=(
                        "Track token latency, error rates, and hallucination metrics. Implement semantic caching to deliver sub-second "
                        "responses on common queries while slashing API expenditure by up to 50%."
                    ),
                    description_ar=(
                        "مراقبة زمن استجابة النموذج (TTFT)، معدل الهلوسة، وجودة الردود. تطبيق التخزين المؤقت الدلالي (Semantic Cache) "
                        "لتقديم استجابات فورية في أقل من ثانية وخفض تكاليف الاستدعاء بنسبة 50%."
                    ),
                    problem_addressed_ar="بطء استجابة النماذج في بعض الاستفسارات المتكررة وتزايد تكاليف استهلاك الـ API.",
                    recommended_technologies=["Langfuse", "Helicone", "Redis Semantic Cache", "LiteLLM"],
                    implementation_steps=[
                        "ربط سجلات التتبع بمكتبة Langfuse لمراقبة دقة كل استجابة.",
                        "تفعيل التخزين الدلالي المسبق للأسئلة الشائعة والمتكررة.",
                    ],
                ),
            ]

        # 4. Save and return report
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
