import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  FileText,
  Download,
  Code,
  Sparkles,
  Palette,
  Layout,
  PenTool,
  Zap,
  TrendingUp,
  ShieldCheck,
  Eye,
  Compass,
  Award,
  Check,
  Copy,
  Printer,
  ExternalLink,
  CheckCircle2,
  FileCheck,
  RefreshCw,
} from 'lucide-react';

const STAGE_REPORTS = [
  { id: 'executive_synthesis', label: 'التقرير التنفيذي المؤسسي الموحد وتصدير وثائق PDF (المرحلة 12)', icon: Award, phase: 12 },
  { id: 'strategic_intelligence', label: 'تقرير الذكاء الاستراتيجي وتوليف خارطة الطريق (المرحلة 11)', icon: Compass, phase: 11 },
  { id: 'accessibility', label: 'تقرير إمكانية الوصول والنفاذ الرقمي (WCAG 2.2)', icon: Eye, phase: 10 },
  { id: 'security_privacy', label: 'تقرير أمان الموقع والخصوصية والثقة', icon: ShieldCheck, phase: 9 },
  { id: 'competitor_intelligence', label: 'تقرير استخبارات ومقارنة المنافسين', icon: TrendingUp, phase: 8 },
  { id: 'technical_seo', label: 'تقرير SEO التقني ومؤشرات الأداء', icon: Zap, phase: 7 },
  { id: 'content_marketing', label: 'تقرير المحتوى والتسويق الرقمي', icon: PenTool, phase: 6 },
  { id: 'ux_ui', label: 'تقرير تجربة وواجهة المستخدم', icon: Layout, phase: 5 },
  { id: 'visual_identity', label: 'تقرير الهوية البصرية وتناسق التصميم', icon: Palette, phase: 4 },
];

