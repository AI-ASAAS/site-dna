import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  Compass,
  Layers,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  GitBranch,
  Scale,
  ListTodo,
  FileCheck,
  Check,
  Search,
  Filter,
  Activity,
  Zap,
  Target,
  ExternalLink,
  ChevronDown,
} from 'lucide-react';

interface StrategicIntelligenceViewProps {
  runId: string;
}

export function StrategicIntelligenceView({ runId }: StrategicIntelligenceViewProps) {
  const { lang, t } = useLang();
  const isAr = lang === 'ar';

  const [report, setReport] = useState<any>(null);
  const [actions, setActions] = useState<any[]>([]);
  const [conflicts, setConflicts] = useState<any[]>([]);
  const [roadmap, setRoadmap] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingActionId, setUpdatingActionId] = useState<string | null>(null);

  // Active sub-tab
  const [activeTab, setActiveTab] = useState<
    'overview' | 'findings' | 'duplicates' | 'conflicts' | 'roadmap' | 'backlog' | 'verification'
  >('overview');

  // Backlog filters
  const [backlogPriorityFilter, setBacklogPriorityFilter] = useState<string>('all');
  const [backlogStatusFilter, setBacklogStatusFilter] = useState<string>('all');
  const [findingsDomainFilter, setFindingsDomainFilter] = useState<string>('all');
  const [findingsSeverityFilter, setFindingsSeverityFilter] = useState<string>('all');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getStrategicReport(runId).catch(() => null),
      api.getStrategicActions(runId).catch(() => []),
      api.getStrategicConflicts(runId).catch(() => []),
      api.getStrategicRoadmap(runId).catch(() => []),
    ])
      .then(([rep, acts, confs, rmap]) => {
        setReport(rep);
        setActions(acts || []);
        setConflicts(confs || []);
        setRoadmap(rmap || []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [runId]);

  const handleUpdateStatus = async (actionId: string, newStatus: string) => {
    setUpdatingActionId(actionId);
    try {
      await api.updateActionStatus(runId, actionId, newStatus, 'Updated via Site DNA Strategic Console');
      // Update local state
      setActions((prev) =>
        prev.map((a) => (a.action_id === actionId ? { ...a, status: newStatus } : a))
      );
      if (report?.action_backlog) {
        const updatedBacklog = report.action_backlog.map((a: any) =>
          a.action_id === actionId ? { ...a, status: newStatus } : a
        );
        setReport({ ...report, action_backlog: updatedBacklog });
      }
    } catch (e) {
      console.error('Failed to update action status:', e);
    } finally {
      setUpdatingActionId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center space-y-3">
        <div className="w-10 h-10 mx-auto rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-500 animate-spin">
          <Compass className="w-5 h-5" />
        </div>
        <p className="text-sm font-bold text-[var(--text)]">
          {isAr
            ? 'جاري تحميل توليف الذكاء الاستراتيجي وخارطة الطريق (Phase 11)...'
            : 'Loading Strategic Intelligence & Action Roadmap (Phase 11)...'}
        </p>
        <p className="text-xs text-[var(--text-3)]">
          {isAr
            ? 'توليف متقاطع لنتائج الوكلاء، تصفية الملاحظات المكررة، وحل التعارضات الهندسية'
            : 'Cross-agent synthesis, deduplication, conflict resolution, and prioritized sequencing'}
        </p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-12 text-center rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
        <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-base text-[var(--text)]">
            {isAr ? 'لا يتوفر تقرير ذكاء استراتيجي لهذه الجولة بعد' : 'No Strategic Report Available'}
          </h3>
          <p className="text-xs text-[var(--text-3)] max-w-md mx-auto">
            {isAr
              ? 'يمكنك تشغيل مرحلة الذكاء الاستراتيجي وتوليف خارطة الطريق من قائمة تشغيل التحليل الجديد.'
              : 'You can trigger Strategic Intelligence & Unified Action Roadmap from the New Analysis page.'}
          </p>
        </div>
      </div>
    );
  }

  const stats = report.statistics || {};
  const coverage = report.coverage || {};
  const duplicateGroups = report.duplicate_groups || [];
  const relationships = report.relationships || [];
  const opportunities = report.opportunities || [];
  const rootCauses = report.root_causes || [];
  const unifiedFindings = report.unified_findings || [];
  const verificationPlans = report.verification_plans || [];
  const measurementPlans = report.measurement_plans || [];
  const manualReviews = report.manual_reviews || [];

  const filteredBacklog = actions.filter((a) => {
    if (backlogPriorityFilter !== 'all' && a.priority !== backlogPriorityFilter) return false;
    if (backlogStatusFilter !== 'all' && a.status !== backlogStatusFilter) return false;
    return true;
  });

  const filteredFindings = unifiedFindings.filter((f: any) => {
    if (findingsDomainFilter !== 'all' && f.domain !== findingsDomainFilter) return false;
    if (findingsSeverityFilter !== 'all' && f.severity !== findingsSeverityFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Strategic Header & Health Index */}
      <div className="p-6 rounded-3xl border border-[var(--glass-rim)] bg-gradient-to-br from-[var(--glass-tint-strong)] to-[var(--glass-tint)] backdrop-blur-xl shadow-lg space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-[var(--hairline)] pb-5">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-500/30">
              <Compass className="w-3.5 h-3.5 text-indigo-500" />
              <span>
                {isAr ? 'المرحلة 11 — الذكاء الاستراتيجي وخارطة الطريق الموحدة' : 'Phase 11 — Strategic Intelligence & Unified Roadmap'}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[var(--text)] tracking-tight">
              {isAr ? 'توليف الرؤية الاستراتيجية وخطة العمل العلاجية' : 'Strategic Synthesis & Action Roadmap'}
            </h1>
            <p className="text-xs sm:text-sm text-[var(--text-2)] max-w-3xl leading-relaxed">
              {isAr
                ? 'دمج وتحليل متقاطع لنتائج كافة الوكلاء المتخصصين، مع كشف وحل التعارضات الهندسية، وإلغاء التكرار، وبناء خارطة طريق ذات 4 موجات تنفيذية محكمة الأدلة.'
                : 'Cross-agent synthesis of all specialized audits, resolving technical conflicts, deduplicating findings, and producing an evidence-grounded 4-wave roadmap.'}
            </p>
          </div>

          {/* Strategic Health Score Tile */}
          <div className="flex items-center gap-4 bg-[var(--glass-inset)] p-4 rounded-2xl border border-[var(--hairline)] shrink-0">
            <div className="text-center">
              <div className="text-xs text-[var(--text-3)] font-medium mb-1">
                {isAr ? 'المؤشر الاستراتيجي' : 'Strategic Health Index'}
              </div>
              <div className="text-3xl font-black text-indigo-600 dark:text-indigo-400 font-mono">
                {stats.strategic_index ?? 75}
                <span className="text-xs text-[var(--text-3)] font-normal"> / 100</span>
              </div>
              <div className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 mt-1">
                {stats.index_label_ar || (isAr ? 'جاهزية استراتيجية جيدة' : 'Good Strategic Posture')}
              </div>
            </div>
          </div>
        </div>

        {/* Multi-Agent Synthesis Stat Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)]">
            <div className="text-[11px] text-[var(--text-3)] mb-1">{isAr ? 'الوكلاء المساهمون' : 'Source Agents'}</div>
            <div className="text-xl font-extrabold text-[var(--text)] font-mono">
              {coverage.available_agents?.length ?? 0}
            </div>
            <div className="text-[10px] text-emerald-700 dark:text-emerald-400">
              {isAr ? 'تغطية تحليلية متكاملة' : 'Integrated Coverage'}
            </div>
          </div>

          <div className="p-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)]">
            <div className="text-[11px] text-[var(--text-3)] mb-1">{isAr ? 'الملاحظات الأولية' : 'Raw Findings'}</div>
            <div className="text-xl font-extrabold text-[var(--text)] font-mono">
              {stats.total_raw_findings ?? 0}
            </div>
            <div className="text-[10px] text-[var(--text-3)]">{isAr ? 'من مختلف المراحل' : 'Across all phases'}</div>
          </div>

          <div className="p-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)]">
            <div className="text-[11px] text-[var(--text-3)] mb-1">{isAr ? 'الملاحظات الموحدة' : 'Unified Findings'}</div>
            <div className="text-xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">
              {stats.total_unified_findings ?? unifiedFindings.length}
            </div>
            <div className="text-[10px] text-indigo-700 dark:text-indigo-300">
              {stats.deduplication_ratio ? `${stats.deduplication_ratio}% تصفية تكرار` : 'بعد إلغاء التكرار'}
            </div>
          </div>

          <div className="p-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)]">
            <div className="text-[11px] text-[var(--text-3)] mb-1">{isAr ? 'مجموعات مكررة' : 'Duplicate Groups'}</div>
            <div className="text-xl font-extrabold text-stone-900 dark:text-stone-100 font-mono">
              {stats.total_duplicate_groups ?? duplicateGroups.length}
            </div>
            <div className="text-[10px] text-stone-700 dark:text-stone-300 font-semibold">{isAr ? 'تم دمجها وربطها' : 'Unified canonical'}</div>
          </div>

          <div className="p-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)]">
            <div className="text-[11px] text-[var(--text-3)] mb-1">{isAr ? 'التعارضات الهندسية' : 'Conflicts'}</div>
            <div className="text-xl font-extrabold text-red-600 dark:text-red-400 font-mono">
              {stats.total_conflicts_detected ?? conflicts.length}
            </div>
            <div className="text-[10px] text-red-700 dark:text-red-300">{isAr ? 'مقايضات مدروسة' : 'Managed tradeoffs'}</div>
          </div>

          <div className="p-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)]">
            <div className="text-[11px] text-[var(--text-3)] mb-1">{isAr ? 'مهام خطة العمل' : 'Backlog Actions'}</div>
            <div className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
              {stats.total_actions ?? actions.length}
            </div>
            <div className="text-[10px] text-emerald-700 dark:text-emerald-400">{isAr ? 'ضمن 4 موجات' : 'Across 4 Waves'}</div>
          </div>
        </div>

        {/* 7 Interactive Sub-Tabs Navigation */}
        <div className="flex items-center gap-1.5 overflow-x-auto border-t border-[var(--hairline)] pt-3 text-xs font-semibold no-scrollbar">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer flex items-center gap-2 ${
              activeTab === 'overview'
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>{isAr ? 'نظرة استراتيجية وتوليف' : 'Overview & Synthesis'}</span>
          </button>

          <button
            onClick={() => setActiveTab('findings')}
            className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer flex items-center gap-2 ${
              activeTab === 'findings'
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>{isAr ? 'الملاحظات الموحدة' : 'Unified Findings'}</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-black/20 text-white">
              {unifiedFindings.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('duplicates')}
            className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer flex items-center gap-2 ${
              activeTab === 'duplicates'
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            <GitBranch className="w-4 h-4" />
            <span>{isAr ? 'الدمج وشبكة العلاقات' : 'Duplicates & Graph'}</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-black/20 text-white">
              {duplicateGroups.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('conflicts')}
            className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer flex items-center gap-2 ${
              activeTab === 'conflicts'
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            <Scale className="w-4 h-4" />
            <span>{isAr ? 'التعارضات والمقايضات' : 'Conflicts & Tradeoffs'}</span>
            {conflicts.length > 0 && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-red-500/30 text-red-200">
                {conflicts.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('roadmap')}
            className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer flex items-center gap-2 ${
              activeTab === 'roadmap'
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>{isAr ? 'خارطة الطريق (4 موجات)' : 'Roadmap (4 Waves)'}</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-black/20 text-white">
              {roadmap.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('backlog')}
            className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer flex items-center gap-2 ${
              activeTab === 'backlog'
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            <ListTodo className="w-4 h-4" />
            <span>{isAr ? 'قائمة المهام التنفيذية (Backlog)' : 'Action Backlog'}</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-black/20 text-white">
              {actions.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('verification')}
            className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer flex items-center gap-2 ${
              activeTab === 'verification'
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            <FileCheck className="w-4 h-4" />
            <span>{isAr ? 'التحقق والقياس المستمر' : 'Verification & Metrics'}</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-black/20 text-white">
              {verificationPlans.length}
            </span>
          </button>
        </div>
      </div>

      {/* SUB-TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Executive Synthesis Summary */}
          <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
            <h2 className="text-lg font-bold text-[var(--text)] flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              <span>{isAr ? 'الخلاصة الاستراتيجية التنفيذية' : 'Executive Strategic Synthesis'}</span>
            </h2>
            <div className="text-sm text-[var(--text-2)] leading-relaxed whitespace-pre-line bg-[var(--glass-inset)] p-4 rounded-2xl border border-[var(--hairline)]">
              {report.executive_summary_md ||
                (isAr
                  ? 'تم إنجاز التوليف الاستراتيجي لكافة محاور الموقع بنجاح. تبرز الأولويات في معالجة فجوات إمكانية الوصول، وتطبيق ترويسات الأمان الصارمة CSP، وتحسين مؤشرات الأداء الحيوية LCP/CLS مع الموازنة بين متطلبات الهوية وسرعة التحميل.'
                  : 'Cross-agent strategic synthesis completed successfully. Core priorities focus on accessibility remediations, CSP hardening, and Core Web Vitals optimization without compromising brand aesthetic or performance.')}
            </div>
          </div>

          {/* Root Cause Candidates & Strategic Opportunities */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Root Causes */}
            <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
              <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                <Target className="w-4 h-4 text-red-500" />
                <span>{isAr ? 'الفرضيات الجذرية للمشاكل (Root Causes)' : 'Root Cause Candidates'}</span>
              </h3>
              <div className="space-y-3">
                {rootCauses.length > 0 ? (
                  rootCauses.map((rc: any, idx: number) => (
                    <div
                      key={rc.candidate_id || idx}
                      className="p-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-[var(--text)]">
                          {isAr ? rc.title_ar || rc.title : rc.title}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-500/15 text-red-700 dark:text-red-300">
                          {rc.confidence_level || 'مرتفع'}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-2)] leading-relaxed">
                        {isAr ? rc.description_ar || rc.description : rc.description}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-center text-xs text-[var(--text-3)]">
                    {isAr ? 'لا توجد فرضيات أسباب جذرية حرجة معقدة.' : 'No major root causes identified.'}
                  </div>
                )}
              </div>
            </div>

            {/* Strategic Opportunities */}
            <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
              <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-500" />
                <span>{isAr ? 'فرص التميز والريادة الاستراتيجية' : 'Strategic Opportunities'}</span>
              </h3>
              <div className="space-y-3">
                {opportunities.length > 0 ? (
                  opportunities.map((opp: any, idx: number) => (
                    <div
                      key={opp.opportunity_id || idx}
                      className="p-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-[var(--text)]">
                          {isAr ? opp.title_ar || opp.title : opp.title}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-700 dark:text-emerald-300">
                          {opp.strategic_theme || 'ريادة'}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-2)] leading-relaxed">
                        {isAr ? opp.description_ar || opp.description : opp.description}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-center text-xs text-[var(--text-3)]">
                    {isAr ? 'لا توجد فرص استراتيجية غير مفعّلة.' : 'No opportunities recorded.'}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: UNIFIED FINDINGS */}
      {activeTab === 'findings' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)]">
            <div className="flex items-center gap-3">
              <Filter className="w-4 h-4 text-[var(--text-3)]" />
              <span className="text-xs font-bold text-[var(--text)]">
                {isAr ? 'تصفية الملاحظات الموحدة:' : 'Filter Unified Findings:'}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={findingsDomainFilter}
                onChange={(e) => setFindingsDomainFilter(e.target.value)}
                className="text-xs px-3 py-1.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-inset)] text-[var(--text)]"
              >
                <option value="all">{isAr ? 'كافة المجالات' : 'All Domains'}</option>
                <option value="accessibility">{isAr ? 'إمكانية الوصول' : 'Accessibility'}</option>
                <option value="security">{isAr ? 'الأمان والخصوصية' : 'Security'}</option>
                <option value="performance">{isAr ? 'الأداء والسرعة' : 'Performance'}</option>
                <option value="seo">{isAr ? 'SEO والظهور' : 'SEO'}</option>
                <option value="ux">{isAr ? 'تجربة المستخدم' : 'UX'}</option>
                <option value="visual">{isAr ? 'الهوية البصرية' : 'Visual'}</option>
                <option value="competitor">{isAr ? 'المنافسة' : 'Competitor'}</option>
              </select>

              <select
                value={findingsSeverityFilter}
                onChange={(e) => setFindingsSeverityFilter(e.target.value)}
                className="text-xs px-3 py-1.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-inset)] text-[var(--text)]"
              >
                <option value="all">{isAr ? 'كافة مستويات الخطورة' : 'All Severities'}</option>
                <option value="critical">{isAr ? 'حرجة (Critical)' : 'Critical'}</option>
                <option value="high">{isAr ? 'عالية (High)' : 'High'}</option>
                <option value="medium">{isAr ? 'متوسطة (Medium)' : 'Medium'}</option>
                <option value="low">{isAr ? 'منخفضة (Low)' : 'Low'}</option>
              </select>
            </div>
          </div>

          {/* Unified Findings List */}
          <div className="space-y-3">
            {filteredFindings.map((finding: any) => (
              <div
                key={finding.unified_finding_id}
                className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-3 hover:border-[var(--glass-rim)] transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[var(--hairline)] text-[var(--text-3)]">
                      {finding.unified_finding_id}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        finding.severity === 'critical'
                          ? 'bg-red-600 text-white'
                          : finding.severity === 'high'
                          ? 'bg-orange-600 text-white'
                          : finding.severity === 'medium'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-600 text-white'
                      }`}
                    >
                      {finding.severity.toUpperCase()}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 font-medium">
                      {finding.domain}
                    </span>
                  </div>
                  <div className="text-[10px] text-[var(--text-3)] font-mono">
                    {finding.source_findings?.length ?? 1} {isAr ? 'مصادر أصلية مدمجة' : 'source findings'}
                  </div>
                </div>

                <div>
                  <h4 className="font-bold text-sm text-[var(--text)]">
                    {isAr ? finding.title_ar || finding.title : finding.title}
                  </h4>
                  <p className="text-xs text-[var(--text-2)] mt-1 leading-relaxed">
                    {isAr ? finding.description_ar || finding.description : finding.description}
                  </p>
                </div>

                {finding.source_agents && finding.source_agents.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-[var(--hairline)]">
                    <span className="text-[10px] text-[var(--text-3)]">{isAr ? 'وكلاء الرصد:' : 'Agents:'}</span>
                    {finding.source_agents.map((ag: string) => (
                      <span
                        key={ag}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--hairline)] text-[var(--text-2)]"
                      >
                        {ag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUB-TAB 3: DUPLICATES & RELATIONSHIPS GRAPH */}
      {activeTab === 'duplicates' && (
        <div className="space-y-6">
          {/* Deduplication Summary */}
          <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
            <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-indigo-500" />
              <span>{isAr ? 'مجموعات الملاحظات المكررة والمدمجة' : 'Deduplication Groups & Canonical Synthesis'}</span>
            </h3>
            <p className="text-xs text-[var(--text-2)]">
              {isAr
                ? 'تم فحص التشابه الدلالي والتقني بين مخرجات مختلف الوكلاء ودمجها لمنع تضخم التقرير وتشتيت فرق التنفيذ.'
                : 'Identical and cross-cutting findings unified under canonical records to prevent audit bloat.'}
            </p>

            <div className="space-y-3">
              {duplicateGroups.length > 0 ? (
                duplicateGroups.map((grp: any, idx: number) => (
                  <div
                    key={grp.group_id || idx}
                    className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[var(--text)]">
                        {isAr ? grp.canonical_title_ar || grp.canonical_title : grp.canonical_title}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-900/10 text-stone-900 dark:bg-stone-100/10 dark:text-stone-100 font-bold border border-stone-800/20">
                        {grp.findings?.length ?? 0} {isAr ? 'ملاحظات مدمجة' : 'merged'}
                      </span>
                    </div>
                    <div className="text-[11px] text-[var(--text-3)]">
                      {isAr ? 'مبرر الدمج:' : 'Merge Rationale:'} {grp.similarity_rationale || grp.rationale}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-6 text-center text-xs text-[var(--text-3)]">
                  {isAr ? 'لم يتم رصد تكرارات مباشرة بين الوكلاء.' : 'No direct duplicate groups detected.'}
                </div>
              )}
            </div>
          </div>

          {/* Semantic Cross-Agent Relationship Graph */}
          <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
            <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
              <Layers className="w-5 h-5 text-amber-500" />
              <span>{isAr ? 'شبكة العلاقات بين الملاحظات (Relationship Graph)' : 'Cross-Agent Relationship Graph'}</span>
            </h3>
            <div className="space-y-2">
              {relationships.length > 0 ? (
                relationships.map((rel: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl border border-[var(--hairline)] bg-[var(--glass-inset)] flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-[var(--text-3)]">{rel.source_id}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                      <span className="font-mono text-[10px] text-[var(--text-3)]">{rel.target_id}</span>
                      <span className="font-medium text-[var(--text)]">{rel.relationship_type}</span>
                    </div>
                    <div className="text-[10px] text-[var(--text-3)]">{rel.explanation}</div>
                  </div>
                ))
              ) : (
                <div className="p-6 text-center text-xs text-[var(--text-3)]">
                  {isAr ? 'شبكة العلاقات الهندسية متوازنة ومستقلة.' : 'No inter-finding coupling issues detected.'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 4: CONFLICTS & TRADEOFFS */}
      {activeTab === 'conflicts' && (
        <div className="space-y-4">
          <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                <Scale className="w-5 h-5 text-stone-800 dark:text-stone-200" />
                <span>{isAr ? 'التعارضات الهندسية والمقايضات المتوازنة' : 'Architectural Conflicts & Balanced Trade-offs'}</span>
              </h3>
              <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-stone-900/10 text-stone-900 dark:bg-stone-100/10 dark:text-stone-100 font-bold border border-stone-800/20">
                {conflicts.length} {isAr ? 'تعارض مرصود' : 'Conflicts'}
              </span>
            </div>
            <p className="text-xs text-[var(--text-2)] leading-relaxed">
              {isAr
                ? 'رصد التناقضات بين الأهداف التقنية (مثل: التباين البصري مقابل هوية العلامة، أو قيود CSP مقابل سكريبتات التسويق) واقتراح حلول هندسية متوازنة دون المساس بالأمان أو إمكانية الوصول الإلزامية.'
                : 'Identifies conflicting technical imperatives (e.g. strict CSP vs 3rd-party trackers, high contrast vs brand design) and provides balanced remediation.'}
            </p>

            <div className="space-y-4">
              {conflicts.length > 0 ? (
                conflicts.map((conf: any, idx: number) => (
                  <div
                    key={conf.conflict_id || idx}
                    className="p-5 rounded-2xl border border-orange-500/40 bg-orange-500/10 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-[var(--text)]">
                        {isAr ? conf.title_ar || conf.title : conf.title}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-700 dark:text-red-300">
                        {conf.conflict_type || 'تعارض متطلبات'}
                      </span>
                    </div>

                    <p className="text-xs text-[var(--text-2)] leading-relaxed">
                      {isAr ? conf.description_ar || conf.description : conf.description}
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-orange-500/30 text-xs">
                      <div className="p-2.5 rounded-xl bg-[var(--glass-inset)]">
                        <div className="font-semibold text-orange-950 dark:text-orange-200 mb-1">
                          {isAr ? 'الطرف الأول' : 'Side A'}
                        </div>
                        <div className="text-[11px] text-[var(--text-2)]">
                          {conf.finding_a_id} ({conf.domain_a})
                        </div>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[var(--glass-inset)]">
                        <div className="font-semibold text-orange-950 dark:text-orange-200 mb-1">
                          {isAr ? 'الطرف الثاني' : 'Side B'}
                        </div>
                        <div className="text-[11px] text-[var(--text-2)]">
                          {conf.finding_b_id} ({conf.domain_b})
                        </div>
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs">
                      <div className="font-bold text-emerald-800 dark:text-emerald-300 mb-0.5 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{isAr ? 'الحل المتوازن الموصى به:' : 'Recommended Resolution:'}</span>
                      </div>
                      <div className="text-[11px] text-[var(--text)] leading-relaxed">
                        {isAr ? conf.resolution_ar || conf.resolution : conf.resolution}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-xs text-[var(--text-3)] bg-[var(--glass-inset)] rounded-2xl">
                  {isAr
                    ? 'لم يتم تسجيل أي تعارضات غير قابلة للتوفيق بين الوكلاء في هذا الموقع.'
                    : 'No irreconcilable conflicts discovered between audit dimensions.'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 5: ACTION ROADMAP (4 WAVES) */}
      {activeTab === 'roadmap' && (
        <div className="space-y-6">
          <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
            <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-500" />
              <span>{isAr ? 'خارطة الطريق التنفيذية عبر 4 موجات متعاقبة' : 'Sequenced 4-Wave Action Roadmap'}</span>
            </h3>
            <p className="text-xs text-[var(--text-2)]">
              {isAr
                ? 'تسلسل زمني استراتيجي يراعي التبعيات التقنية والجدوى وسرعة تحقيق الأثر (Quick Wins).'
                : 'Prioritized wave sequencing accounting for technical dependencies and quick-win impacts.'}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {roadmap.map((w: any) => (
                <div
                  key={w.wave_number}
                  className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] flex flex-col justify-between space-y-3"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-black px-2 py-1 rounded bg-indigo-500/20 text-indigo-700 dark:text-indigo-300">
                        {isAr ? `الموجة ${w.wave_number}` : `Wave ${w.wave_number}`}
                      </span>
                      <span className="text-[10px] text-[var(--text-3)]">{w.timeframe}</span>
                    </div>

                    <h4 className="font-bold text-sm text-[var(--text)]">
                      {isAr ? w.title_ar || w.title : w.title}
                    </h4>
                    <p className="text-xs text-[var(--text-2)] leading-relaxed">
                      {isAr ? w.description_ar || w.description : w.description}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-[var(--hairline)] flex items-center justify-between text-xs">
                    <span className="text-[var(--text-3)]">{isAr ? 'المهام المدرجة:' : 'Actions:'}</span>
                    <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                      {w.actions?.length ?? 0}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 6: ACTION BACKLOG (TABLE WITH STATUS PATCH) */}
      {activeTab === 'backlog' && (
        <div className="space-y-4">
          {/* Backlog Filters */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)]">
            <div className="flex items-center gap-3">
              <ListTodo className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-bold text-[var(--text)]">
                {isAr ? 'تصفية قائمة المهام:' : 'Filter Backlog Actions:'}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={backlogPriorityFilter}
                onChange={(e) => setBacklogPriorityFilter(e.target.value)}
                className="text-xs px-3 py-1.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-inset)] text-[var(--text)]"
              >
                <option value="all">{isAr ? 'كافة الأولويات' : 'All Priorities'}</option>
                <option value="P0">P0 — عاجل فوري</option>
                <option value="P1">P1 — أولوية عالية</option>
                <option value="P2">P2 — أولوية متوسطة</option>
                <option value="P3">P3 — تحسين مستمر</option>
              </select>

              <select
                value={backlogStatusFilter}
                onChange={(e) => setBacklogStatusFilter(e.target.value)}
                className="text-xs px-3 py-1.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-inset)] text-[var(--text)]"
              >
                <option value="all">{isAr ? 'كافة الحالات' : 'All Statuses'}</option>
                <option value="pending">{isAr ? 'قيد الانتظار' : 'Pending'}</option>
                <option value="in_progress">{isAr ? 'قيد التنفيذ' : 'In Progress'}</option>
                <option value="verified">{isAr ? 'تم التحقق والإنجاز' : 'Verified'}</option>
                <option value="deferred">{isAr ? 'مؤجل' : 'Deferred'}</option>
              </select>
            </div>
          </div>

          {/* Action Backlog Table */}
          <div className="p-4 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md overflow-x-auto">
            <table className="w-full text-start text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-[var(--hairline)] text-[var(--text-3)] text-start">
                  <th className="py-3 px-3 font-semibold">{isAr ? 'المهمة والمعرف' : 'Action & ID'}</th>
                  <th className="py-3 px-3 font-semibold">{isAr ? 'الأولوية والموجة' : 'Priority & Wave'}</th>
                  <th className="py-3 px-3 font-semibold">{isAr ? 'المالك / الدور' : 'Owner'}</th>
                  <th className="py-3 px-3 font-semibold">{isAr ? 'الأثر والجهد' : 'Impact / Effort'}</th>
                  <th className="py-3 px-3 font-semibold">{isAr ? 'الحالة الحالية' : 'Status'}</th>
                  <th className="py-3 px-3 font-semibold text-end">{isAr ? 'تحديث الحالة' : 'Change Status'}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--hairline)]">
                {filteredBacklog.map((act) => (
                  <tr key={act.action_id} className="hover:bg-[var(--glass-inset)] transition-colors">
                    <td className="py-3.5 px-3 max-w-sm">
                      <div className="font-semibold text-[var(--text)]">
                        {isAr ? act.title_ar || act.title : act.title}
                      </div>
                      <div className="text-[10px] font-mono text-[var(--text-3)] mt-0.5">
                        {act.action_id}
                      </div>
                      <p className="text-xs text-[var(--text-2)] mt-1 line-clamp-2">
                        {isAr ? act.description_ar || act.description : act.description}
                      </p>
                    </td>

                    <td className="py-3.5 px-3">
                      <div className="flex flex-col gap-1">
                        <span
                          className={`inline-block text-[10px] font-mono font-bold px-2 py-0.5 rounded w-max ${
                            act.priority === 'P0'
                              ? 'bg-red-600 text-white'
                              : act.priority === 'P1'
                              ? 'bg-orange-600 text-white'
                              : act.priority === 'P2'
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-600 text-white'
                          }`}
                        >
                          {act.priority}
                        </span>
                        <span className="text-[10px] text-[var(--text-3)] font-mono">
                          Wave {act.wave_number ?? 1}
                        </span>
                      </div>
                    </td>

                    <td className="py-3.5 px-3 text-[var(--text-2)] text-xs">
                      {act.suggested_owner || 'Engineer'}
                    </td>

                    <td className="py-3.5 px-3 text-xs">
                      <div>
                        <span className="text-[10px] text-[var(--text-3)]">{isAr ? 'الأثر: ' : 'Impact: '}</span>
                        <span className="font-semibold text-[var(--text)]">{act.impact_category || 'high'}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-[var(--text-3)]">{isAr ? 'الجهد: ' : 'Effort: '}</span>
                        <span className="text-[var(--text-2)]">{act.effort_estimate || 'medium'}</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-3">
                      <span
                        className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                          act.status === 'verified'
                            ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300'
                            : act.status === 'in_progress'
                            ? 'bg-blue-500/15 text-blue-800 dark:text-blue-300'
                            : act.status === 'deferred'
                            ? 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
                            : 'bg-stone-900/10 text-stone-900 dark:bg-stone-100/10 dark:text-stone-100 font-bold border border-stone-800/20'
                        }`}
                      >
                        {act.status}
                      </span>
                    </td>

                    <td className="py-3.5 px-3 text-end">
                      <select
                        value={act.status}
                        disabled={updatingActionId === act.action_id}
                        onChange={(e) => handleUpdateStatus(act.action_id, e.target.value)}
                        className="text-xs px-2.5 py-1 rounded-lg border border-[var(--hairline)] bg-[var(--glass-inset)] text-[var(--text)] cursor-pointer"
                      >
                        <option value="pending">{isAr ? 'قيد الانتظار' : 'Pending'}</option>
                        <option value="in_progress">{isAr ? 'قيد العمل' : 'In Progress'}</option>
                        <option value="verified">{isAr ? 'تم الإنجاز' : 'Verified'}</option>
                        <option value="deferred">{isAr ? 'تأجيل' : 'Deferred'}</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-TAB 7: VERIFICATION & MEASUREMENT PLANS */}
      {activeTab === 'verification' && (
        <div className="space-y-6">
          {/* Verification Plans */}
          <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
            <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-emerald-500" />
              <span>{isAr ? 'خطط التحقق التقنية المحكمة' : 'Deterministic Verification Procedures'}</span>
            </h3>
            <div className="space-y-3">
              {verificationPlans.map((vp: any, idx: number) => (
                <div
                  key={vp.plan_id || idx}
                  className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] space-y-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[var(--text)]">
                      {isAr ? vp.title_ar || vp.action_id : vp.action_id}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-700 dark:text-emerald-300">
                      {vp.tooling || 'Automated Check'}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-2)] leading-relaxed">
                    {isAr ? vp.procedure_ar || vp.procedure : vp.procedure}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Metric Measurement Plan */}
          <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
            <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-500" />
              <span>{isAr ? 'خطة قياس الأثر والمؤشرات الحيوية' : 'Metric Impact Measurement Plan'}</span>
            </h3>
            <div className="space-y-3">
              {measurementPlans.map((mp: any, idx: number) => (
                <div
                  key={mp.measurement_id || idx}
                  className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[var(--text)]">{mp.metric_name}</span>
                    <span className="text-[10px] font-mono text-[var(--accent)]">{mp.cadence || 'Weekly'}</span>
                  </div>
                  <div className="text-[11px] text-[var(--text-2)]">
                    {isAr ? 'المستوى المرجعي الأساسي: ' : 'Baseline: '} {mp.baseline_value ?? '—'}
                  </div>
                  <div className="text-[11px] text-emerald-700 dark:text-emerald-400 font-medium">
                    {isAr ? 'الهدف المرجو: ' : 'Target Goal: '} {mp.target_value ?? '—'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
