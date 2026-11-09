import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

export function RecommendationsViewer({ runId }: { runId: string }) {
  const { t } = useLang();
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState('all');

  useEffect(() => {
    api
      .getRecommendations(runId)
      .then((data) => {
        setRecommendations(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [runId]);

  const filtered = recommendations.filter((r) => {
    if (priorityFilter === 'all') return true;
    return (r.priority || '').toLowerCase() === priorityFilter.toLowerCase();
  });

  return (
    <div className="space-y-6">
      {/* Priority Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--hairline)] pb-4">
        <div>
          <h2 className="text-base font-bold text-[var(--text)]">{t('recs.title')}</h2>
          <p className="text-xs text-[var(--text-3)]">{t('recs.subtitle')}</p>
        </div>

        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[var(--hairline)]">
          <button
            onClick={() => setPriorityFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              priorityFilter === 'all'
                ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            الكل ({recommendations.length})
          </button>
          <button
            onClick={() => setPriorityFilter('p1')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              priorityFilter === 'p1'
                ? 'bg-red-500/15 text-red-700 dark:text-red-300 shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            P1 قصوى
          </button>
          <button
            onClick={() => setPriorityFilter('p2')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              priorityFilter === 'p2'
                ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            P2 متوسطة
          </button>
          <button
            onClick={() => setPriorityFilter('p3')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              priorityFilter === 'p3'
                ? 'bg-blue-500/15 text-blue-700 dark:text-blue-300 shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            P3 روتينية
          </button>
        </div>
      </div>

      {/* Recommendations Cards */}
      {loading ? (
        <div className="py-16 text-center text-xs text-[var(--text-3)]">{t('common.loading')}</div>
      ) : filtered.length > 0 ? (
        <div className="space-y-4">
          {filtered.map((rec, idx) => {
            const prio = (rec.priority || 'p3').toLowerCase();
            return (
              <div
                key={idx}
                className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4 hover:border-amber-500/30 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <PriorityPill priority={prio} />
                    <h3 className="font-bold text-sm text-[var(--text)]">{rec.title}</h3>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-[var(--text-3)] font-mono">
                    {rec.estimated_effort && <span>الجهد: {rec.estimated_effort}</span>}
                    {rec.stage_id && <span className="text-[var(--accent)] font-semibold">{rec.stage_id}</span>}
                  </div>
                </div>

                {rec.problem_statement && (
                  <div className="text-xs text-[var(--text-2)] leading-relaxed">
                    <span className="font-semibold text-[var(--text)]">المشكلة المرصودة: </span>
                    {rec.problem_statement}
                  </div>
                )}

                {rec.proposed_solution && (
                  <div className="p-3.5 rounded-2xl bg-[var(--bg)] border border-[var(--hairline)] text-xs text-[var(--text)] space-y-1">
                    <span className="font-bold text-stone-900 dark:text-stone-100 block">الحل المقترح (Proposed Solution):</span>
                    <p className="leading-relaxed">{rec.proposed_solution}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
                  {rec.expected_benefit && (
                    <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300">
                      <span className="font-bold block mb-1">الأثر والعائد المتوقع:</span>
                      <span>{rec.expected_benefit}</span>
                    </div>
                  )}

                  {rec.verification_method && (
                    <div className="p-3 rounded-xl bg-blue-500/5 border border-blue-500/20 text-blue-800 dark:text-blue-300">
                      <span className="font-bold block mb-1">طريقة التحقق من نجاح الحل:</span>
                      <span>{rec.verification_method}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="py-16 text-center text-xs text-[var(--text-3)]">{t('recs.empty')}</div>
      )}
    </div>
  );
}

function PriorityPill({ priority }: { priority: string }) {
  if (priority === 'p1' || priority === 'high') {
    return (
      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-500/15 text-red-800 dark:text-red-300 border border-red-500/30">
        P1 أولوية قصوى
      </span>
    );
  }
  if (priority === 'p2' || priority === 'medium') {
    return (
      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-orange-600 text-white shadow-xs">
        P2 أولوية متوسطة
      </span>
    );
  }
  return (
    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-500/15 text-blue-800 dark:text-blue-300 border border-blue-500/30">
      P3 تحسين روتيني
    </span>
  );
}