export function ReportViewer({ runId, stages }: { runId: string; stages: string[] }) {
  const { t, lang } = useLang();
  // Filter only stages available in run or default to executive_synthesis / first
  const availableReports = STAGE_REPORTS.filter(
    (sr) => stages.includes(sr.id) || sr.id === 'executive_synthesis' || stages.length === 0
  );
  const [selectedStage, setSelectedStage] = useState<string>(
    availableReports[0]?.id || 'executive_synthesis'
  );
  const [format, setFormat] = useState<'markdown' | 'json'>('markdown');
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Phase 12 Final PDF reports state
  const [finalReports, setFinalReports] = useState<any[]>([]);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [showIframePreview, setShowIframePreview] = useState(false);

  const fetchFinalReports = () => {
    api
      .getFinalReports(runId)
      .then((data) => setFinalReports(data || []))
      .catch(() => setFinalReports([]));
  };

  useEffect(() => {
    fetchFinalReports();
  }, [runId]);

  useEffect(() => {
    if (!selectedStage) return;
    setLoading(true);

    if (selectedStage === 'executive_synthesis' && finalReports.length > 0) {
      const latest = finalReports[0];
      const targetUrl =
        format === 'markdown'
          ? api.getDownloadReportUrl(runId, latest.report_id, 'md')
          : api.getDownloadReportUrl(runId, latest.report_id, 'json');

      fetch(targetUrl)
        .then((r) => r.text())
        .then((txt) => {
          setContent(txt);
          setLoading(false);
        })
        .catch(() => {
          setContent('# التقرير التنفيذي الشامل\n\nجارٍ إعداد الوثيقة...');
          setLoading(false);
        });
      return;
    }

    api
      .getReport(runId, selectedStage, format)
      .then((res) => {
        setContent(res.content);
        setLoading(false);
      })
      .catch(() => {
        setContent('# تقرير هذه المرحلة غير متاح أو لم يكتمل بعد.\n\nلم يتم توليد ملف التقرير لهذا الوكيل في هذه الجولة.');
        setLoading(false);
      });
  }, [runId, selectedStage, format, finalReports]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], {
      type: format === 'markdown' ? 'text/markdown;charset=utf-8' : 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${selectedStage}-${runId}.${format === 'markdown' ? 'md' : 'json'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleGeneratePdf = async () => {
    setGeneratingPdf(true);
    try {
      await api.generateFinalReport({
        crawl_run_id: runId,
        mode: 'comprehensive',
        language: lang === 'en' ? 'en' : 'ar',
        paper_size: 'A4',
      });
      fetchFinalReports();
    } catch (err) {
      console.error('Failed to generate final report:', err);
    } finally {
      setGeneratingPdf(false);
    }
  };

  const latestPdfReport = finalReports[0];

  return (
    <div className="space-y-6">
      {/* Enterprise PDF Export Card (Phase 12) */}
      <div className="p-6 sm:p-8 rounded-3xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-[var(--glass-tint-strong)] to-[var(--glass-tint)] backdrop-blur-xl shadow-lg relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm border border-stone-800 dark:border-stone-200">
              <Award className="w-4 h-4 text-amber-400 dark:text-amber-600" />
              <span>وثائق أساس للذكاء الاصطناعي — تقرير بصمة الموقع التنفيذي v1.0.0</span>
            </div>
            <h2 className="text-2xl font-black text-[var(--text)] tracking-tight">
              {t('reports.final_title')}
            </h2>
            <p className="text-xs sm:text-sm text-[var(--text-2)] leading-relaxed">
              {t('reports.final_subtitle')}
            </p>

            {latestPdfReport && (
              <div className="flex flex-wrap items-center gap-4 pt-2 text-xs text-[var(--text-2)]">
                <div className="flex items-center gap-1.5 font-mono bg-[var(--hairline)] px-2.5 py-1 rounded-lg">
                  <FileText className="w-3.5 h-3.5 text-amber-500" />
                  <span>{latestPdfReport.report_id}</span>
                </div>
                <div className="flex items-center gap-1 text-emerald-800 dark:text-emerald-300 font-semibold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{latestPdfReport.page_count} صفحات (A4)</span>
                </div>
                <div className="flex items-center gap-1 text-indigo-800 dark:text-indigo-300 font-semibold">
                  <span>التقييم الشامل: {latestPdfReport.overall_score ?? 60}/100</span>
                </div>
                <div className="flex items-center gap-1 text-[var(--text-3)] text-[11px] font-mono">
                  <span>SHA256: {latestPdfReport.sha256_checksum?.slice(0, 12)}...</span>
                </div>
              </div>
            )}
          </div>

          <div className="flex flex-wrap lg:flex-col items-stretch gap-2.5 shrink-0">
            {latestPdfReport ? (
              <>
                <a
                  href={api.getDownloadReportUrl(runId, latestPdfReport.report_id, 'pdf')}
                  download
                  className="flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-[var(--accent-fill)] text-[var(--on-accent)] font-bold text-sm shadow-md hover:shadow-lg hover:scale-102 transition-all cursor-pointer text-decoration-none"
                >
                  <Printer className="w-4 h-4" />
                  <span>{t('reports.download_pdf')}</span>
                </a>
                <button
                  onClick={() => setShowIframePreview(!showIframePreview)}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl border border-[var(--hairline)] hover:bg-[var(--glass-inset)] text-xs font-semibold text-[var(--text)] transition-colors cursor-pointer"
                >
                  <ExternalLink className="w-4 h-4 text-amber-500" />
                  <span>{showIframePreview ? 'إغلاق المعاينة' : t('reports.preview_pdf')}</span>
                </button>
              </>
            ) : (
              <button
                onClick={handleGeneratePdf}
                disabled={generatingPdf}
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl bg-[var(--accent-fill)] text-[var(--on-accent)] font-bold text-sm shadow-md hover:shadow-lg hover:scale-102 transition-all cursor-pointer disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                <span>{generatingPdf ? 'جارٍ التوليد عبر Chromium...' : t('reports.generate_pdf')}</span>
              </button>
            )}

            {latestPdfReport && (
              <button
                onClick={handleGeneratePdf}
                disabled={generatingPdf}
                className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl border border-[var(--hairline)] text-[11px] text-[var(--text-3)] hover:text-[var(--text)] cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3 h-3 ${generatingPdf ? 'animate-spin' : ''}`} />
                <span>إعادة توليد التقرير</span>
              </button>
            )}
          </div>
        </div>

        {/* Browser Iframe Preview */}
        {showIframePreview && latestPdfReport && (
          <div className="mt-6 pt-6 border-t border-[var(--hairline)] space-y-3">
            <div className="flex items-center justify-between text-xs text-[var(--text-2)] font-semibold">
              <span>معاينة حية للوثيقة (HTML / Print View)</span>
              <a
                href={api.getPreviewReportUrl(runId, latestPdfReport.report_id)}
                target="_blank"
                rel="noreferrer"
                className="text-[var(--accent)] hover:underline inline-flex items-center gap-1"
              >
                <span>فتح في نافذة كاملة</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <div className="rounded-2xl border border-[var(--hairline)] overflow-hidden bg-white shadow-inner h-[600px]">
              <iframe
                src={api.getPreviewReportUrl(runId, latestPdfReport.report_id)}
                title="Site DNA Executive Report"
                className="w-full h-full border-0"
              />
            </div>
          </div>
        )}
      </div>

      {/* Stage Selector Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--hairline)] pb-4">
        <div>
          <h3 className="text-base font-bold text-[var(--text)]">{t('reports.title')}</h3>
          <p className="text-xs text-[var(--text-3)]">{t('reports.subtitle')}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Format Toggle */}
          <div className="flex items-center p-1 rounded-xl bg-[var(--hairline)]">
            <button
              onClick={() => setFormat('markdown')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer ${
                format === 'markdown'
                  ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                  : 'text-[var(--text-3)]'
              }`}
            >
              Markdown
            </button>
            <button
              onClick={() => setFormat('json')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer ${
                format === 'json'
                  ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                  : 'text-[var(--text-3)]'
              }`}
            >
              JSON
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-[var(--hairline)] hover:bg-[var(--glass-inset)] text-xs text-[var(--text-2)] hover:text-[var(--text)] cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'تم النسخ' : 'نسخ'}</span>
          </button>

          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[var(--accent-fill)] text-[var(--on-accent)] text-xs font-semibold hover:opacity-90 transition-opacity cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>تحميل</span>
          </button>
        </div>
      </div>

      {/* Report Stage Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto border-b border-[var(--hairline)] pb-3">
        {availableReports.map((item) => {
          const IconComp = item.icon;
          const isActive = selectedStage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setSelectedStage(item.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                isActive
                  ? 'bg-amber-500/20 text-amber-900 dark:text-amber-200 border border-amber-500/40 shadow-sm'
                  : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
              }`}
            >
              <IconComp className="w-4 h-4 text-amber-500" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Report Content Box */}
      <div className="p-6 sm:p-8 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md shadow-inner">
        {loading ? (
          <div className="py-20 text-center text-xs text-[var(--text-3)]">{t('common.loading')}</div>
        ) : format === 'json' ? (
          <pre className="font-mono text-xs text-[var(--text)] overflow-x-auto p-4 rounded-2xl bg-black/20" dir="ltr">
            {content}
          </pre>
        ) : (
          <div className="prose dark:prose-invert max-w-none text-sm text-[var(--text)] leading-relaxed space-y-4 whitespace-pre-wrap font-sans">
            {content}
          </div>
        )}
      </div>
    </div>
  );
}
