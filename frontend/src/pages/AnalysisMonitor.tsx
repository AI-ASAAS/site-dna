import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useRunEvents } from '../lib/useRunEvents';
import { useLang } from '../lib/i18n';
import {
  Globe,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Camera,
  Search,
  Sparkles,
  Download,
  RefreshCw,
  ShieldAlert,
  ArrowUpRight,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react';

import { AnalysisOverview } from './AnalysisOverview';
import { ScreenshotExplorer } from './ScreenshotExplorer';
import { FindingsExplorer } from './FindingsExplorer';
import { RecommendationsViewer } from './RecommendationsViewer';
import { CompetitorIntelligenceView } from './CompetitorIntelligenceView';
import { SecurityPrivacyView } from './SecurityPrivacyView';
import { AccessibilityView } from './AccessibilityView';
import { StrategicIntelligenceView } from './StrategicIntelligenceView';
import { AIAutomationView } from './AIAutomationView';
import { ReportViewer } from './ReportViewer';

type TabType = 'monitor' | 'overview' | 'screenshots' | 'findings' | 'recommendations' | 'ai_automation' | 'competitors' | 'security' | 'accessibility' | 'strategic' | 'reports';

export function AnalysisMonitor() {
  const { runId } = useParams<{ runId: string }>();
  const { run, events, loading, error, refresh } = useRunEvents(runId);
  const { t, lang } = useLang();
  const [activeTab, setActiveTab] = useState<TabType>('monitor');

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3 animate-pulse">
        <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-500/20 flex items-center justify-center text-amber-500">
          <Clock className="w-6 h-6 animate-spin" />
        </div>
        <div className="font-bold text-base text-[var(--text)]">{t('common.loading')}</div>
        <div className="text-xs text-[var(--text-3)]">جاري جلب تفاصيل الجولة وحالات الوكلاء...</div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="p-8 rounded-3xl border border-red-500/30 bg-red-500/10 text-center space-y-4 max-w-lg mx-auto">
        <ShieldAlert className="w-12 h-12 mx-auto text-red-500" />
        <h2 className="text-lg font-bold text-red-700 dark:text-red-300">تعذر تحميل بيانات الجولة</h2>
        <p className="text-xs text-[var(--text-2)]">{error || 'Run not found'}</p>
        <Link
          to="/history"
          className="inline-block px-4 py-2 rounded-xl bg-[var(--accent-fill)] text-[var(--on-accent)] text-xs font-semibold"
        >
          العودة لسجل التحليلات
        </Link>
      </div>
    );
  }

  const isRunning = run.status === 'running' || run.status === 'queued' || run.status === 'created';
  const hasAiBlock = run.status === 'ai_blocked' || Object.values(run.stages).some((s) => s.status === 'ai_blocked');

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Breadcrumb & Metadata Card */}
      <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-3)]">
              <span>Run ID:</span>
              <span className="font-bold text-[var(--accent)]">{run.run_id}</span>
              <span>•</span>
              <span>{new Date(run.created_at).toLocaleString(lang === 'ar' ? 'ar-SA' : 'en-US')}</span>
            </div>
            <div className="flex items-center gap-3">
              <Globe className="w-6 h-6 text-amber-500 shrink-0" />
              <h1 className="text-2xl sm:text-3xl font-black text-[var(--text)] tracking-tight truncate max-w-xl">
                {run.url}
              </h1>
              <a
                href={run.url}
                target="_blank"
                rel="noreferrer"
                className="p-1.5 rounded-lg border border-[var(--hairline)] text-[var(--text-3)] hover:text-[var(--text)]"
                title="Open website in new tab"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <RunStatusPill status={run.status} />
            <button
              onClick={refresh}
              className="p-2 rounded-xl border border-[var(--hairline)] hover:bg-[var(--glass-inset)] text-[var(--text-2)] hover:text-[var(--text)] transition-all cursor-pointer"
              title={t('common.refresh')}
            >
              <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Quota Warning Alert */}
        {hasAiBlock && (
          <div className="p-3.5 rounded-2xl border border-orange-500/40 bg-orange-500/10 text-xs text-orange-950 dark:text-orange-100 flex items-start gap-2.5 shadow-sm">
            <AlertTriangle className="w-4 h-4 shrink-0 text-orange-600 dark:text-orange-400 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-extrabold text-orange-900 dark:text-orange-200">{t('monitor.quota_warning')}</span>
              <p className="text-[11px] text-orange-950/80 dark:text-orange-100/90 font-medium">
                تم حفظ وتوثيق نتائج التدقيق الحتمي والملاحظات الكاملة بنجاح، ويمكن مراجعتها في التقرير وقوائم الملاحظات.
              </p>
            </div>
          </div>
        )}

        {/* Navigation Tabs Bar */}
        <div className="flex items-center gap-1.5 overflow-x-auto border-t border-[var(--hairline)] pt-3 text-xs font-semibold no-scrollbar">
          <TabButton
            active={activeTab === 'monitor'}
            onClick={() => setActiveTab('monitor')}
            label={t('monitor.title')}
            count={isRunning ? '●' : undefined}
          />
          <TabButton
            active={activeTab === 'overview'}
            onClick={() => setActiveTab('overview')}
            label="نظرة عامة والتقييم"
            score={run.overall_score}
          />
          <TabButton
            active={activeTab === 'screenshots'}
            onClick={() => setActiveTab('screenshots')}
            label={t('screens.title')}
          />
          <TabButton
            active={activeTab === 'findings'}
            onClick={() => setActiveTab('findings')}
            label={t('findings.title')}
            count={run.total_findings}
          />
          <TabButton
            active={activeTab === 'recommendations'}
            onClick={() => setActiveTab('recommendations')}
            label={t('recs.title')}
            count={run.total_recommendations}
          />
          <TabButton
            active={activeTab === 'ai_automation'}
            onClick={() => setActiveTab('ai_automation')}
            label={t('monitor.view_ai_automation')}
            icon={<Sparkles className="w-3.5 h-3.5 text-amber-500" />}
          />
          {run.stages?.competitor_intelligence && (
            <TabButton
              active={activeTab === 'competitors'}
              onClick={() => setActiveTab('competitors')}
              label={t('monitor.view_competitors')}
              score={run.scores?.competitor_intelligence}
            />
          )}
          {run.stages?.security_privacy && (
            <TabButton
              active={activeTab === 'security'}
              onClick={() => setActiveTab('security')}
              label={t('monitor.view_security')}
              score={run.scores?.security_privacy}
            />
          )}
          {run.stages?.accessibility && (
            <TabButton
              active={activeTab === 'accessibility'}
              onClick={() => setActiveTab('accessibility')}
              label={t('monitor.view_accessibility')}
              score={run.scores?.accessibility}
            />
          )}
          {run.stages?.strategic_intelligence && (
            <TabButton
              active={activeTab === 'strategic'}
              onClick={() => setActiveTab('strategic')}
              label={t('monitor.view_strategic')}
              score={run.scores?.strategic_intelligence}
            />
          )}
          <TabButton
            active={activeTab === 'reports'}
            onClick={() => setActiveTab('reports')}
            label={t('reports.title')}
          />
        </div>
      </div>

      {/* Tab Content Display */}
      {activeTab === 'monitor' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Stages Execution Timeline */}
          <div className="lg:col-span-2 space-y-4">
            <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-3">
                <h2 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                  <Layers className="w-4 h-4 text-amber-500" />
                  <span>{t('monitor.stage_timeline')}</span>
                </h2>
                <div className="text-xs text-[var(--text-3)] font-mono">
                  {Object.values(run.stages).filter((s) => s.status === 'completed').length} /{' '}
                  {Object.keys(run.stages).length} مكتمل
                </div>
              </div>

              <div className="space-y-3">
                {Object.entries(run.stages).map(([stageId, s]) => (
                  <div
                    key={stageId}
                    className={`p-4 rounded-2xl border transition-all ${
                      s.status === 'running'
                        ? 'border-blue-500/40 bg-blue-500/5 ring-1 ring-blue-500/20'
                        : s.status === 'completed'
                        ? 'border-emerald-500/20 bg-emerald-500/5'
                        : s.status === 'ai_blocked'
                        ? 'border-amber-500/30 bg-amber-500/5'
                        : s.status === 'failed'
                        ? 'border-red-500/30 bg-red-500/5'
                        : 'border-[var(--hairline)] bg-[var(--glass-inset)] opacity-70'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <StageIcon status={s.status} />
                        <div>
                          <div className="font-bold text-sm text-[var(--text)]">
                            {lang === 'ar' ? s.name_ar : s.name}
                          </div>
                          <div className="text-[11px] text-[var(--text-3)] font-mono">ID: {s.stage_id}</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {s.score !== null && s.score !== undefined && (
                          <span className="font-mono font-bold text-xs px-2.5 py-0.5 rounded-full bg-[var(--hairline)] text-[var(--text)] border border-[var(--hairline)]">
                            {s.score} / 100
                          </span>
                        )}
                        <StageStatusBadge status={s.status} />
                      </div>
                    </div>

                    {(s.findings_count > 0 || s.duration_ms > 0 || s.error_message) && (
                      <div className="mt-2.5 pt-2.5 border-t border-[var(--hairline)] flex flex-wrap items-center justify-between gap-2 text-xs text-[var(--text-3)]">
                        <div className="flex items-center gap-3 font-mono text-[11px]">
                          {s.duration_ms > 0 && <span>⏱ {s.duration_ms.toFixed(0)} ms</span>}
                          {s.findings_count > 0 && <span>⚠️ {s.findings_count} ملاحظات</span>}
                          {s.recommendations_count > 0 && <span>💡 {s.recommendations_count} توصيات</span>}
                        </div>
                        {s.error_message && (
                          <div className="text-[11px] text-red-700 dark:text-red-300 font-mono font-medium truncate max-w-sm">
                            {s.error_message}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Live Events Stream */}
          <div className="space-y-4">
            <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-3">
                <h2 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-500" />
                  <span>{t('monitor.live_events')}</span>
                </h2>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              </div>

              <div className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
                {events.length > 0 ? (
                  events.map((evt) => (
                    <div
                      key={evt.event_id}
                      className="p-3 rounded-xl border border-[var(--hairline)] bg-[var(--bg)] text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-3)]">
                        <span className="text-[var(--accent)] font-semibold">{evt.event_type}</span>
                        <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="text-[var(--text)] font-medium leading-relaxed">
                        {lang === 'ar' ? evt.message_ar : evt.message}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-12 text-center text-xs text-[var(--text-3)]">
                    {t('monitor.no_events')}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'overview' && <AnalysisOverview run={run} />}
      {activeTab === 'screenshots' && <ScreenshotExplorer runId={run.run_id} />}
      {activeTab === 'findings' && <FindingsExplorer runId={run.run_id} />}
      {activeTab === 'recommendations' && <RecommendationsViewer runId={run.run_id} />}
      {activeTab === 'ai_automation' && <AIAutomationView runId={run.run_id} />}
      {activeTab === 'competitors' && <CompetitorIntelligenceView runId={run.run_id} />}
      {activeTab === 'security' && <SecurityPrivacyView runId={run.run_id} />}
      {activeTab === 'accessibility' && <AccessibilityView runId={run.run_id} />}
      {activeTab === 'strategic' && <StrategicIntelligenceView runId={run.run_id} />}
      {activeTab === 'reports' && <ReportViewer runId={run.run_id} stages={Object.keys(run.stages)} />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  label,
  count,
  score,
  icon,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  count?: any;
  score?: number | null;
  icon?: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer flex items-center gap-2 ${
        active
          ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
          : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
      }`}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{label}</span>
      {count !== undefined && count !== null && (
        <span
          className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${
            active ? 'bg-black/20 text-white' : 'bg-[var(--hairline)] text-[var(--text-2)]'
          }`}
        >
          {count}
        </span>
      )}
      {score !== undefined && score !== null && (
        <span
          className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${
            active ? 'bg-black/20 text-white' : 'bg-stone-900/10 text-stone-900 dark:bg-stone-100/10 dark:text-stone-100 font-bold'
          }`}
        >
          {score}
        </span>
      )}
    </button>
  );
}

