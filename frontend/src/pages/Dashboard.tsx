import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, type DashboardSummary } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  FileSearch,
  Sparkles,
  ArrowUpRight,
  PlusCircle,
  Globe,
  Layers,
  Clock,
  ShieldAlert,
} from 'lucide-react';

export function Dashboard() {
  const { t, lang } = useLang();
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getDashboardSummary()
      .then((data) => {
        setSummary(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch dashboard data');
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Hero Welcome & Quick Launch */}
      <div className="relative overflow-hidden rounded-3xl p-6 sm:p-8 border border-[var(--glass-rim)] bg-gradient-to-br from-[var(--glass-tint-strong)] to-[var(--glass-tint)] backdrop-blur-xl shadow-lg">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm border border-stone-800 dark:border-stone-200">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 dark:text-amber-600" />
              <span>{t('app.brand')} — AI Website Intelligence</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--text)]">
              {t('dash.title')}
            </h1>
            <p className="text-sm sm:text-base text-[var(--text-2)] leading-relaxed">
              {t('dash.subtitle')}
            </p>
          </div>
          <button
            onClick={() => navigate('/analyses/new')}
            className="flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-2xl bg-[var(--accent-fill)] text-[var(--on-accent)] font-bold text-base shadow-lg hover:shadow-xl hover:scale-102 active:scale-98 transition-all shrink-0 cursor-pointer"
          >
            <PlusCircle className="w-5 h-5" />
            <span>{t('dash.new_btn')}</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Runs */}
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-2">
          <div className="flex items-center justify-between text-[var(--text-3)]">
            <span className="text-xs font-medium">{t('dash.total_runs')}</span>
            <Activity className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-[var(--text)]">
            {loading ? '...' : summary?.total_runs ?? 0}
          </div>
          <div className="text-[11px] text-[var(--text-3)]">إجمالي الفحوصات المسجلة</div>
        </div>

        {/* Completed Runs */}
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-2">
          <div className="flex items-center justify-between text-[var(--text-3)]">
            <span className="text-xs font-medium">{t('dash.completed_runs')}</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-700 dark:text-emerald-400">
            {loading ? '...' : summary?.completed_runs ?? 0}
          </div>
          <div className="text-[11px] text-[var(--text-3)]">جولات مكتملة بنجاح</div>
        </div>

        {/* Active Runs */}
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-2">
          <div className="flex items-center justify-between text-[var(--text-3)]">
            <span className="text-xs font-medium">{t('dash.active_runs')}</span>
            <Clock className="w-4 h-4 text-blue-500 animate-spin" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-blue-700 dark:text-blue-400">
            {loading ? '...' : summary?.running_runs ?? 0}
          </div>
          <div className="text-[11px] text-[var(--text-3)]">قيد التنفيذ والمتابعة</div>
        </div>

        {/* Findings Count */}
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-2">
          <div className="flex items-center justify-between text-[var(--text-3)]">
            <span className="text-xs font-medium">{t('dash.findings_count')}</span>
            <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-orange-900 dark:text-orange-300 font-mono">
            {loading ? '...' : summary?.total_findings ?? 0}
          </div>
          <div className="text-[11px] text-[var(--text-3)]">مشاكل وملاحظات موثقة</div>
        </div>

        {/* Strategic Recs */}
        <div className="col-span-2 lg:col-span-1 p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-2">
          <div className="flex items-center justify-between text-[var(--text-3)]">
            <span className="text-xs font-medium">{t('dash.recs_count')}</span>
            <FileSearch className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-indigo-700 dark:text-indigo-400">
            {loading ? '...' : summary?.total_recommendations ?? 0}
          </div>
          <div className="text-[11px] text-[var(--text-3)]">توصيات علاجية P1–P3</div>
        </div>
      </div>

      {/* Agent Platform Readiness Matrix (Phases 01-12) */}
      <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--hairline)] pb-3">
          <div>
            <h2 className="text-lg font-bold text-[var(--text)]">{t('dash.agent_readiness')}</h2>
            <p className="text-xs text-[var(--text-3)]">
              كافة المراحل (01–12) مكتملة ومحققة بنسبة 100% وجاهزة للتنفيذ وتصدير تقارير PDF المؤسسية
            </p>
          </div>
          <Link
            to="/agents"
            className="text-xs font-semibold text-[var(--accent)] hover:underline inline-flex items-center gap-1 self-start sm:self-auto"
          >
            <span>{t('nav.agents')}</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {summary?.agent_readiness &&
            Object.entries(summary.agent_readiness).map(([agentId, info]: [string, any]) => {
              const isReady = info.status === 'ready' || info.can_execute !== false;
              return (
                <div
                  key={agentId}
                  className={`p-3.5 rounded-2xl border transition-all ${
                    isReady
                      ? 'border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/10'
                      : 'border-slate-500/20 bg-slate-500/5 opacity-75'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--hairline)] text-[var(--text-3)]">
                      Phase {String(info.phase).padStart(2, '0')}
                    </span>
                    <span
                      className={`w-2 h-2 rounded-full ${
                        isReady ? 'bg-emerald-500' : 'bg-slate-400'
                      }`}
                    />
                  </div>
                  <div className="font-semibold text-xs text-[var(--text)] truncate" title={lang === 'ar' ? info.name_ar : info.name}>
                    {lang === 'ar' ? info.name_ar : info.name}
                  </div>
                  <div className="mt-1 text-[10px] text-[var(--text-3)]">
                    {isReady ? (
                      <span className="text-emerald-700 dark:text-emerald-400 font-medium">جاهز للتشغيل</span>
                    ) : (
                      <span className="text-amber-800 dark:text-amber-400">قريبًا (مخطط)</span>
                    )}
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Recent Analyses List */}
      <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--hairline)] pb-3">
          <div>
            <h2 className="text-lg font-bold text-[var(--text)]">{t('dash.recent_title')}</h2>
            <p className="text-xs text-[var(--text-3)]">{t('dash.recent_subtitle')}</p>
          </div>
          <Link
            to="/history"
            className="text-xs font-semibold text-[var(--accent)] hover:underline inline-flex items-center gap-1 self-start sm:self-auto"
          >
            <span>{t('nav.history')}</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-[var(--text-3)]">{t('common.loading')}</div>
        ) : summary?.recent_runs && summary.recent_runs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-start text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-[var(--hairline)] text-[var(--text-3)] text-start">
                  <th className="py-3 px-3 font-semibold">{t('history.url')}</th>
                  <th className="py-3 px-3 font-semibold">{t('history.status')}</th>
                  <th className="py-3 px-3 font-semibold">{t('history.score')}</th>
                  <th className="py-3 px-3 font-semibold">{t('history.stages')}</th>
                  <th className="py-3 px-3 font-semibold text-end">{t('history.action')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--hairline)]">
                {summary.recent_runs.map((r: any) => (
                  <tr key={r.run_id} className="hover:bg-[var(--glass-inset)] transition-colors">
                    <td className="py-3.5 px-3">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-amber-500 shrink-0" />
                        <div className="min-w-0">
                          <div className="font-semibold text-[var(--text)] truncate max-w-xs sm:max-w-sm">
                            {r.url}
                          </div>
                          <div className="text-[11px] font-mono text-[var(--text-3)]">{r.run_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-3">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="py-3.5 px-3 font-bold">
                      {r.overall_score !== null && r.overall_score !== undefined ? (
                        <span className="text-amber-800 dark:text-amber-300 font-mono">
                          {r.overall_score} <span className="text-[10px] text-[var(--text-3)]">/ 100</span>
                        </span>
                      ) : (
                        <span className="text-[var(--text-3)]">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 text-[var(--text-2)]">
                      <span className="font-mono text-xs">
                        {r.stages_completed} / {r.total_stages || 4}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 text-end">
                      <Link
                        to={`/analyses/${r.run_id}`}
                        className="px-3 py-1.5 rounded-lg border border-[var(--hairline)] hover:border-[var(--accent)] text-xs font-semibold text-[var(--text)] hover:text-[var(--accent)] transition-all"
                      >
                        {t('dash.view_run')}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-16 text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-3xl bg-amber-500/10 flex items-center justify-center text-amber-500">
              <Layers className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-base text-[var(--text)]">{t('dash.empty_title')}</h3>
              <p className="text-xs text-[var(--text-3)] max-w-md mx-auto">{t('dash.empty_desc')}</p>
            </div>
            <button
              onClick={() => navigate('/analyses/new')}
              className="px-5 py-2.5 rounded-xl bg-[var(--accent-fill)] text-[var(--on-accent)] font-semibold text-xs shadow hover:scale-102 transition-all cursor-pointer"
            >
              {t('dash.new_btn')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  if (s === 'completed') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30">
        <CheckCircle2 className="w-3 h-3" /> مكتمل
      </span>
    );
  }
  if (s === 'running' || s === 'queued' || s === 'created') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/15 text-blue-800 dark:text-blue-300 border border-blue-500/30">
        <Clock className="w-3 h-3 animate-spin" /> قيد التنفيذ
      </span>
    );
  }
  if (s === 'ai_blocked' || s === 'partial') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-600 text-white shadow-xs border border-orange-700">
        <AlertTriangle className="w-3 h-3 text-white" /> جزئي / حظر حصة
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-600 text-white shadow-xs border border-red-700">
      <ShieldAlert className="w-3 h-3 text-white" /> تعثر
    </span>
  );
}
