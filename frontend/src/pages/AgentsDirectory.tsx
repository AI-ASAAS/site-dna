import React, { useEffect, useState } from 'react';
import { api, type AgentRegistryItem } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  Users,
  Cpu,
  Globe,
  Camera,
  Palette,
  Layout,
  PenTool,
  Zap,
  TrendingUp,
  MousePointer,
  ShieldCheck,
  Award,
  Eye,
  Compass,
  CheckCircle2,
  Lock,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  cpu: Cpu,
  globe: Globe,
  camera: Camera,
  palette: Palette,
  layout: Layout,
  'pen-tool': PenTool,
  zap: Zap,
  'trending-up': TrendingUp,
  users: Users,
  'mouse-pointer': MousePointer,
  'shield-check': ShieldCheck,
  eye: Eye,
  accessibility: Eye,
  compass: Compass,
  award: Award,
};

export function AgentsDirectory() {
  const { t, lang } = useLang();
  const [agents, setAgents] = useState<AgentRegistryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'ready' | 'planned'>('all');
  const [selectedAgent, setSelectedAgent] = useState<AgentRegistryItem | null>(null);

  useEffect(() => {
    api
      .getAgents()
      .then((data) => {
        setAgents(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const filtered = agents.filter((a) => {
    if (filter === 'ready') return a.implementation_status === 'implemented';
    if (filter === 'planned') return a.implementation_status === 'planned';
    return true;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm border border-stone-800 dark:border-stone-200">
            <Users className="w-3.5 h-3.5 text-stone-300 dark:text-stone-700" />
            <span>منظومة الوكلاء المتخصصة (Phases 01–12)</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[var(--text)] tracking-tight">
            {t('agents.title')}
          </h1>
          <p className="text-sm text-[var(--text-2)]">{t('agents.subtitle')}</p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-[var(--hairline)] self-start sm:self-auto">
          <button
            onClick={() => setFilter('all')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === 'all'
                ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            {t('agents.filter_all')} ({agents.length})
          </button>
          <button
            onClick={() => setFilter('ready')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === 'ready'
                ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            {t('agents.filter_ready')} ({agents.filter((a) => a.implementation_status === 'implemented').length})
          </button>
          <button
            onClick={() => setFilter('planned')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === 'planned'
                ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300 shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            {t('agents.filter_planned')} ({agents.filter((a) => a.implementation_status === 'planned').length})
          </button>
        </div>
      </div>

      {/* Agents Grid */}
      {loading ? (
        <div className="py-24 text-center text-xs text-[var(--text-3)]">{t('common.loading')}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((agent) => {
            const IconComp = ICON_MAP[agent.icon] || Cpu;
            const isReady = agent.implementation_status === 'implemented';

            return (
              <div
                key={agent.id}
                onClick={() => setSelectedAgent(agent)}
                className={`p-6 rounded-3xl border transition-all cursor-pointer flex flex-col justify-between space-y-4 hover:shadow-lg ${
                  isReady
                    ? 'border-[var(--hairline)] bg-[var(--glass-tint)] hover:border-amber-500/40'
                    : 'border-dashed border-slate-500/30 bg-slate-500/5 opacity-80'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`w-9 h-9 rounded-2xl flex items-center justify-center ${
                          isReady
                            ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30'
                            : 'bg-slate-500/15 text-slate-500 border border-slate-500/30'
                        }`}
                      >
                        <IconComp className="w-5 h-5" />
                      </div>
                      <span className="font-mono text-xs font-bold text-[var(--accent)]">
                        Phase {String(agent.phase).padStart(2, '0')}
                      </span>
                    </div>

                    {isReady ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30">
                        <CheckCircle2 className="w-3 h-3" /> متاح
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30">
                        <Lock className="w-3 h-3" /> مخطط
                      </span>
                    )}
                  </div>

                  <div>
                    <h3 className="font-bold text-base text-[var(--text)] leading-snug">
                      {lang === 'ar' ? agent.name_ar : agent.name}
                    </h3>
                    <p className="text-xs text-[var(--text-2)] leading-relaxed mt-1.5">
                      {lang === 'ar' ? agent.description_ar : agent.description}
                    </p>
                  </div>
                </div>

                <div className="pt-3 border-t border-[var(--hairline)] flex items-center justify-between text-xs text-[var(--text-3)]">
                  <span className="font-mono text-[11px]">Model: {agent.model_name}</span>
                  <span className="font-semibold text-[var(--accent)] hover:underline text-[11px]">
                    التفاصيل والمخرجات ←
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm p-4 flex items-center justify-center animate-in fade-in duration-150">
          <div className="max-w-lg w-full bg-[var(--bg)] rounded-3xl border border-[var(--hairline)] p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-3">
              <div>
                <span className="text-xs font-mono text-[var(--accent)]">
                  Phase {String(selectedAgent.phase).padStart(2, '0')} • {selectedAgent.category}
                </span>
                <h3 className="font-bold text-lg text-[var(--text)]">
                  {lang === 'ar' ? selectedAgent.name_ar : selectedAgent.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedAgent(null)}
                className="p-1.5 rounded-xl border border-[var(--hairline)] text-[var(--text-3)] hover:text-[var(--text)] cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <span className="text-[var(--text-3)] block mb-1">الوصف الشامل:</span>
                <p className="text-[var(--text)] leading-relaxed">
                  {lang === 'ar' ? selectedAgent.description_ar : selectedAgent.description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div className="p-3 rounded-2xl bg-[var(--glass-tint)] border border-[var(--hairline)]">
                  <span className="text-[var(--text-3)] block mb-1">النموذج المعتمد:</span>
                  <span className="font-mono font-bold text-[var(--text)]">{selectedAgent.model_name}</span>
                </div>
                <div className="p-3 rounded-2xl bg-[var(--glass-tint)] border border-[var(--hairline)]">
                  <span className="text-[var(--text-3)] block mb-1">حالة الجاهزية:</span>
                  <span className="font-bold text-emerald-700 dark:text-emerald-400">
                    {selectedAgent.implementation_status === 'implemented'
                      ? 'مكتمل ومتاح للتشغيل'
                      : 'قريبًا (مخطط مستقبلاً)'}
                  </span>
                </div>
              </div>

              {selectedAgent.dependencies.length > 0 && (
                <div>
                  <span className="text-[var(--text-3)] block mb-1.5">الاعتماديات المسبقة (Dependencies):</span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedAgent.dependencies.map((dep) => (
                      <span key={dep} className="px-2.5 py-1 rounded-xl bg-[var(--hairline)] font-mono text-[11px]">
                        {dep}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedAgent.output_types.length > 0 && (
                <div>
                  <span className="text-[var(--text-3)] block mb-1.5">الملفات والمخرجات المتولدة:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedAgent.output_types.map((ot) => (
                      <span key={ot} className="px-2.5 py-1 rounded-xl bg-amber-500/10 text-amber-800 dark:text-amber-300 font-mono text-[11px] border border-amber-500/20">
                        {ot}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-2 text-end">
              <button
                onClick={() => setSelectedAgent(null)}
                className="px-5 py-2.5 rounded-2xl bg-[var(--accent-fill)] text-[var(--on-accent)] font-semibold text-xs cursor-pointer"
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
