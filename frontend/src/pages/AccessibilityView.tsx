import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  Eye,
  Keyboard,
  Layers,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Sparkles,
  Info,
  ExternalLink,
  ClipboardList,
  Check,
  Copy,
  Languages,
  Monitor,
  MousePointer,
  HelpCircle,
  FileCheck,
} from 'lucide-react';

interface AccessibilityViewProps {
  runId: string;
}

export function AccessibilityView({ runId }: AccessibilityViewProps) {
  const { lang } = useLang();
  const [report, setReport] = useState<any>(null);
  const [wcagList, setWcagList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedRecId, setCopiedRecId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'wcag' | 'manual' | 'contrast' | 'keyboard' | 'recs'>('overview');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getAccessibilityReport(runId).catch(() => null),
      api.getWcagCriteria(runId).catch(() => []),
    ])
      .then(([rep, criteria]) => {
        setReport(rep);
        setWcagList(criteria || []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [runId]);

  const handleUpdateTaskStatus = async (reviewId: string, newStatus: string) => {
    try {
      await api.updateManualReviewTask(runId, reviewId, newStatus, 'Verified by human reviewer');
      // Update local state
      if (report && report.manual_review_tasks) {
        const updated = report.manual_review_tasks.map((t: any) =>
          t.review_id === reviewId ? { ...t, review_status: newStatus } : t
        );
        setReport({ ...report, manual_review_tasks: updated });
      }
    } catch (e) {
      console.error('Failed to update manual task:', e);
    }
  };

  const copySnippet = (recId: string, snippet: string) => {
    navigator.clipboard.writeText(snippet);
    setCopiedRecId(recId);
    setTimeout(() => setCopiedRecId(null), 2000);
  };

  if (loading) {
    return (
      <div className="p-12 text-center space-y-3">
        <div className="w-10 h-10 mx-auto rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-500 animate-spin">
          <Eye className="w-5 h-5" />
        </div>
        <p className="text-sm font-bold text-[var(--text)]">
          {lang === 'ar' ? 'جاري تحميل تدقيق إمكانية الوصول والنفاذ الرقمي (WCAG 2.2)...' : 'Loading Accessibility & WCAG 2.2 Audit...'}
        </p>
        <p className="text-xs text-[var(--text-3)]">
          {lang === 'ar'
            ? 'فحص البنية الدلالية، شجرة الأسماء المتاحة، لوحة المفاتيح، والتباين البصري'
            : 'Auditing semantics, accessible names, keyboard navigation, and color contrast'}
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
            {lang === 'ar' ? 'لا يتوفر تقرير إمكانية وصول لهذه الجولة بعد' : 'No Accessibility Audit Available'}
          </h3>
          <p className="text-xs text-[var(--text-3)] max-w-md mx-auto">
            {lang === 'ar'
              ? 'تأكد من اختيار مرحلة "إمكانية الوصول الرقمي (WCAG 2.2)" عند إطلاق الفحص، أو انتظر اكتمال تحليلها.'
              : 'Ensure the Accessibility stage was selected when launching the analysis run.'}
          </p>
        </div>
      </div>
    );
  }

  const scores = report.scores || {};
  const overallScore = scores.overall_score ?? 0;
  const isGood = overallScore >= 75;
  const isMedium = overallScore >= 50 && overallScore < 75;

  const tabs = [
    { id: 'overview', labelAr: 'نظرة عامة والدرجات', labelEn: 'Overview & Scores' },
    { id: 'wcag', labelAr: `معايير WCAG 2.2 (${wcagList.length || 14})`, labelEn: `WCAG Criteria (${wcagList.length || 14})` },
    { id: 'manual', labelAr: `مهام المراجعة البشرية (${report.manual_review_tasks?.length || 0})`, labelEn: `Manual Review (${report.manual_review_tasks?.length || 0})` },
    { id: 'contrast', labelAr: 'التباين والألوان', labelEn: 'Color Contrast' },
    { id: 'keyboard', labelAr: 'لوحة المفاتيح والتركيز', labelEn: 'Keyboard & Focus' },
    { id: 'recs', labelAr: 'خارطة التوصيات (P1–P3)', labelEn: 'Remediation Roadmap' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* 1. Mandatory Disclaimer Alert */}
      <div className="p-4 rounded-2xl border border-blue-500/20 bg-blue-500/10 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs leading-relaxed text-blue-900 dark:text-blue-200">
          <span className="font-bold">
            {lang === 'ar' ? 'تقييم استرشادي غير تدخلي ممتثل للأنظمة: ' : 'Informative Accessibility Assessment: '}
          </span>
          {lang === 'ar' ? scores.conformance_disclaimer_ar : scores.conformance_disclaimer}
        </div>
      </div>

      {/* 2. Top Posture Score Card */}
      <div className="p-6 sm:p-8 rounded-3xl border border-[var(--glass-rim)] bg-gradient-to-br from-[var(--glass-tint-strong)] to-[var(--glass-tint)] backdrop-blur-xl shadow-lg relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm border border-stone-800 dark:border-stone-200">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 dark:text-amber-600" />
              <span>Phase 10 — استخبارات إمكانية الوصول والنفاذ الرقمي</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-[var(--text)] tracking-tight">
              {lang === 'ar' ? 'مؤشر النفاذ الرقمي وتجربة المستخدم الشاملة' : 'Web Accessibility & Inclusive Experience Posture'}
            </h1>
            <p className="text-xs text-[var(--text-3)] font-mono">
              {report.target_url}
            </p>
          </div>

          <div className="flex items-center gap-4 bg-[var(--glass-inset)] p-4 rounded-2xl border border-[var(--hairline)] shrink-0">
            <div className={`w-16 h-16 rounded-2xl flex flex-col items-center justify-center font-black ${
              isGood
                ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30'
                : isMedium
                ? 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30'
                : 'bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-500/30'
            }`}>
              <span className="text-2xl leading-none">{overallScore}</span>
              <span className="text-[10px] opacity-70">/ 100</span>
            </div>
            <div>
              <div className="text-xs text-[var(--text-3)] font-medium">
                {lang === 'ar' ? 'التقييم المركب' : 'Composite Score'}
              </div>
              <div className="text-sm font-bold text-[var(--text)]">
                {lang === 'ar' ? scores.score_label_ar : scores.score_label}
              </div>
              <div className="text-[11px] text-[var(--text-3)]">
                {lang === 'ar' ? `${report.statistics?.pages_evaluated || 1} صفحات ممثلة` : `${report.statistics?.pages_evaluated || 1} Sampled Pages`}
              </div>
            </div>
          </div>
        </div>

        {/* 6 Posture Dimension Scores Matrix */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-6 pt-6 border-t border-[var(--hairline)]">
          <div className="p-3.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-tint)] text-center space-y-1">
            <div className="text-[11px] text-[var(--text-3)] flex items-center justify-center gap-1">
              <Layers className="w-3 h-3 text-amber-500" />
              <span>{lang === 'ar' ? 'البنية الدلالية (20%)' : 'Semantics (20%)'}</span>
            </div>
            <div className="text-lg font-extrabold text-[var(--text)]">{scores.semantics_names_score ?? 0}</div>
          </div>

          <div className="p-3.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-tint)] text-center space-y-1">
            <div className="text-[11px] text-[var(--text-3)] flex items-center justify-center gap-1">
              <Keyboard className="w-3 h-3 text-amber-500" />
              <span>{lang === 'ar' ? 'لوحة المفاتيح (20%)' : 'Keyboard (20%)'}</span>
            </div>
            <div className="text-lg font-extrabold text-[var(--text)]">{scores.keyboard_focus_score ?? 0}</div>
          </div>

          <div className="p-3.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-tint)] text-center space-y-1">
            <div className="text-[11px] text-[var(--text-3)] flex items-center justify-center gap-1">
              <Eye className="w-3 h-3 text-amber-500" />
              <span>{lang === 'ar' ? 'التباين البصري (20%)' : 'Contrast (20%)'}</span>
            </div>
            <div className="text-lg font-extrabold text-[var(--text)]">{scores.visual_contrast_score ?? 0}</div>
          </div>

          <div className="p-3.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-tint)] text-center space-y-1">
            <div className="text-[11px] text-[var(--text-3)] flex items-center justify-center gap-1">
              <ClipboardList className="w-3 h-3 text-amber-500" />
              <span>{lang === 'ar' ? 'النماذج وحقولها (15%)' : 'Forms (15%)'}</span>
            </div>
            <div className="text-lg font-extrabold text-[var(--text)]">{scores.forms_interaction_score ?? 0}</div>
          </div>

          <div className="p-3.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-tint)] text-center space-y-1">
            <div className="text-[11px] text-[var(--text-3)] flex items-center justify-center gap-1">
              <MousePointer className="w-3 h-3 text-amber-500" />
              <span>{lang === 'ar' ? 'بنية التنقل (15%)' : 'Navigation (15%)'}</span>
            </div>
            <div className="text-lg font-extrabold text-[var(--text)]">{scores.navigation_structure_score ?? 0}</div>
          </div>

          <div className="p-3.5 rounded-xl border border-[var(--hairline)] bg-[var(--glass-tint)] text-center space-y-1">
            <div className="text-[11px] text-[var(--text-3)] flex items-center justify-center gap-1">
              <Languages className="w-3 h-3 text-amber-500" />
              <span>{lang === 'ar' ? 'اللغة والوسائط (10%)' : 'Language (10%)'}</span>
            </div>
            <div className="text-lg font-extrabold text-[var(--text)]">{scores.language_media_score ?? 0}</div>
          </div>
        </div>
      </div>

      {/* 3. Sub-Navigation Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto border-b border-[var(--hairline)] pb-2 text-xs font-semibold no-scrollbar">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer ${
              activeTab === tab.id
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            {lang === 'ar' ? tab.labelAr : tab.labelEn}
          </button>
        ))}
      </div>

      {/* 4. Tab: Overview & Scores */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-2">
              <div className="text-xs text-[var(--text-3)] font-medium">
                {lang === 'ar' ? 'العينة الممثلة المختارة' : 'Representative Sample'}
              </div>
              <div className="text-2xl font-bold text-[var(--text)]">
                {report.sampling?.sampled_pages_count || 0} / {report.sampling?.total_pages_discovered || 0}
              </div>
              <div className="text-[11px] text-[var(--text-3)]">
                {lang === 'ar' ? 'صفحات وفق معيار WCAG-EM 2.0' : 'Pages evaluated under WCAG-EM 2.0'}
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-2">
              <div className="text-xs text-[var(--text-3)] font-medium">
                {lang === 'ar' ? 'حواجز النفاذ المؤكدة' : 'Confirmed Barriers'}
              </div>
              <div className="text-2xl font-bold text-rose-600 dark:text-rose-400">
                {report.statistics?.confirmed_failures_count || 0}
              </div>
              <div className="text-[11px] text-[var(--text-3)]">
                {lang === 'ar' ? 'مخالفات حتمية تتطلب إصلاحاً' : 'Deterministic failures requiring fix'}
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-2">
              <div className="text-xs text-[var(--text-3)] font-medium">
                {lang === 'ar' ? 'مهام المراجعة اليدوية' : 'Manual Review Queue'}
              </div>
              <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                {report.statistics?.manual_review_tasks_count || 0}
              </div>
              <div className="text-[11px] text-[var(--text-3)]">
                {lang === 'ar' ? 'تتطلب تدقيقاً بشرياً مخصصاً' : 'Dimensions requiring human review'}
              </div>
            </div>
          </div>

          {/* Key Findings List */}
          <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
            <h3 className="text-sm font-bold text-[var(--text)] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400" />
              <span>{lang === 'ar' ? 'ملخص حواجز إمكانية الوصول المرصودة' : 'Observed Accessibility Barriers Summary'}</span>
            </h3>

            <div className="space-y-3">
              {(report.findings || []).map((f: any, idx: number) => (
                <div key={idx} className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-sm text-[var(--text)]">
                      {lang === 'ar' ? f.title_ar : f.title}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      f.severity === 'critical' ? 'bg-rose-500/20 text-rose-700 dark:text-rose-300' : 'bg-orange-500/20 text-orange-950 dark:text-orange-200 border border-orange-500/40'
                    }`}>
                      {f.severity}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-2)] leading-relaxed">
                    {lang === 'ar' ? f.description_ar : f.description}
                  </p>
                  <div className="text-[11px] text-[var(--accent)] font-medium">
                    {lang === 'ar' ? 'الإصلاح المقترح:' : 'Recommended Fix:'} {lang === 'ar' ? f.recommended_fix_ar : f.recommended_fix}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 5. Tab: WCAG Criteria Explorer */}
      {activeTab === 'wcag' && (
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
          <div>
            <h3 className="text-base font-bold text-[var(--text)]">
              {lang === 'ar' ? 'مصفوفة معايير WCAG 2.2 (المستويات A و AA)' : 'WCAG 2.2 Success Criteria Matrix (A/AA)'}
            </h3>
            <p className="text-xs text-[var(--text-3)]">
              {lang === 'ar'
                ? 'تدقيق ومطابقة الأدلة المرصودة مع معايير النفاذ العالمية مع توثيق طريقة الفحص وحدوده'
                : 'Mapping observable evidence against WCAG criteria with clear test method boundaries'}
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-start">
              <thead>
                <tr className="border-b border-[var(--hairline)] text-[var(--text-3)]">
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'المعيار' : 'Criterion'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'الاسم' : 'Name'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'المستوى' : 'Level'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'الحالة' : 'Status'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'طريقة الفحص' : 'Test Method'}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--hairline)]">
                {wcagList.map((crit: any, idx: number) => (
                  <tr key={idx} className="hover:bg-[var(--glass-inset)] transition-colors">
                    <td className="py-2.5 font-mono font-bold text-[var(--text)]">{crit.criterion_id}</td>
                    <td className="py-2.5 text-[var(--text)] font-medium">
                      {lang === 'ar' ? crit.criterion_name_ar : crit.criterion_name}
                    </td>
                    <td className="py-2.5">
                      <span className="px-2 py-0.5 rounded bg-[var(--glass-inset)] font-bold text-[10px] text-[var(--text-2)]">
                        Level {crit.conformance_level}
                      </span>
                    </td>
                    <td className="py-2.5">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[10px] ${
                        crit.status === 'confirmed_failure'
                          ? 'bg-rose-500/15 text-rose-700 dark:text-rose-400'
                          : crit.status === 'passed_specific_check'
                          ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400'
                          : crit.status === 'manual_review_required'
                          ? 'bg-blue-500/15 text-blue-700 dark:text-blue-400'
                          : 'bg-orange-500/15 text-orange-950 dark:text-orange-200 border border-orange-500/30'
                      }`}>
                        {crit.status === 'confirmed_failure' && <XCircle className="w-3 h-3" />}
                        {crit.status === 'passed_specific_check' && <CheckCircle2 className="w-3 h-3" />}
                        {crit.status === 'manual_review_required' && <HelpCircle className="w-3 h-3" />}
                        <span>
                          {crit.status === 'confirmed_failure'
                            ? lang === 'ar' ? 'حاجز مؤكد' : 'Failure'
                            : crit.status === 'passed_specific_check'
                            ? lang === 'ar' ? 'اجتاز الفحص' : 'Passed Check'
                            : crit.status === 'manual_review_required'
                            ? lang === 'ar' ? 'مراجعة بشرية' : 'Manual Review'
                            : lang === 'ar' ? 'ملاحظة محتملة' : 'Potential Issue'}
                        </span>
                      </span>
                    </td>
                    <td className="py-2.5 font-mono text-[10px] text-[var(--text-3)]">{crit.test_method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 6. Tab: Manual Review Queue */}
      {activeTab === 'manual' && (
        <div className="space-y-4">
          <div className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)]">
            <h3 className="text-sm font-bold text-[var(--text)] flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-blue-500" />
              <span>{lang === 'ar' ? 'قائمة مهام المراجعة البشرية المخصصة' : 'Human Review Workflow Queue'}</span>
            </h3>
            <p className="text-xs text-[var(--text-3)] mt-1">
              {lang === 'ar'
                ? 'جوانب النفاذ التي لا يمكن للأدوات الآلية إثباتها قطعياً وتتطلب تجربة عملية واعية من متخصص بشري.'
                : 'Accessibility dimensions that require direct human verification and evaluation.'}
            </p>
          </div>

          <div className="space-y-4">
            {(report.manual_review_tasks || []).map((task: any, idx: number) => (
              <div key={idx} className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--hairline)] pb-3">
                  <div>
                    <span className="font-mono text-[10px] text-[var(--text-3)] block">{task.wcag_criterion}</span>
                    <h4 className="font-bold text-sm text-[var(--text)]">
                      {lang === 'ar' ? task.review_question_ar : task.review_question}
                    </h4>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold shrink-0 self-start sm:self-center ${
                    task.review_status === 'manually_verified_pass'
                      ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300'
                      : task.review_status === 'manually_verified_fail'
                      ? 'bg-rose-500/20 text-rose-700 dark:text-rose-300'
                      : 'bg-orange-500/20 text-orange-950 dark:text-orange-200 border border-orange-500/40'
                  }`}>
                    {task.review_status === 'manually_verified_pass'
                      ? lang === 'ar' ? 'تم الاعتماد (مطابق)' : 'Verified Pass'
                      : task.review_status === 'manually_verified_fail'
                      ? lang === 'ar' ? 'تم التوثيق (مخالف)' : 'Verified Fail'
                      : lang === 'ar' ? 'بانتظار المراجعة' : 'Pending Review'}
                  </span>
                </div>

                <div className="text-xs text-[var(--text-2)] bg-[var(--glass-inset)] p-3 rounded-xl border border-[var(--hairline)] space-y-1">
                  <span className="font-bold text-[var(--text)]">
                    {lang === 'ar' ? 'لماذا يتعذر الحسم الآلي؟' : 'Why automation is insufficient:'}
                  </span>
                  <p>{lang === 'ar' ? task.why_automation_is_insufficient_ar : task.why_automation_is_insufficient}</p>
                </div>

                <div className="space-y-1 text-xs">
                  <span className="font-bold text-[var(--text)]">
                    {lang === 'ar' ? 'خطوات التحقق اليدوي الموصى بها:' : 'Manual verification steps:'}
                  </span>
                  <ol className="list-decimal list-inside space-y-0.5 text-[var(--text-2)]">
                    {(lang === 'ar' ? task.manual_steps_ar : task.manual_steps || []).map((st: string, sIdx: number) => (
                      <li key={sIdx}>{st}</li>
                    ))}
                  </ol>
                </div>

                {/* Reviewer Actions */}
                <div className="flex items-center gap-2 pt-2 border-t border-[var(--hairline)]">
                  <button
                    onClick={() => handleUpdateTaskStatus(task.review_id, 'manually_verified_pass')}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 text-xs font-bold hover:bg-emerald-500/25 transition-colors cursor-pointer"
                  >
                    {lang === 'ar' ? 'اعتماد النجاح' : 'Mark as Pass'}
                  </button>
                  <button
                    onClick={() => handleUpdateTaskStatus(task.review_id, 'manually_verified_fail')}
                    className="px-3 py-1.5 rounded-lg bg-rose-500/15 text-rose-700 dark:text-rose-300 text-xs font-bold hover:bg-rose-500/25 transition-colors cursor-pointer"
                  >
                    {lang === 'ar' ? 'توثيق الإخفاق' : 'Mark as Fail'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Tab: Color Contrast */}
      {activeTab === 'contrast' && (
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
          <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
            <Eye className="w-5 h-5 text-amber-500" />
            <span>{lang === 'ar' ? 'قياسات تباين ألوان النصوص (WCAG 1.4.3)' : 'Text Color Contrast Measurements'}</span>
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-start">
              <thead>
                <tr className="border-b border-[var(--hairline)] text-[var(--text-3)]">
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'العينة النصية' : 'Text Sample'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'اللون الأمامي' : 'Foreground'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'الخلفية' : 'Background'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'نسبة التباين' : 'Ratio'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'الحد الأدنى' : 'Required'}</th>
                  <th className="py-2.5 text-start">{lang === 'ar' ? 'النتيجة' : 'Result'}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--hairline)]">
                {(report.contrast?.sample_measurements || []).map((m: any, idx: number) => (
                  <tr key={idx} className="hover:bg-[var(--glass-inset)]">
                    <td className="py-2.5 font-medium text-[var(--text)] max-w-xs truncate">{m.text_sample}</td>
                    <td className="py-2.5 font-mono">{m.foreground_color}</td>
                    <td className="py-2.5 font-mono">{m.background_color}</td>
                    <td className="py-2.5 font-bold font-mono text-sm">{m.contrast_ratio}:1</td>
                    <td className="py-2.5 font-mono text-[var(--text-3)]">{m.required_ratio}:1</td>
                    <td className="py-2.5">
                      <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                        m.meets_threshold
                          ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400'
                          : 'bg-rose-500/15 text-rose-700 dark:text-rose-400'
                      }`}>
                        {m.meets_threshold ? (lang === 'ar' ? 'مطابق' : 'Pass') : (lang === 'ar' ? 'مخالف' : 'Fail')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 8. Tab: Keyboard & Focus */}
      {activeTab === 'keyboard' && (
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
          <h3 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
            <Keyboard className="w-5 h-5 text-amber-500" />
            <span>{lang === 'ar' ? 'جاهزية التنقل بلوحة المفاتيح والتركيز المرئي' : 'Keyboard Navigation & Focus Readiness'}</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] space-y-1">
              <span className="text-xs text-[var(--text-3)]">{lang === 'ar' ? 'رابط تجاوز التنقل (Skip Link)' : 'Skip Navigation Link'}</span>
              <div className="flex items-center gap-2 font-bold text-sm text-[var(--text)]">
                {report.keyboard_focus?.skip_link_present ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-500" />
                )}
                <span>
                  {report.keyboard_focus?.skip_link_present
                    ? lang === 'ar' ? 'متوفر في أعلى الصفحة' : 'Present'
                    : lang === 'ar' ? 'غير متوفر' : 'Missing'}
                </span>
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-inset)] space-y-1">
              <span className="text-xs text-[var(--text-3)]">{lang === 'ar' ? 'مؤشرات التركيز المرئية (:focus-visible)' : 'Focus Indicators Visibility'}</span>
              <div className="flex items-center gap-2 font-bold text-sm text-[var(--text)]">
                {report.keyboard_focus?.focus_indicators_visible ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-500" />
                )}
                <span>
                  {report.keyboard_focus?.focus_indicators_visible
                    ? lang === 'ar' ? 'واضحة وغير ملغاة' : 'Visible'
                    : lang === 'ar' ? 'ملغاة عبر outline:none' : 'Suppressed'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 9. Tab: Remediation Roadmap */}
      {activeTab === 'recs' && (
        <div className="space-y-4">
          {(report.recommendations || []).map((rec: any, idx: number) => (
            <div key={idx} className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-3">
              <div className="flex items-center justify-between gap-3 border-b border-[var(--hairline)] pb-3">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-black ${
                    rec.priority === 'P1'
                      ? 'bg-rose-500/20 text-rose-700 dark:text-rose-300'
                      : rec.priority === 'P2'
                      ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300'
                      : 'bg-blue-500/20 text-blue-700 dark:text-blue-300'
                  }`}>
                    {rec.priority}
                  </span>
                  <h4 className="font-bold text-base text-[var(--text)]">
                    {lang === 'ar' ? rec.title_ar : rec.title}
                  </h4>
                </div>
              </div>

              <div className="text-xs text-[var(--text-2)] space-y-1">
                <p><span className="font-bold text-[var(--text)]">{lang === 'ar' ? 'الحاجز المرصود:' : 'Observed Barrier:'}</span> {lang === 'ar' ? rec.observed_barrier_ar : rec.observed_barrier}</p>
                <p><span className="font-bold text-[var(--text)]">{lang === 'ar' ? 'الحل المقترح:' : 'Remediation:'}</span> {lang === 'ar' ? rec.recommended_remediation_ar : rec.recommended_remediation}</p>
              </div>

              {rec.code_snippet && (
                <div className="relative rounded-xl overflow-hidden border border-[var(--hairline)] bg-neutral-900 text-neutral-100 p-4 font-mono text-xs">
                  <div className="flex justify-between items-center mb-2 pb-1 border-b border-neutral-800 text-[10px] text-neutral-400">
                    <span>{lang === 'ar' ? 'كود الإصلاح المقترح' : 'Remediation Code'}</span>
                    <button
                      onClick={() => copySnippet(rec.recommendation_id, rec.code_snippet)}
                      className="inline-flex items-center gap-1 hover:text-white transition-colors cursor-pointer"
                    >
                      {copiedRecId === rec.recommendation_id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedRecId === rec.recommendation_id ? (lang === 'ar' ? 'تم النسخ!' : 'Copied!') : (lang === 'ar' ? 'نسخ' : 'Copy')}</span>
                    </button>
                  </div>
                  <pre className="overflow-x-auto">{rec.code_snippet}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
