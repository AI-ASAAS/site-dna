import React from 'react';
import type { RunRecord } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  Palette,
  Layout,
  PenTool,
  Zap,
  Info,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Clock,
  Layers,
} from 'lucide-react';

export function AnalysisOverview({ run }: { run: RunRecord }) {
  const { t, lang } = useLang();

  const scoreItems = [
    {
      key: 'visual_identity',
      name: 'الهوية البصرية',
      nameEn: 'Visual Identity',
      icon: Palette,
      score: run.scores?.visual_identity,
      phase: 4,
    },
    {
      key: 'ux_ui',
      name: 'تجربة وواجهة المستخدم',
      nameEn: 'UX/UI Usability',
      icon: Layout,
      score: run.scores?.ux_ui,
      phase: 5,
    },
    {
      key: 'content_marketing',
      name: 'المحتوى والتسويق الرقمي',
      nameEn: 'Content & Marketing',
      icon: PenTool,
      score: run.scores?.content_marketing,
      phase: 6,
    },
    {
      key: 'technical_seo',
      name: 'SEO التقني ومؤشرات الأداء',
      nameEn: 'Technical SEO & Performance',
      icon: Zap,
      score: run.scores?.technical_seo,
      phase: 7,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Overall Score & Dimension Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {scoreItems.map((item) => {
          const IconComp = item.icon;
          const hasScore = item.score !== null && item.score !== undefined;
          return (
            <div
              key={item.key}
              className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-3"
            >
              <div className="flex items-center justify-between text-[var(--text-3)]">
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[var(--hairline)]">
                  Phase {String(item.phase).padStart(2, '0')}
                </span>
                <IconComp className="w-4 h-4 text-amber-500" />
              </div>
              <div>
                <div className="text-3xl font-black text-[var(--text)] font-mono">
                  {hasScore ? (
                    <>
                      {item.score} <span className="text-xs font-normal text-[var(--text-3)]">/ 100</span>
                    </>
                  ) : (
                    <span className="text-xs font-semibold text-[var(--text-3)]">غير متاح</span>
                  )}
                </div>
                <div className="font-bold text-xs text-[var(--text)] mt-1">
                  {lang === 'ar' ? item.name : item.nameEn}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Analysis Metrics Grid */}
      <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
        <h3 className="font-bold text-sm text-[var(--text)] flex items-center gap-2">
          <Layers className="w-4 h-4 text-amber-500" />
          <span>ملخص إحصاءات الجولة الميدانية</span>
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] space-y-1">
            <span className="text-[var(--text-3)]">إجمالي الملاحظات</span>
            <div className="text-xl font-bold font-mono text-[var(--text)]">{run.total_findings}</div>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] space-y-1">
            <span className="text-[var(--text-3)]">التوصيات العلاجية</span>
            <div className="text-xl font-bold font-mono text-indigo-700 dark:text-indigo-400">{run.total_recommendations}</div>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] space-y-1">
            <span className="text-[var(--text-3)]">المدة الكلية للتنفيذ</span>
            <div className="text-xl font-bold font-mono text-[var(--text)]">{(run.total_duration_ms / 1000).toFixed(1)} ثانية</div>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] space-y-1">
            <span className="text-[var(--text-3)]">المراحل المنفذة</span>
            <div className="text-xl font-bold font-mono text-emerald-700 dark:text-emerald-400">
              {Object.values(run.stages).filter((s) => s.status === 'completed' || s.status === 'ai_blocked').length}
            </div>
          </div>
        </div>
      </div>

      {/* Scientific Boundaries & Limitations Disclaimer */}
      <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-amber-500/5 text-xs text-[var(--text-2)] space-y-2">
        <div className="flex items-center gap-2 font-bold text-amber-800 dark:text-amber-300">
          <Info className="w-4 h-4 text-amber-600 dark:text-amber-400" />
          <span>الحدود الهندسية والنزاهة العلمية للتقييم (Scientific Boundaries)</span>
        </div>
        <ul className="list-disc list-inside space-y-1 text-[11px] leading-relaxed text-[var(--text-3)]">
          <li><strong>الفهرسة الفعلية:</strong> يؤكد النظام قابلية الصفحة الفنية للأرشفة، ولا يدعي مطلقاً فهرستها الفعلية في محرك بحث جوجل بدون إذن مباشر من Google Search Console.</li>
          <li><strong>مؤشر INP:</strong> يتطلب تفاعل مستخدمين بشريين حقيقيين؛ ويتم تسجيله كـ غير مقاس لمنع التلفيق المعملي.</li>
          <li><strong>المقاييس المعملية:</strong> قياسات الأداء LCP/CLS مستخلصة من بيئة كروميوم المعملية المحلية تحت ظروف محاكاة.</li>
        </ul>
      </div>
    </div>
  );
}
