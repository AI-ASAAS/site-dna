import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  AlertTriangle,
  ShieldAlert,
  Info,
  Filter,
  CheckCircle2,
  FileCode,
  Globe,
  ChevronDown,
  ChevronUp,
  X,
  ExternalLink,
} from 'lucide-react';

export function FindingsExplorer({ runId }: { runId: string }) {
  const { t } = useLang();
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [agentFilter, setAgentFilter] = useState('all');
  const [selectedFinding, setSelectedFinding] = useState<any | null>(null);

  useEffect(() => {
    api
      .getFindings(runId)
      .then((data) => {
        setFindings(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [runId]);

  const filtered = findings.filter((f) => {
    if (severityFilter !== 'all' && (f.severity || '').toLowerCase() !== severityFilter) {
      return false;
    }
    if (agentFilter !== 'all' && f.agent_id !== agentFilter) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Filters Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--hairline)] pb-4">
        <div>
          <h2 className="text-base font-bold text-[var(--text)]">{t('findings.title')}</h2>
          <p className="text-xs text-[var(--text-3)]">{t('findings.subtitle')}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Agent Filter */}
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-[var(--hairline)] bg-[var(--bg)] text-xs text-[var(--text)] focus:outline-none"
          >
            <option value="all">{t('findings.all_agents')}</option>
            <option value="visual_identity">الهوية البصرية</option>
            <option value="ux_ui">تجربة المستخدم (UX/UI)</option>
            <option value="content_marketing">المحتوى والتسويق</option>
            <option value="technical_seo">SEO التقني والأداء</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-[var(--hairline)] bg-[var(--bg)] text-xs text-[var(--text)] focus:outline-none"
          >
            <option value="all">{t('findings.all_severities')}</option>
            <option value="critical">{t('findings.critical')}</option>
            <option value="high">{t('findings.high')}</option>
            <option value="medium">{t('findings.medium')}</option>
            <option value="low">{t('findings.low')}</option>
          </select>
        </div>
      </div>

      {/* Findings Count Summary */}
      <div className="flex items-center justify-between text-xs text-[var(--text-3)]">
        <span>عرض {filtered.length} من أصل {findings.length} ملاحظة مسجلة</span>
      </div>

      {/* Findings List */}
      {loading ? (
        <div className="py-16 text-center text-xs text-[var(--text-3)]">{t('common.loading')}</div>
      ) : filtered.length > 0 ? (
        <div className="space-y-3.5">
          {filtered.map((f, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-3 hover:border-amber-500/40 transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={f.severity} />
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-[var(--hairline)] text-[var(--text-3)]">
                    {f.finding_id || `F-${idx + 1}`}
                  </span>
                  <span className="text-[11px] text-[var(--accent)] font-semibold">
                    {f.agent_name || f.category}
                  </span>
                </div>
                {f.page_url && (
                  <span className="text-xs font-mono text-[var(--text-3)] truncate max-w-xs" title={f.page_url}>
                    {f.page_url}
                  </span>
                )}
              </div>

              <div>
                <h3 className="font-bold text-sm text-[var(--text)] leading-snug">{f.title}</h3>
                <p className="text-xs text-[var(--text-2)] leading-relaxed mt-1">{f.description}</p>
              </div>

              {f.recommended_action && (
                <div className="p-3 rounded-xl bg-stone-900/5 dark:bg-stone-100/5 border border-stone-800/15 text-xs text-[var(--text-2)] space-y-1">
                  <span className="font-bold text-stone-900 dark:text-stone-100">الإجراء الموصى به:</span>
                  <p>{f.recommended_action}</p>
                </div>
              )}

              {/* Footer Evidence Action */}
              <div className="flex items-center justify-between pt-1 text-[11px] text-[var(--text-3)]">
                <div className="flex items-center gap-3">
                  {f.observation_type && <span>نوع الرصد: {f.observation_type}</span>}
                  {f.evidence_ids && f.evidence_ids.length > 0 && (
                    <span className="font-mono">الأدلة: {f.evidence_ids.join(', ')}</span>
                  )}
                </div>
                {(f.source_excerpt || (f.evidence_ids && f.evidence_ids.length > 0)) && (
                  <button
                    onClick={() => setSelectedFinding(f)}
                    className="text-xs font-semibold text-[var(--accent)] hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <span>{t('findings.evidence_btn')}</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-16 text-center text-xs text-[var(--text-3)]">{t('findings.empty')}</div>
      )}

      {/* Evidence Drawer Modal */}
      {selectedFinding && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm p-4 flex items-center justify-center animate-in fade-in duration-150">
          <div className="max-w-xl w-full bg-[var(--bg)] rounded-3xl border border-[var(--hairline)] p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-3">
              <div>
                <h3 className="font-bold text-sm text-[var(--text)]">دليل الملاحظة المرصودة</h3>
                <span className="text-xs font-mono text-[var(--accent)]">{selectedFinding.finding_id}</span>
              </div>
              <button
                onClick={() => setSelectedFinding(null)}
                className="p-1.5 rounded-lg border border-[var(--hairline)] text-[var(--text-3)] hover:text-[var(--text)]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[var(--text-3)] block mb-1">الصفحة المرتبطة:</span>
                <span className="font-mono text-xs text-[var(--text)] break-all">{selectedFinding.page_url || '—'}</span>
              </div>

              {selectedFinding.source_excerpt && (
                <div>
                  <span className="text-[var(--text-3)] block mb-1">المقتطف أو الكود المصدري المباشر (Source Excerpt):</span>
                  <pre className="p-3 rounded-xl bg-black/20 font-mono text-[11px] overflow-x-auto text-[var(--text)]" dir="ltr">
                    {selectedFinding.source_excerpt}
                  </pre>
                </div>
              )}

              {selectedFinding.evidence_ids && (
                <div>
                  <span className="text-[var(--text-3)] block mb-1">معرفات الأدلة المصدرية (Evidence IDs):</span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedFinding.evidence_ids.map((id: string) => (
                      <span key={id} className="px-2 py-0.5 rounded bg-[var(--hairline)] font-mono text-[10px]">
                        {id}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedFinding.potential_technical_impact && (
                <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/20 text-red-800 dark:text-red-300">
                  <span className="font-bold block mb-1">الأثر التقني المتوقع:</span>
                  <span>{selectedFinding.potential_technical_impact}</span>
                </div>
              )}
            </div>

            <div className="pt-2 text-end">
              <button
                onClick={() => setSelectedFinding(null)}
                className="px-4 py-2 rounded-xl bg-[var(--accent-fill)] text-[var(--on-accent)] font-semibold text-xs cursor-pointer"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SeverityBadge({ severity }: { severity?: string }) {
  const s = (severity || 'low').toLowerCase();
  if (s === 'critical') {
    return (
      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-500/15 text-red-800 dark:text-red-300 border border-red-500/30">
        حرج
      </span>
    );
  }
  if (s === 'high') {
    return (
      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-orange-500/15 text-orange-800 dark:text-orange-300 border border-orange-500/30">
        مرتفع
      </span>
    );
  }
  if (s === 'medium') {
    return (
      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-orange-600 text-white shadow-xs">
        متوسط
      </span>
    );
  }
  return (
    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/15 text-blue-800 dark:text-blue-300 border border-blue-500/30">
      منخفض
    </span>
  );
}