function RunStatusPill({ status }: { status: string }) {
  const s = status.toLowerCase();
  if (s === 'completed') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30">
        <CheckCircle2 className="w-3.5 h-3.5" /> مكتمل بنجاح
      </span>
    );
  }
  if (s === 'running' || s === 'queued' || s === 'created') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-500/15 text-blue-800 dark:text-blue-300 border border-blue-500/30">
        <Clock className="w-3.5 h-3.5 animate-spin" /> جاري التنفيذ
      </span>
    );
  }
  if (s === 'ai_blocked' || s === 'partial') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-orange-600 text-white shadow-xs border border-orange-700">
        <AlertTriangle className="w-3.5 h-3.5 text-white" /> جزئي (حظر حصة AI)
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-600 text-white shadow-xs border border-red-700">
      <ShieldAlert className="w-3.5 h-3.5 text-white" /> متعثر
    </span>
  );
}

function StageIcon({ status }: { status: string }) {
  if (status === 'running') {
    return <Clock className="w-4 h-4 text-blue-500 animate-spin shrink-0" />;
  }
  if (status === 'completed') {
    return <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />;
  }
  if (status === 'ai_blocked') {
    return <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400 shrink-0" />;
  }
  if (status === 'failed') {
    return <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />;
  }
  return <Clock className="w-4 h-4 text-[var(--text-3)] shrink-0" />;
}

function StageStatusBadge({ status }: { status: string }) {
  if (status === 'completed') {
    return <span className="text-[11px] font-bold text-emerald-700 dark:text-emerald-400">مكتمل</span>;
  }
  if (status === 'running') {
    return <span className="text-[11px] font-bold text-blue-700 dark:text-blue-400">قيد العمل</span>;
  }
  if (status === 'ai_blocked') {
    return <span className="text-[11px] font-extrabold text-orange-600 dark:text-orange-400">حظر حصة</span>;
  }
  if (status === 'failed') {
    return <span className="text-[11px] font-bold text-red-700 dark:text-red-400">فشل</span>;
  }
  return <span className="text-[11px] font-semibold text-[var(--text-3)]">في الانتظار</span>;
}
