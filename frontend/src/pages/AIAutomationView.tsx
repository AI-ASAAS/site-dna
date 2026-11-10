import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  Sparkles,
  Bot,
  Cpu,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Zap,
  Layers,
  Code2,
  Terminal,
  TrendingUp,
  ShieldCheck,
  Search,
  MessageSquare,
  Workflow,
  Wand2,
} from 'lucide-react';

interface AIAutomationViewProps {
  runId: string;
}

export function AIAutomationView({ runId }: AIAutomationViewProps) {
  const { lang } = useLang();
  const isAr = lang === 'ar';

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .getAIAutomation(runId)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load AI automation data:', err);
        setLoading(false);
      });
  }, [runId]);

  if (loading) {
    return (
      <div className="p-12 text-center space-y-3">
        <div className="w-10 h-10 mx-auto rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-500 animate-spin">
          <Sparkles className="w-5 h-5" />
        </div>
        <p className="text-sm font-bold text-[var(--text)]">
          {isAr
            ? 'جاري فحص وتدقيق جاهزية وتوظيف الذكاء الاصطناعي والأتمتة...'
            : 'Auditing website AI readiness, chatbots, and automation capabilities...'}
        </p>
        <p className="text-xs text-[var(--text-3)]">
          {isAr
            ? 'فحص روبوتات المحادثة، الوكلاء الأذكياء، محركات البحث الدلالية، وأدوات أتمتة المهام'
            : 'Inspecting chatbot widgets, autonomous agents, semantic vector search, and workflow automation'}
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-12 text-center rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-3">
        <AlertTriangle className="w-8 h-8 mx-auto text-amber-500" />
        <h3 className="font-bold text-sm text-[var(--text)]">
          {isAr ? 'لم تكتمل مرحلة فحص الذكاء الاصطناعي لهذه الجولة بعد' : 'AI Analysis Not Available'}
        </h3>
        <p className="text-xs text-[var(--text-3)] max-w-md mx-auto">
          {isAr
            ? 'تأكد من اكتمال استكشاف وزحف الموقع ليتمكن الوكيل من استخلاص جاهزية الذكاء الاصطناعي.'
            : 'Ensure discovery and crawl stages are completed to generate the AI readiness report.'}
        </p>
      </div>
    );
  }

  const isPresent = data.status === 'present';
  const isPartial = data.status === 'partial';
  const isAbsent = data.status === 'absent';

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* 1. Header / Hero Diagnosis Banner */}
      <div
        className={`p-6 md:p-8 rounded-3xl border transition-all ${
          isPresent
            ? 'border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 via-emerald-500/5 to-transparent'
            : isPartial
            ? 'border-blue-500/30 bg-gradient-to-br from-blue-500/10 via-blue-500/5 to-transparent'
            : 'border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-amber-500/5 to-transparent'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2.5 max-w-3xl">
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                  isPresent
                    ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                    : isPartial
                    ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/30'
                    : 'bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/30'
                }`}
              >
                {isPresent && <Bot className="w-3.5 h-3.5" />}
                {isPartial && <Cpu className="w-3.5 h-3.5" />}
                {isAbsent && <Sparkles className="w-3.5 h-3.5" />}
                <span>
                  {isPresent
                    ? isAr
                      ? 'تم رصد توظيف ذكاء اصطناعي ووكلاء أذكياء'
                      : 'AI & Agents Detected'
                    : isPartial
                    ? isAr
                      ? 'توظيف أولي وجزئي للذكاء الاصطناعي'
                      : 'Partial AI Utilization'
                    : isAr
                    ? 'الموقع يفتقر لتوظيف الذكاء الاصطناعي وروبوتات المحادثة'
                    : 'Lacks AI & Conversational Automation'}
                </span>
              </span>
              <span className="text-[11px] font-mono text-[var(--text-3)]">{data.target_url}</span>
            </div>

            <h1 className="text-xl md:text-2xl font-bold text-[var(--text)] tracking-tight">
              {isAr ? data.headline_ar : data.headline_en}
            </h1>

            <p className="text-xs md:text-sm text-[var(--text-2)] leading-relaxed">
              {isAr ? data.summary_ar : data.summary_en}
            </p>
          </div>

          {/* Maturity Score Circular Gauge */}
          <div className="flex flex-col items-center justify-center p-4 rounded-2xl bg-[var(--bg)] border border-[var(--hairline)] min-w-[140px] shadow-sm">
            <div className="text-[10px] font-bold text-[var(--text-3)] uppercase tracking-wider mb-1">
              {isAr ? 'مؤشر جاهزية الذكاء الاصطناعي' : 'AI Readiness Score'}
            </div>
            <div className="flex items-baseline gap-1">
              <span
                className={`text-3xl font-black font-mono ${
                  data.maturity_score >= 70
                    ? 'text-emerald-500'
                    : data.maturity_score >= 40
                    ? 'text-blue-500'
                    : 'text-amber-500'
                }`}
              >
                {Math.round(data.maturity_score)}
              </span>
              <span className="text-xs text-[var(--text-3)] font-mono">/100</span>
            </div>
            <div className="mt-1 text-[11px] font-semibold text-[var(--text-2)]">
              {data.maturity_score >= 70
                ? isAr
                  ? 'نضج ذكي متقدم'
                  : 'Advanced Maturity'
                : data.maturity_score >= 40
                ? isAr
                  ? 'جاهزية متوسطة'
                  : 'Moderate Readiness'
                : isAr
                ? 'فجوة استراتيجية ملحة'
                : 'Strategic Gap'}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Key AI Capabilities Checklist */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                data.has_chatbot ? 'bg-emerald-500/10 text-emerald-500' : 'bg-stone-500/10 text-stone-400'
              }`}
            >
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-[var(--text)]">
                {isAr ? 'روبوت محادثة تفاعلي (Chatbot)' : 'Conversational Chatbot'}
              </div>
              <div className="text-[11px] text-[var(--text-3)]">
                {data.has_chatbot
                  ? isAr
                    ? 'متوفر ونشط في الموقع'
                    : 'Active on website'
                  : isAr
                    ? 'غير متوفر (فرصة فورية)'
                    : 'Not Detected (High Opportunity)'}
              </div>
            </div>
          </div>
          {data.has_chatbot ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
          ) : (
            <XCircle className="w-5 h-5 text-stone-400 shrink-0" />
          )}
        </div>

        <div className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                data.has_agent ? 'bg-emerald-500/10 text-emerald-500' : 'bg-stone-500/10 text-stone-400'
              }`}
            >
              <Workflow className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-[var(--text)]">
                {isAr ? 'وكلاء أذكياء وأتمتة (AI Agents)' : 'Autonomous AI Agents'}
              </div>
              <div className="text-[11px] text-[var(--text-3)]">
                {data.has_agent
                  ? isAr
                    ? 'تم رصد بنية وكلاء أو أنظمة ذكية'
                    : 'Intelligent systems detected'
                  : isAr
                    ? 'غير متوفر (فرصة أتمتة)'
                    : 'Not Detected'}
              </div>
            </div>
          </div>
          {data.has_agent ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
          ) : (
            <XCircle className="w-5 h-5 text-stone-400 shrink-0" />
          )}
        </div>

        <div className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                data.has_semantic_search ? 'bg-emerald-500/10 text-emerald-500' : 'bg-stone-500/10 text-stone-400'
              }`}
            >
              <Search className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-[var(--text)]">
                {isAr ? 'بحث دلالي وتوصيات (Semantic RAG)' : 'Semantic Vector Search'}
              </div>
              <div className="text-[11px] text-[var(--text-3)]">
                {data.has_semantic_search
                  ? isAr
                    ? 'محرك ذكي قائم على المعنى'
                    : 'Active vector search'
                  : isAr
                    ? 'بحث تقليدي أو غائب'
                    : 'Traditional or Missing'}
              </div>
            </div>
          </div>
          {data.has_semantic_search ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
          ) : (
            <XCircle className="w-5 h-5 text-stone-400 shrink-0" />
          )}
        </div>
      </div>

      {/* 3. Detected Evidence Section */}
      {data.detected_evidences && data.detected_evidences.length > 0 && (
        <div className="p-5 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-3">
          <h2 className="text-xs font-bold text-[var(--text)] flex items-center gap-2">
            <Code2 className="w-4 h-4 text-amber-500" />
            <span>{isAr ? 'الأدلة والتقنيات المرصودة في فحص الموقع' : 'Observed Technical Evidence & Indicators'}</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {data.detected_evidences.map((ev: any, idx: number) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-[var(--hairline)] bg-[var(--bg)] flex items-start gap-2.5"
              >
                <div className="w-6 h-6 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center shrink-0 mt-0.5">
                  <Terminal className="w-3.5 h-3.5" />
                </div>
                <div className="space-y-0.5 overflow-hidden">
                  <div className="text-xs font-bold text-[var(--text)] truncate">{ev.indicator}</div>
                  <div className="text-[11px] text-[var(--text-3)] leading-snug line-clamp-2">{ev.source}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Actionable AI Blueprint & Proposals */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-3">
          <div>
            <h2 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
              <Wand2 className="w-4 h-4 text-amber-500" />
              <span>
                {isAbsent
                  ? isAr
                    ? 'خطة التوظيف الفوري للذكاء الاصطناعي والأتمتة (AI Adoption Blueprint)'
                    : 'Immediate AI & Automation Adoption Blueprint'
                  : isAr
                  ? 'خطة الترقية المتقدمة للذكاء الاصطناعي والوكلاء (AI Optimization Blueprint)'
                  : 'Advanced AI Optimization & Agentic Blueprint'}
              </span>
            </h2>
            <p className="text-xs text-[var(--text-3)] mt-0.5">
              {isAbsent
                ? isAr
                  ? 'حلول موجهة لسد الفجوة وتوفير دعم العملاء الفوري ومضاعفة المبيعات عبر الوكلاء'
                  : 'Targeted proposals to bridge the competitive gap with 24/7 chatbots and sales agents'
                : isAr
                ? 'مقترحات نوعية لترقية الأنظمة نحو الوكلاء متعددي الوسائط والذاكرة الدائمة والأتمتة الإجرائية'
                : 'Advanced proposals to elevate agents with multi-modal reasoning and tool execution'}
            </p>
          </div>
          <span className="text-xs font-mono font-bold text-amber-500 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20">
            {data.proposals?.length || 0} {isAr ? 'مقترحات معتمدة' : 'Proposals'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.proposals &&
            data.proposals.map((prop: any) => (
              <div
                key={prop.id}
                className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] flex flex-col justify-between space-y-4 hover:border-amber-500/40 transition-all shadow-sm"
              >
                <div className="space-y-3">
                  {/* Top Badges */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/20">
                        {prop.id}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          prop.priority === 'P1'
                            ? 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20'
                            : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                        }`}
                      >
                        {prop.priority === 'P1'
                          ? isAr
                            ? 'أولوية قصوى P1'
                            : 'High Priority P1'
                          : isAr
                          ? 'أولوية تطويرية P2'
                          : 'Medium Priority P2'}
                      </span>
                    </div>

                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      {prop.expected_impact === 'critical'
                        ? isAr
                          ? 'أثر حاسم'
                          : 'Critical Impact'
                        : isAr
                        ? 'أثر مرتفع'
                        : 'High Impact'}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="text-sm font-bold text-[var(--text)] leading-snug">
                    {isAr ? prop.title_ar : prop.title}
                  </h3>

                  {/* Problem addressed */}
                  {prop.problem_addressed_ar && (
                    <div className="p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/15 text-xs space-y-0.5">
                      <div className="text-[10px] font-bold text-amber-700 dark:text-amber-400">
                        {isAr ? 'الفجوة أو المشكلة المعالجة:' : 'Bottleneck Addressed:'}
                      </div>
                      <div className="text-[var(--text-2)] text-[11px] leading-relaxed">
                        {prop.problem_addressed_ar}
                      </div>
                    </div>
                  )}

                  {/* Detailed Description */}
                  <p className="text-xs text-[var(--text-2)] leading-relaxed">
                    {isAr ? prop.description_ar : prop.description}
                  </p>

                  {/* Recommended Technologies */}
                  {prop.recommended_technologies && prop.recommended_technologies.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <div className="text-[10px] font-bold text-[var(--text-3)] uppercase tracking-wider">
                        {isAr ? 'التقنيات والنماذج المقترحة:' : 'Recommended Stack:'}
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {prop.recommended_technologies.map((tech: string, tIdx: number) => (
                          <span
                            key={tIdx}
                            className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-[var(--bg)] border border-[var(--hairline)] text-[var(--text)] font-semibold"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Implementation Steps */}
                  {prop.implementation_steps && prop.implementation_steps.length > 0 && (
                    <div className="space-y-1.5 pt-1 border-t border-[var(--hairline)]">
                      <div className="text-[10px] font-bold text-[var(--text-3)] uppercase tracking-wider">
                        {isAr ? 'خطوات التنفيذ الموصى بها:' : 'Implementation Steps:'}
                      </div>
                      <ul className="space-y-1 text-[11px] text-[var(--text-2)]">
                        {prop.implementation_steps.map((step: string, sIdx: number) => (
                          <li key={sIdx} className="flex items-start gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 mt-1.5" />
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
