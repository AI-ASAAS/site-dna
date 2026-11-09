import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, type RunSubmissionRequest } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  Globe,
  Camera,
  Palette,
  Layout,
  PenTool,
  Zap,
  TrendingUp,
  Users,
  MousePointer,
  ShieldCheck,
  Award,
  Eye,
  Compass,
  CheckSquare,
  Square,
  Sparkles,
  AlertCircle,
  HelpCircle,
  Play,
  Cpu,
  CheckCircle2,
  FileText,
} from 'lucide-react';

interface StageOption {
  id: string;
  phase: number;
  nameKey: string;
  name: string;
  nameAr: string;
  descKey: string;
  desc: string;
  descAr: string;
  icon: React.ComponentType<{ className?: string }>;
  canExecute: boolean;
  requiresVisual: boolean;
}

const AVAILABLE_STAGES: StageOption[] = [
  {
    id: 'discovery',
    phase: 2,
    nameKey: 'agent.discovery',
    name: 'Website Discovery & Crawling',
    nameAr: 'استكشاف وزحف الموقع',
    descKey: 'agent.discovery.desc',
    desc: 'Crawl sitemaps, robots.txt, extract links, headers, and raw HTML.',
    descAr: 'زحف مسارات الموقع، فحص robots.txt وخريطة الموقع وجمع كود HTML.',
    icon: Globe,
    canExecute: true,
    requiresVisual: false,
  },
  {
    id: 'visual_capture',
    phase: 3,
    nameKey: 'agent.visual',
    name: 'Browser Rendering & Visual Evidence',
    nameAr: 'التصيير المتصفحي والأدلة البصرية',
    descKey: 'agent.visual.desc',
    desc: 'Render in Chromium, capture desktop & mobile screenshots, extract DOM & CSS.',
    descAr: 'التقاط صور لسطح المكتب والجوال عبر المتصفح واستخراج الأنماط وشجرة DOM.',
    icon: Camera,
    canExecute: true,
    requiresVisual: false,
  },
  {
    id: 'visual_identity',
    phase: 4,
    nameKey: 'agent.vi',
    name: 'Visual Identity Analyst',
    nameAr: 'محلل الهوية البصرية',
    descKey: 'agent.vi.desc',
    desc: 'Multimodal typography, color palette contrast, layout harmony, and logo audit.',
    descAr: 'تدقيق الألوان المتناسقة، الخطوط، توزيع المساحات، وتماسك الهوية البصرية.',
    icon: Palette,
    canExecute: true,
    requiresVisual: true,
  },
  {
    id: 'ux_ui',
    phase: 5,
    nameKey: 'agent.ux',
    name: 'UX/UI Usability Analyst',
    nameAr: 'محلل تجربة وواجهة المستخدم',
    descKey: 'agent.ux.desc',
    desc: 'Interactive usability, CTA prominence, form ergonomics, and mobile layout.',
    descAr: 'فحص سهولة التنقل، وضوح أزرار اتخاذ القرار CTA، ونماذج البيانات.',
    icon: Layout,
    canExecute: true,
    requiresVisual: true,
  },
  {
    id: 'content_marketing',
    phase: 6,
    nameKey: 'agent.content',
    name: 'Content & Marketing Intelligence',
    nameAr: 'ذكاء المحتوى والتسويق الرقمي',
    descKey: 'agent.content.desc',
    desc: 'Value proposition audit, brand tone consistency, and conversion copywriting.',
    descAr: 'تحليل صياغة القيمة المقترحة، نبرة الصوت التسويقية، ونصوص الإقناع.',
    icon: PenTool,
    canExecute: true,
    requiresVisual: false,
  },
  {
    id: 'technical_seo',
    phase: 7,
    nameKey: 'agent.seo',
    name: 'Technical SEO & Performance Analyst',
    nameAr: 'محلل SEO التقني ومؤشرات الأداء',
    descKey: 'agent.seo.desc',
    desc: 'Crawlability, canonical consistency, Core Web Vitals (LCP/CLS), and JSON-LD schema.',
    descAr: 'فحص إمكانية الأرشفة، مؤشرات Core Web Vitals، والبيانات المنظمة JSON-LD.',
    icon: Zap,
    canExecute: true,
    requiresVisual: false,
  },
  {
    id: 'competitor_intelligence',
    phase: 8,
    nameKey: 'agent.competitor',
    name: 'Competitor Intelligence & Benchmark',
    nameAr: 'استخبارات المنافسين والمقارنة المعيارية',
    descKey: 'agent.competitor.desc',
    desc: 'Autonomous AI discovery of the top 3 closest industry competitors and comprehensive benchmarking of features, pricing, and positioning.',
    descAr: 'استكشاف آلي ذكي لأقرب 3 منافسين لقطاع موقعك، مصفوفة الخصائص، مقارنة الأسعار، وكشف الفجوات والتموضع التنافسي.',
    icon: TrendingUp,
    canExecute: true,
    requiresVisual: true,
  },
  {
    id: 'security_privacy',
    phase: 9,
    nameKey: 'agent.security',
    name: 'Security, Privacy & Digital Trust',
    nameAr: 'أمان الموقع والخصوصية والثقة الرقمية',
    descKey: 'agent.security.desc',
    desc: 'Passive HTTPS transport, 8 security headers, CSP defense, cookie security, and privacy disclosures.',
    descAr: 'تدقيق دفاعي سلبي للتشفير، 8 ترويسات أمان، درع CSP، أمان ملفات تعريف الارتباط، وإفصاحات الخصوصية.',
    icon: ShieldCheck,
    canExecute: true,
    requiresVisual: false,
  },
  {
    id: 'accessibility',
    phase: 10,
    nameKey: 'agent.accessibility',
    name: 'Web Accessibility & WCAG 2.2',
    nameAr: 'إمكانية الوصول والنفاذ الرقمي (WCAG 2.2)',
    descKey: 'agent.accessibility.desc',
    desc: 'W3C WCAG 2.2 Level A/AA conformance, semantics, keyboard navigation, contrast, and manual review tasks.',
    descAr: 'فحص إمكانية الوصول والنفاذ الرقمي الشامل وفق معايير W3C WCAG 2.2 والمستويات A و AA، فحص التباين واللوحة والمسميات.',
    icon: Eye,
    canExecute: true,
    requiresVisual: false,
  },
  {
    id: 'strategic_intelligence',
    phase: 11,
    nameKey: 'agent.strategic',
    name: 'Strategic Intelligence & Unified Roadmap',
    nameAr: 'الذكاء الاستراتيجي وتوليف خارطة الطريق الموحدة',
    descKey: 'agent.strategic.desc',
    desc: 'Cross-agent synthesis, deduplication, conflict resolution, and 4-wave prioritized action backlog.',
    descAr: 'توليف متقاطع بين كافة الوكلاء، دمج الملاحظات المكررة، حل التعارضات التقنية، وتوليد خطة عمل ذات 4 موجات تنفيذية.',
    icon: Compass,
    canExecute: true,
    requiresVisual: false,
  },
  {
    id: 'executive_synthesis',
    phase: 12,
    nameKey: 'agent.executive',
    name: 'Final Reporting & Enterprise PDF Export',
    nameAr: 'التقرير التنفيذي المؤسسي وتصدير وثائق PDF المعتمدة',
    descKey: 'agent.executive.desc',
    desc: 'Production-ready Arabic RTL PDF reports with official Thmanyah fonts, evidence grounding, and 20-point quality verification.',
    descAr: 'توليد التقارير التنفيذية الرسمية وتصدير وثائق PDF عالية الجودة والطباعة بخطوط ثمانية وأصول أساس للذكاء الاصطناعي مع التحقق الآلي.',
    icon: Award,
    canExecute: true,
    requiresVisual: true,
  },
];

