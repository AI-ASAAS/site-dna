import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type RunRecord } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  History as HistoryIcon,
  Search,
  Globe,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  Filter,
} from 'lucide-react';

export function History() {
  const { t } = useLang();
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);

  const fetchHistory = () => {
    setLoading(true);
    api
      .getRuns({ query: search || undefined, status: statusFilter !== 'all' ? statusFilter : undefined, page, page_size: 15 })
      .then((res) => {
        setRuns(res.items);
        setTotal(res.total);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHistory();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchHistory();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm border border-stone-800 dark:border-stone-200">
            <HistoryIcon className="w-3.5 h-3.5 text-stone-300 dark:text-stone-700" />
            <span>أرشيف وسجل التحليلات الميدانية</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[var(--text)] tracking-tight">
            {t('history.title')}
          </h1>
          <p className="text-sm text-[var(--text-2)]">{t('history.subtitle')}</p>
        </div>

        <Link
          to="/analyses/new"
          className="px-4 py-2.5 rounded-2xl bg-[var(--accent-fill)] text-[var(--on-accent)] font-bold text-xs shadow hover:opacity-90 transition-opacity self-start sm:self-auto"
        >
          {t('dash.new_btn')}
        </Link>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('history.search_placeholder')}
            className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-[var(--hairline)] bg-[var(--bg)] text-xs text-[var(--text)] placeholder-[var(--text-3)] focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
          <Search className="w-4 h-4 text-[var(--text-3)] absolute left-3.5 top-3" />
        </form>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="px-3.5 py-2.5 rounded-2xl border border-[var(--hairline)] bg-[var(--bg)] text-xs text-[var(--text)] focus:outline-none cursor-pointer"
        >
          <option value="all">كافة الحالات</option>
          <option value="completed">مكتمل بنجاح</option>
          <option value="running">قيد التنفيذ</option>
          <option value="ai_blocked">حظر حصة AI / جزئي</option>
          <option value="failed">متعثر</option>
        </select>
      </div>

      {/* History Table Card */}
      <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md">
        {loading ? (
          <div className="py-20 text-center text-xs text-[var(--text-3)]">{t('common.loading')}</div>
        ) : runs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-start text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-[var(--hairline)] text-[var(--text-3)] text-start">
                  <th className="py-3 px-3 font-semibold">{t('history.url')}</th>
                  <th className="py-3 px-3 font-semibold">{t('history.date')}</th>
                  <th className="py-3 px-3 font-semibold">{t('history.status')}</th>
                  <th className="py-3 px-3 font-semibold">{t('history.score')}</th>
                  <th className="py-3 px-3 font-semibold">{t('history.stages')}</th>
                  <th className="py-3 px-3 font-semibold text-end">{t('history.action')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--hairline)]">
                {runs.map((r) => (
                  <tr key={r.run_id} className="hover:bg-[var(--glass-inset)] transition-colors">
                    <td className="py-3.5 px-3">
                      <div className="flex items-center gap-2.5">
                        <Globe className="w-4 h-4 text-amber-500 shrink-0" />
                        <div className="min-w-0">
                          <div className="font-semibold text-[var(--text)] truncate max-w-xs sm:max-w-md">
                            {r.url}
                          </div>
                          <div className="text-[11px] font-mono text-[var(--text-3)]">{r.run_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-3 text-xs text-[var(--text-3)] whitespace-nowrap">
                      {new Date(r.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-3">
                      <HistoryStatusBadge status={r.status} />
                    </td>
                    <td className="py-3.5 px-3 font-bold font-mono">
                      {r.overall_score !== null && r.overall_score !== undefined ? (
                        <span className="text-amber-800 dark:text-amber-300">
                          {r.overall_score} <span className="text-[10px] text-[var(--text-3)]">/ 100</span>
                        </span>
                      ) : (
                        <span className="text-[var(--text-3)]">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 font-mono text-xs text-[var(--text-2)]">
                      {Object.values(r.stages).filter((s) => s.status === 'completed').length} /{' '}
                      {Object.keys(r.stages).length}
                    </td>
                    <td className="py-3.5 px-3 text-end">
                      <Link
                        to={`/analyses/${r.run_id}`}
                        className="px-3.5 py-1.5 rounded-xl border border-[var(--hairline)] hover:border-[var(--accent)] text-xs font-semibold text-[var(--text)] hover:text-[var(--accent)] transition-all"
                      >
                        {t('history.open')}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-16 text-center text-xs text-[var(--text-3)]">
            لم يتم العثور على أي جولات تحليل تطابق معايير البحث.
          </div>
        )}
      </div>
    </div>
  );
}

function HistoryStatusBadge({ status }: { status: string }) {
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
        <AlertTriangle className="w-3 h-3 text-white" /> جزئي
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-600 text-white shadow-xs border border-red-700">
      <ShieldAlert className="w-3 h-3 text-white" /> متعثر
    </span>
  );
}
