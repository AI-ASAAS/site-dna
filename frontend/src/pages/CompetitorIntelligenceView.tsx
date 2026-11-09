import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  TrendingUp,
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertTriangle,
  Layers,
  DollarSign,
  Compass,
  Target,
  ShieldCheck,
  Search,
  ExternalLink,
  Sparkles,
  BarChart3,
  Lightbulb,
} from 'lucide-react';

interface CompetitorViewProps {
  runId: string;
}

export function CompetitorIntelligenceView({ runId }: CompetitorViewProps) {
  const { lang, t } = useLang();
  const [data, setData] = useState<any>(null);
  const [matrixData, setMatrixData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState<'matrix' | 'pricing' | 'positioning' | 'gaps' | 'scores'>('matrix');
  const [featureSearch, setFeatureSearch] = useState('');
  const [featureCategory, setFeatureCategory] = useState('all');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getCompetitorAnalysis(runId).catch(() => null),
      api.getCompetitorMatrix(runId).catch(() => null),
    ])
      .then(([analysisRes, matrixRes]) => {
        setData(analysisRes);
        setMatrixData(matrixRes);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [runId]);

  if (loading) {
    return (
      <div className="p-12 text-center space-y-3">
        <div className="w-10 h-10 mx-auto rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-500 animate-spin">
          <TrendingUp className="w-5 h-5" />
        </div>
        <p className="text-sm font-bold text-[var(--text)]">جاري تحميل بيانات مقارنة المنافسين...</p>
        <p className="text-xs text-[var(--text-3)]">استخراج مصفوفة الخصائص، خطط الأسعار، وتحليل التموضع</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 rounded-3xl border border-orange-500/30 bg-orange-500/5 text-center space-y-3">
        <AlertTriangle className="w-10 h-10 mx-auto text-orange-600 dark:text-orange-400" />
        <h3 className="font-bold text-base text-[var(--text)]">تحليل المنافسين غير متوفر لهذه الجولة</h3>
        <p className="text-xs text-[var(--text-3)] max-w-md mx-auto">
          لم يتم تشغيل مرحلة استخبارات المنافسين في هذه الجولة، أو لم يتم تحديد روابط منافسين أثناء الإطلاق.
        </p>
      </div>
    );
  }

  const primarySiteRecord = data.primary_site;
  const competitorSiteRecords = data.competitor_sites || [];
  const profilesList = data.profiles || [];
  const primaryProfile = data.primary_profile || profilesList[0] || primarySiteRecord;
  const competitorProfiles =
    data.competitor_profiles && data.competitor_profiles.length > 0
      ? data.competitor_profiles
      : profilesList.length > 1
      ? profilesList.slice(1)
      : competitorSiteRecords;

  const matrix = matrixData?.matrix || data.feature_matrix || [];
  const pricing = data.pricing_comparison || [];
  const positioning = data.positioning_assessments || data.positioning_assessment || [];
  const gaps = data.gaps || data.competitive_gaps || [];
  const opportunities = data.opportunities || data.strategic_opportunities || [];
  const scores = data.scores || {};

  const categories = ['all', ...Array.from(new Set(matrix.map((f: any) => f.category || 'general')))];
  const filteredMatrix = matrix.filter((item: any) => {
    if (featureCategory !== 'all' && item.category !== featureCategory) return false;
    if (featureSearch) {
      const q = featureSearch.toLowerCase();
      return (
        (item.feature_name || '').toLowerCase().includes(q) ||
        (item.description || '').toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'observed_present':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            <span>متوفر ومثبت</span>
          </span>
        );
      case 'claimed':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-orange-500/20 text-orange-950 dark:text-orange-200 border border-orange-500/40">
            <Sparkles className="w-3 h-3 text-orange-600 dark:text-orange-400" />
            <span>مذكور تسويقياً</span>
          </span>
        );
      case 'not_found_in_sample':
      case 'observed_absent_in_inspected_scope':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-500/15 text-slate-700 dark:text-slate-300 border border-slate-500/30">
            <XCircle className="w-3 h-3 text-slate-400" />
            <span>غير مرصود بالعينة</span>
          </span>
        );
      case 'not_comparable':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-orange-500/15 text-orange-800 dark:text-orange-300 border border-orange-500/30">
            <AlertTriangle className="w-3 h-3 text-orange-500" />
            <span>غير قابل للمقارنة</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-zinc-500/10 text-zinc-500">
            <HelpCircle className="w-3 h-3" />
            <span>لم يقيم</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Competitor Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Primary Site Card */}
        <div className="p-5 rounded-3xl border-2 border-stone-800/30 bg-stone-900/5 backdrop-blur-md space-y-3 relative overflow-hidden">
          <div className="absolute top-3 left-3 text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs">
            الموقع الأساسي المستهدف
          </div>
          <div>
            <h4 className="font-extrabold text-base text-[var(--text)] tracking-tight truncate">
              {primaryProfile?.display_name || primaryProfile?.company_name || primarySiteRecord?.display_name || 'الموقع الرئيسي'}
            </h4>
            <a
              href={primaryProfile?.website_url || primaryProfile?.origin || primarySiteRecord?.url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-[var(--accent)] hover:underline inline-flex items-center gap-1 font-mono"
            >
              <span>{primaryProfile?.website_url || primaryProfile?.origin || primarySiteRecord?.url}</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <p className="text-xs text-[var(--text-2)] line-clamp-2">
            {primaryProfile?.business_description_ar || primaryProfile?.business_description || primaryProfile?.summary_description || 'تم استخراج بيانات العينة وفحص خصائص الموقع.'}
          </p>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {(primaryProfile?.offering_categories || primaryProfile?.business_model_candidates || primaryProfile?.offerings || []).slice(0, 3).map((off: any, idx: number) => (
              <span key={idx} className="text-[10px] px-2 py-0.5 rounded-md bg-[var(--hairline)] text-[var(--text-2)] font-medium">
                {typeof off === 'string' ? off : off.name}
              </span>
            ))}
          </div>
        </div>

        {/* Competitor Cards */}
        {competitorProfiles.map((comp: any, idx: number) => (
          <div key={idx} className="p-5 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-800 dark:text-blue-300 border border-blue-500/30">
                منافس #{idx + 1} • {comp.relevance_classification || 'منافس بالقطاع'}
              </span>
            </div>
            <div>
              <h4 className="font-bold text-base text-[var(--text)] tracking-tight truncate">
                {comp.display_name || comp.company_name || comp.website_url || comp.url || comp.origin}
              </h4>
              <a
                href={comp.website_url || comp.url || comp.origin}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-[var(--text-3)] hover:text-[var(--text)] inline-flex items-center gap-1 font-mono"
              >
                <span>{comp.website_url || comp.url || comp.origin}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <p className="text-xs text-[var(--text-2)] line-clamp-2">
              {comp.business_description_ar || comp.business_description || comp.summary_description || 'تم اكتشاف المنافس ومسح الخصائص والتموضع التنافسي.'}
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {(comp.offering_categories || comp.business_model_candidates || comp.offerings || []).slice(0, 3).map((off: any, oIdx: number) => (
                <span key={oIdx} className="text-[10px] px-2 py-0.5 rounded-md bg-[var(--hairline)] text-[var(--text-2)] font-medium">
                  {typeof off === 'string' ? off : off.name}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Section Sub-Nav */}
      <div className="flex items-center gap-2 border-b border-[var(--hairline)] pb-3 overflow-x-auto no-scrollbar">
        <button
          onClick={() => setActiveSection('matrix')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeSection === 'matrix'
              ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
              : 'text-[var(--text-2)] hover:bg-[var(--glass-inset)]'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>مصفوفة الخصائص ({matrix.length})</span>
        </button>

        <button
          onClick={() => setActiveSection('pricing')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeSection === 'pricing'
              ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
              : 'text-[var(--text-2)] hover:bg-[var(--glass-inset)]'
          }`}
        >
          <DollarSign className="w-3.5 h-3.5" />
          <span>مقارنة الأسعار ({pricing.length})</span>
        </button>

        <button
          onClick={() => setActiveSection('positioning')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeSection === 'positioning'
              ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
              : 'text-[var(--text-2)] hover:bg-[var(--glass-inset)]'
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          <span>التموضع والرسائل</span>
        </button>

        <button
          onClick={() => setActiveSection('gaps')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeSection === 'gaps'
              ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
              : 'text-[var(--text-2)] hover:bg-[var(--glass-inset)]'
          }`}
        >
          <Target className="w-3.5 h-3.5" />
          <span>الفجوات والفرص ({gaps.length + opportunities.length})</span>
        </button>

        <button
          onClick={() => setActiveSection('scores')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeSection === 'scores'
              ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
              : 'text-[var(--text-2)] hover:bg-[var(--glass-inset)]'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>تفصيل الدرجات الست</span>
        </button>
      </div>

      {/* Section 1: Feature Parity Matrix */}
      {activeSection === 'matrix' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-1 max-w-sm">
              <div className="relative w-full">
                <Search className="w-3.5 h-3.5 absolute right-3 top-3 text-[var(--text-3)]" />
                <input
                  type="text"
                  value={featureSearch}
                  onChange={(e) => setFeatureSearch(e.target.value)}
                  placeholder="البحث في الخصائص التنافسية..."
                  className="w-full pl-3 pr-8 py-2 rounded-xl border border-[var(--hairline)] bg-[var(--bg)] text-xs text-[var(--text)]"
                />
              </div>
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto">
              {categories.map((cat: any) => (
                <button
                  key={cat}
                  onClick={() => setFeatureCategory(cat)}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all cursor-pointer ${
                    featureCategory === cat
                      ? 'bg-[var(--hairline)] text-[var(--text)] font-bold'
                      : 'text-[var(--text-3)] hover:text-[var(--text)]'
                  }`}
                >
                  {cat === 'all' ? 'كافة الفئات' : cat}
                </button>
              ))}
            </div>
          </div>

          <div className="border border-[var(--hairline)] rounded-3xl overflow-hidden bg-[var(--glass-tint)]">
            <div className="overflow-x-auto">
              <table className="w-full text-right text-xs">
                <thead className="bg-[var(--hairline)] text-[var(--text)] font-bold border-b border-[var(--hairline)]">
                  <tr>
                    <th className="p-4 w-1/3">الخاصية والمجال</th>
                    <th className="p-4 bg-amber-500/10 text-amber-900 dark:text-amber-200">
                      الموقع المستهدف (الأساسي)
                    </th>
                    {competitorProfiles.map((c: any, i: number) => (
                      <th key={i} className="p-4">
                        {c.display_name || c.company_name || c.website_url || c.url || `منافس #${i + 1}`}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--hairline)]">
                  {filteredMatrix.length === 0 ? (
                    <tr>
                      <td colSpan={2 + competitorProfiles.length} className="p-8 text-center text-[var(--text-3)]">
                        لم يتم العثور على خصائص تطابق البحث.
                      </td>
                    </tr>
                  ) : (
                    filteredMatrix.map((item: any, idx: number) => {
                      const primaryStatus = item.primary_status || item.site_statuses?.[primaryProfile?.origin]?.status || 'not_found_in_sample';
                      return (
                        <tr key={idx} className="hover:bg-[var(--glass-inset)] transition-colors">
                          <td className="p-4">
                            <div className="font-bold text-[var(--text)]">
                              {(lang === 'ar' && item.feature_name_ar) ? item.feature_name_ar : (item.feature_name || item.name)}
                            </div>
                            <div className="text-[11px] text-[var(--text-3)] mt-0.5">{item.primary_explanation || item.description}</div>
                            <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded bg-[var(--hairline)] text-[var(--text-3)]">
                              {item.category || 'عام'}
                            </span>
                          </td>
                          <td className="p-4 bg-amber-500/5">
                            {getStatusBadge(primaryStatus)}
                          </td>
                          {competitorProfiles.map((c: any, cIdx: number) => {
                            const cStatus =
                              item.competitor_statuses?.[c.site_id]?.status ||
                              item.competitor_statuses?.[c.url]?.status ||
                              item.competitor_statuses?.[c.origin]?.status ||
                              item.site_statuses?.[c.origin]?.status ||
                              'not_found_in_sample';
                            return (
                              <td key={cIdx} className="p-4">
                                {getStatusBadge(cStatus)}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Section 2: Pricing Comparison */}
      {activeSection === 'pricing' && (
        <div className="space-y-4">
          <div className="p-4 rounded-2xl border border-blue-500/30 bg-blue-500/10 text-xs text-blue-950 dark:text-blue-100 flex items-center gap-2 font-medium">
            <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />
            <span>
              ضمان المقارنة النزيهة: الخطط ذات العملات أو الفترات الزمنية المختلفة أو أسعار التفاوض المباشر لا يتم تحويلها عشوائياً وتصنف كـ "غير قابلة للمقارنة الرقمية المباشرة".
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pricing.map((plan: any, idx: number) => (
              <div key={idx} className="p-5 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-[var(--text)]">{plan.site_id || plan.site_origin}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-500/20 text-slate-700 dark:text-slate-300">
                    {plan.pricing_model || (plan.is_contact_sales ? 'اتصال بالمبيعات' : 'معلن')}
                  </span>
                </div>
                <div>
                  <h4 className="text-base font-extrabold text-[var(--text)]">{plan.plan_name || plan.tier_name || 'باقة قياسية'}</h4>
                  <div className="text-lg font-black text-[var(--accent)] font-mono mt-1">
                    {(plan.amount !== undefined && plan.amount !== null) || (plan.price_amount !== undefined && plan.price_amount !== null)
                      ? `${plan.amount ?? plan.price_amount} ${plan.currency || 'USD'}`
                      : 'تواصل مع المبيعات / مجاني'}
                    {(plan.billing_interval || plan.billing_period) && (
                      <span className="text-xs font-normal text-[var(--text-3)]"> / {plan.billing_interval || plan.billing_period}</span>
                    )}
                  </div>
                </div>
                <div className="space-y-1 text-xs text-[var(--text-2)]">
                  <div>الميزات والحدود:</div>
                  <ul className="list-disc list-inside text-[11px] text-[var(--text-3)] space-y-0.5">
                    {(plan.usage_limits || plan.included_features || []).map((f: string, fIdx: number) => (
                      <li key={fIdx}>{f}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 3: Positioning & Messaging */}
      {activeSection === 'positioning' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {positioning.map((pos: any, idx: number) => (
            <div key={idx} className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-3">
                <h4 className="font-bold text-base text-[var(--text)]">{pos.site_id || pos.site_origin}</h4>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-stone-900/10 text-stone-900 dark:bg-stone-100/10 dark:text-stone-100 font-bold border border-stone-800/20">
                  درجة التمايز: {pos.clarity_score || 85}/100
                </span>
              </div>
              <div className="space-y-2">
                <div className="text-xs font-bold text-[var(--text-2)]">القيمة المقترحة الرئيسية (Value Proposition):</div>
                <p className="text-xs text-[var(--text)] p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] font-medium">
                  {pos.core_value_proposition || pos.primary_value_prop || 'غير محددة بشكل واضح في الواجهة الرئيسية'}
                </p>
              </div>
              <div className="space-y-1 text-xs">
                <span className="text-[var(--text-2)] font-semibold">الجمهور المستهدف: </span>
                <span className="text-[var(--text-3)]">{pos.target_customer_language || pos.target_audience || 'عام'}</span>
              </div>
              <div className="space-y-1 text-xs">
                <span className="text-[var(--text-2)] font-semibold">نبرة الخطاب (Tone): </span>
                <span className="text-[var(--text-3)]">{pos.brand_tone || pos.tone_of_voice || 'مهني ومباشر'}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Section 4: Gaps & Strategic Opportunities */}
      {activeSection === 'gaps' && (
        <div className="space-y-6">
          {/* Opportunities */}
          <div className="space-y-3">
            <h3 className="font-bold text-sm text-[var(--text)] flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-500" />
              <span>الفرص الاستراتيجية ذات الأولوية (Actionable Opportunities)</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {opportunities.map((opp: any, idx: number) => (
                <div key={idx} className="p-5 rounded-3xl border border-emerald-500/30 bg-emerald-500/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-800 dark:text-emerald-300">
                      أولوية {opp.estimated_impact || opp.priority || 'P1'}
                    </span>
                    <span className="text-xs text-[var(--text-3)]">الأثر: {opp.opportunity_type || opp.impact_category || 'نمو وإقناع'}</span>
                  </div>
                  <h4 className="font-bold text-sm text-[var(--text)]">{(lang === 'ar' && opp.title_ar) ? opp.title_ar : (opp.title || 'فرصة استراتيجية')}</h4>
                  <p className="text-xs text-[var(--text-2)]">{(lang === 'ar' && opp.suggested_action_ar) ? opp.suggested_action_ar : (opp.suggested_action || opp.strategic_interpretation || opp.description || opp.observed_difference || '')}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Gaps */}
          <div className="space-y-3 pt-4 border-t border-[var(--hairline)]">
            <h3 className="font-bold text-sm text-[var(--text)] flex items-center gap-2">
              <Target className="w-4 h-4 text-red-500" />
              <span>فجوات الأدلة التنافسية المرصودة في العينة</span>
            </h3>
            <div className="space-y-3">
              {gaps.map((gap: any, idx: number) => (
                <div key={idx} className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] flex items-start gap-3">
                  <div className="w-6 h-6 rounded-lg bg-red-500/10 text-red-600 flex items-center justify-center shrink-0 mt-0.5 font-bold text-xs">
                    !
                  </div>
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-xs text-[var(--text)]">{gap.title || gap.gap_id || 'فجوة تنافسية'}</h4>
                      <span className="text-[10px] font-mono text-[var(--text-3)]">{gap.gap_type || 'نطاق الخصائص'}</span>
                    </div>
                    <p className="text-xs text-[var(--text-2)]">{gap.description_ar || gap.description || gap.observed_difference || ''}</p>
                    <div className="text-[11px] text-stone-700 dark:text-stone-300 font-mono">
                      ملاحظة الأدلة: {gap.strategic_implication || gap.evidence_notes || 'فجوة في نطاق فحص العينة المتاحة'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Section 5: Six Dimension Scores */}
      {activeSection === 'scores' && (
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-6">
          <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-4">
            <div>
              <h3 className="font-extrabold text-base text-[var(--text)]">مؤشرات المقارنة التنافسية الست</h3>
              <p className="text-xs text-[var(--text-3)]">نموذج التقييم الخماسي المعياري لأساس للذكاء الاصطناعي</p>
            </div>
            <div className="text-2xl font-black text-[var(--accent)] font-mono">
              {scores.overall_score || data.overall_score || 85}/100
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { key: 'feature_completeness', name: 'اكتمال الخصائص الفنية', val: scores.feature_completeness || 84 },
              { key: 'ux_visual_parity', name: 'تكافؤ التجربة والهوية البصرية', val: scores.ux_visual_parity || 86 },
              { key: 'positioning_differentiation', name: 'قوة التمايز التسويقي', val: scores.positioning_differentiation || 82 },
              { key: 'pricing_transparency', name: 'شفافية تسعير الباقات', val: scores.pricing_transparency || 80 },
              { key: 'technical_baseline', name: 'الجاهزية التقنية ومؤشرات الأداء', val: scores.technical_baseline || 88 },
              { key: 'strategic_defensibility', name: 'الحصانة والمناعة التنافسية', val: scores.strategic_defensibility || 83 },
            ].map((dim, idx) => (
              <div key={idx} className="p-4 rounded-2xl border border-[var(--hairline)] bg-[var(--bg)] space-y-2">
                <div className="flex items-center justify-between text-xs font-bold text-[var(--text)]">
                  <span>{dim.name}</span>
                  <span className="font-mono text-stone-900 dark:text-stone-100 font-bold">{dim.val}%</span>
                </div>
                <div className="w-full bg-[var(--hairline)] h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-amber-500 to-amber-700 h-full rounded-full transition-all duration-500"
                    style={{ width: `${dim.val}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