const FUTURE_STAGES: StageOption[] = [];

export function NewAnalysis() {
  const { t, lang } = useLang();
  const navigate = useNavigate();

  const [url, setUrl] = useState('');
  // User selects which stages to run (default all implemented analysis stages selected)
  const [selectedStages, setSelectedStages] = useState<string[]>([
    'discovery',
    'visual_capture',
    'visual_identity',
    'ux_ui',
    'content_marketing',
    'technical_seo',
    'competitor_intelligence',
    'security_privacy',
    'accessibility',
  ]);
  const [maxPages, setMaxPages] = useState(5);
  const [isFullScan, setIsFullScan] = useState(false);
  const [deterministicOnly, setDeterministicOnly] = useState(false);
  const [offlineMode, setOfflineMode] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleStage = (stageId: string) => {
    setSelectedStages((prev) =>
      prev.includes(stageId) ? prev.filter((s) => s !== stageId) : [...prev, stageId]
    );
  };

  const selectAll = () => {
    setSelectedStages(AVAILABLE_STAGES.map((s) => s.id));
  };

  const deselectAll = () => {
    setSelectedStages([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanUrl = url.trim();
    if (!cleanUrl) {
      setError(t('new.error_invalid_url'));
      return;
    }
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      setError(t('new.error_invalid_url'));
      return;
    }
    if (selectedStages.length === 0) {
      setError(t('new.error_no_agents'));
      return;
    }

    setSubmitting(true);
    try {
      const payload: RunSubmissionRequest = {
        url: cleanUrl,
        stages: selectedStages,
        max_pages: isFullScan ? 50 : maxPages,
        full_site_scan: isFullScan,
        deterministic_only: deterministicOnly,
        offline_mode: offlineMode,
        competitor_urls: [], // Autonomous agent discovery will find Top 3 closest competitors
      };
      const created = await api.submitRun(payload);
      navigate(`/analyses/${created.run_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit analysis');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="space-y-2 border-b border-[var(--hairline)] pb-5">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm border border-stone-800 dark:border-stone-200">
          <Sparkles className="w-3.5 h-3.5 text-amber-400 dark:text-amber-600" />
          <span>{t('app.brand')} — Phase 12 (Release Candidate)</span>
        </div>
        <h1 className="text-3xl font-extrabold text-[var(--text)] tracking-tight">
          {t('new.title')}
        </h1>
        <p className="text-sm text-[var(--text-2)]">{t('new.subtitle')}</p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl border border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* URL Input Card */}
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
          <label className="block text-sm font-bold text-[var(--text)]">
            {t('new.url_label')} <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={t('new.url_placeholder')}
              className="w-full px-4 py-3.5 rounded-2xl border border-[var(--hairline)] bg-[var(--bg)] text-[var(--text)] text-base font-mono focus:outline-none focus:ring-2 focus:ring-amber-500/50 shadow-inner"
              dir="ltr"
            />
          </div>
          <div className="text-xs text-[var(--text-3)] flex items-center gap-1.5">
            <HelpCircle className="w-4 h-4 text-stone-500" />
            <span>{t('new.url_hint')}</span>
          </div>
        </div>



        {/* Agent Selection Header & Controls */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--hairline)] pb-3">
            <div>
              <h2 className="text-lg font-bold text-[var(--text)]">{t('new.select_agents')}</h2>
              <p className="text-xs text-[var(--text-3)]">
                اختر الوكلاء المطلوب تشغيلهم فقط (يمكنك اختيار واحد فقط أو أكثر أو الكل)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={selectAll}
                className="px-3 py-1.5 rounded-xl border border-[var(--hairline)] text-xs font-semibold text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)] transition-colors cursor-pointer"
              >
                {t('new.select_all')}
              </button>
              <button
                type="button"
                onClick={deselectAll}
                className="px-3 py-1.5 rounded-xl border border-[var(--hairline)] text-xs font-semibold text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)] transition-colors cursor-pointer"
              >
                {t('new.deselect_all')}
              </button>
            </div>
          </div>

          {/* Implemented & Ready Agents (Phases 02-07) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {AVAILABLE_STAGES.map((stage) => {
              const isSelected = selectedStages.includes(stage.id);
              const IconComp = stage.icon;

              return (
                <div
                  key={stage.id}
                  onClick={() => toggleStage(stage.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer select-none flex items-start gap-3.5 ${
                    isSelected
                      ? 'border-stone-800/40 bg-stone-900/5 dark:border-stone-200/40 dark:bg-stone-100/10 shadow-xs ring-1 ring-stone-800/20'
                      : 'border-[var(--hairline)] bg-[var(--glass-tint)] hover:bg-[var(--glass-inset)] opacity-90'
                  }`}
                >
                  <div className="pt-0.5 text-stone-900 dark:text-stone-100">
                    {isSelected ? (
                      <CheckSquare className="w-5 h-5 text-stone-900 dark:text-stone-100" />
                    ) : (
                      <Square className="w-5 h-5 text-[var(--text-3)]" />
                    )}
                  </div>
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <IconComp className="w-4 h-4 text-stone-800 dark:text-stone-200 shrink-0" />
                        <span className="font-bold text-sm text-[var(--text)]">
                          {lang === 'ar' ? stage.nameAr : stage.name}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30">
                        Phase {String(stage.phase).padStart(2, '0')}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-2)] leading-relaxed">
                      {lang === 'ar' ? stage.descAr : stage.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Planned / Future Agents (Phases 08-12) - VISIBLE BUT DISABLED */}
          <div className="pt-4 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[var(--text-3)] uppercase tracking-wider">
              <Cpu className="w-4 h-4 text-slate-400" />
              <span>وكلاء المراحل المستقبلية المخططة (المراحل 08–12) — غير قابلة للتشغيل حاليًا</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {FUTURE_STAGES.map((stage) => {
                const IconComp = stage.icon;
                return (
                  <div
                    key={stage.id}
                    className="p-4 rounded-2xl border border-dashed border-slate-500/30 bg-slate-500/5 opacity-65 cursor-not-allowed select-none flex items-start gap-3.5"
                    title={t('new.planned_badge')}
                  >
                    <div className="pt-0.5 text-slate-400">
                      <Square className="w-5 h-5" />
                    </div>
                    <div className="space-y-1 flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                          <IconComp className="w-4 h-4 shrink-0" />
                          <span className="font-bold text-sm line-through">
                            {lang === 'ar' ? stage.nameAr : stage.name}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-500/20 text-slate-600 dark:text-slate-300 border border-slate-500/30">
                          Phase {String(stage.phase).padStart(2, '0')}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-3)]">
                        {lang === 'ar' ? stage.descAr : stage.desc}
                      </p>
                      <div className="text-[11px] font-semibold text-stone-600 dark:text-stone-400 mt-1">
                        🔒 {t('new.planned_badge')}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Advanced Options */}
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-5">
          <h3 className="font-bold text-sm text-[var(--text)]">خيارات التحليل المتقدمة ونطاق الفحص</h3>

          {/* Scope Selector: Custom pages limit vs Full & Comprehensive Site Scan */}
          <div className="space-y-2">
            <label className="block text-xs font-bold text-[var(--text)]">
              {t('new.scope_label')}
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setIsFullScan(false)}
                className={`p-3.5 rounded-2xl border text-start transition-all cursor-pointer ${
                  !isFullScan
                    ? 'border-stone-800/40 bg-stone-900/5 dark:border-stone-200/40 dark:bg-stone-100/10 shadow-xs ring-1 ring-stone-800/20'
                    : 'border-[var(--hairline)] bg-[var(--bg)] opacity-70 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-xs text-[var(--text)] flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-stone-700 dark:text-stone-300" />
                    {t('new.scope_limited')}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-stone-900/10 text-stone-900 dark:bg-stone-100/10 dark:text-stone-100 font-bold">
                    محدد
                  </span>
                </div>
                <p className="text-[11px] text-[var(--text-3)] leading-relaxed">
                  فحص سريع ومخصص بعدد صفحات محدد لتسريع وقت التحليل وإنجاز التقرير في ثوانٍ.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setIsFullScan(true)}
                className={`p-3.5 rounded-2xl border text-start transition-all cursor-pointer ${
                  isFullScan
                    ? 'border-emerald-600/40 bg-emerald-600/5 dark:border-emerald-400/40 dark:bg-emerald-400/10 shadow-xs ring-1 ring-emerald-600/20'
                    : 'border-[var(--hairline)] bg-[var(--bg)] opacity-70 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-xs text-emerald-900 dark:text-emerald-200 flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-emerald-600" />
                    {t('new.scope_full')}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-600 text-white shadow-xs">
                    كامل الموقع 🌐
                  </span>
                </div>
                <p className="text-[11px] text-[var(--text-3)] leading-relaxed">
                  فحص شامل وزحف معمق لكافة صفحات ومسارات الموقع المكتشفة في الخريطة والروابط الداخلية.
                </p>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            {!isFullScan ? (
              <div>
                <label className="block text-xs font-semibold text-[var(--text-2)] mb-1.5">
                  {t('new.max_pages_label')}
                </label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={maxPages}
                  onChange={(e) => setMaxPages(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-[var(--hairline)] bg-[var(--bg)] text-[var(--text)] text-sm font-mono"
                />
              </div>
            ) : (
              <div className="p-3.5 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-900 dark:text-emerald-200 text-xs flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span className="leading-relaxed">
                  <strong>وضع الفحص الشامل مفعل:</strong> ستقوم المنظومة باكتشاف وزحف كافة مسارات وصفحات الموقع المتاحة تلقائياً دون تقييد بعدد صفحات.
                </span>
              </div>
            )}

            <div className="space-y-2 pt-1">
              <label className="flex items-center gap-2.5 text-xs text-[var(--text-2)] cursor-pointer">
                <input
                  type="checkbox"
                  checked={deterministicOnly}
                  onChange={(e) => setDeterministicOnly(e.target.checked)}
                  className="rounded text-stone-800 focus:ring-stone-600"
                />
                <span>{t('new.mode_deterministic')}</span>
              </label>
              <label className="flex items-center gap-2.5 text-xs text-[var(--text-2)] cursor-pointer">
                <input
                  type="checkbox"
                  checked={offlineMode}
                  onChange={(e) => setOfflineMode(e.target.checked)}
                  className="rounded text-stone-800 focus:ring-stone-600"
                />
                <span>{t('new.mode_offline')}</span>
              </label>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="px-5 py-3 rounded-2xl border border-[var(--hairline)] text-sm font-semibold text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)] transition-colors cursor-pointer"
          >
            {t('common.back')}
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="flex items-center gap-2.5 px-8 py-3.5 rounded-2xl bg-[var(--accent-fill)] text-[var(--on-accent)] font-bold text-base shadow-lg hover:shadow-xl hover:scale-102 active:scale-98 transition-all disabled:opacity-50 cursor-pointer"
          >
            {submitting ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>{t('new.starting')}</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5 fill-current" />
                <span>{t('new.start_btn')}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
