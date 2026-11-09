import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  ShieldCheck,
  ShieldAlert,
  Lock,
  Globe,
  FileText,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Eye,
  Layers,
  Sparkles,
  Info,
  Cookie,
  UserCheck,
  ExternalLink,
} from 'lucide-react';

interface SecurityViewProps {
  runId: string;
}

export function SecurityPrivacyView({ runId }: SecurityViewProps) {
  const { lang, t } = useLang();
  const [report, setReport] = useState<any>(null);
  const [headersData, setHeadersData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'headers' | 'cookies' | 'isolation' | 'third_party' | 'privacy' | 'recs'
  >('overview');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getSecurityReport(runId).catch(() => null),
      api.getSecurityHeaders(runId).catch(() => null),
    ])
      .then(([rep, hdrs]) => {
        setReport(rep);
        setHeadersData(hdrs);
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
          <ShieldCheck className="w-5 h-5" />
        </div>
        <p className="text-sm font-bold text-[var(--text)]">
          {lang === 'ar' ? 'جاري تحميل تدقيق الأمان والخصوصية...' : 'Loading Security & Privacy Audit...'}
        </p>
        <p className="text-xs text-[var(--text-3)]">
          {lang === 'ar'
            ? 'فحص ترويسات الأمان، شهادات التشفير، ملفات تعريف الارتباط، وسياسات الخصوصية'
            : 'Evaluating headers, certificates, cookies, and privacy signals'}
        </p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-12 text-center rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
        <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-base text-[var(--text)]">
            {lang === 'ar' ? 'لا يتوفر تقرير أمان لهذه الجولة بعد' : 'No Security Audit Available'}
          </h3>
          <p className="text-xs text-[var(--text-3)] max-w-md mx-auto">
            {lang === 'ar'
              ? 'تأكد من اختيار مرحلة "أمان الموقع والخصوصية" عند إطلاق الفحص، أو انتظر اكتمال تحليلها.'
              : 'Ensure the Security & Privacy stage was selected when launching the analysis run.'}
          </p>
        </div>
      </div>
    );
  }

  const scores = report.scores || {};
  const overallScore = scores.overall_score ?? 0;
  const isGood = overallScore >= 75;
  const isMedium = overallScore >= 50 && overallScore < 75;

  const tabs = [
    { id: 'overview', labelAr: 'نظرة عامة والدرجات', labelEn: 'Overview & Scores' },
    { id: 'headers', labelAr: 'ترويسات الحماية (8)', labelEn: 'Security Headers' },
    { id: 'cookies', labelAr: 'أمان ملفات الارتباط', labelEn: 'Cookie Security' },
    { id: 'isolation', labelAr: 'عزل المتصفح (Sandbox)', labelEn: 'Browser Isolation' },
    { id: 'third_party', labelAr: 'الأطراف الخارجية والتتبع', labelEn: 'Third-Party Inventory' },
    { id: 'privacy', labelAr: 'سياسات الخصوصية والإفصاح', labelEn: 'Privacy Disclosures' },
    { id: 'recs', labelAr: 'خارطة التوصيات (P1–P3)', labelEn: 'Remediation Roadmap' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Defensive Non-Intrusive Regulatory Banner */}
      <div className="p-4 rounded-2xl border border-blue-500/30 bg-blue-500/10 text-blue-900 dark:text-blue-200 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
        <div className="text-xs leading-relaxed">
          <span className="font-bold">
            {lang === 'ar' ? 'تدقيق دفاعي غير تدخلي ممتثل للأنظمة:' : 'Defensive Non-Intrusive Audit Notice:'}
          </span>{' '}
          {lang === 'ar'
            ? 'هذا التقييم مستند حصرياً إلى الأدلة التقنية السلبية المتاحة للعموم (ترويسات HTTP، شهادات التشفير، ملفات الارتباط المعلنة، وإفصاحات الخصوصية). لا يتضمن أي اختبارات اختراق هجومية أو محاولات حقن.'
            : 'This audit is strictly passive and based on observable public website telemetry. Zero active vulnerability probing or injection is conducted.'}
        </div>
      </div>

      {/* Header & Overall Posture Card */}
      <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm border border-stone-800 dark:border-stone-200">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 dark:text-amber-600" />
              <span>Phase 09 — {lang === 'ar' ? 'استخبارات الأمان والخصوصية' : 'Security & Privacy Intelligence'}</span>
            </div>
            <h2 className="text-2xl font-extrabold text-[var(--text)]">
              {lang === 'ar' ? 'مؤشر الوضع الأمني والدفاعي للموقع' : 'Defensive Website Security Posture'}
            </h2>
            <p className="text-xs text-[var(--text-2)] max-w-2xl leading-relaxed">
              {report.target_url} • {lang === 'ar' ? 'النموذج المعتمد:' : 'Model:'}{' '}
              <span className="font-mono text-stone-900 dark:text-stone-100 font-bold">
                {report.model_name || 'gemini-3.6-flash'}
              </span>
            </p>
          </div>

          <div className="flex items-center gap-4 bg-[var(--glass-inset)] p-4 rounded-2xl border border-[var(--hairline)] self-start md:self-auto">
            <div className="text-end">
              <div className="text-xs text-[var(--text-3)] font-medium">
                {lang === 'ar' ? 'التقييم المركب' : 'Posture Score'}
              </div>
              <div
                className={`text-3xl font-black font-mono ${
                  isGood
                    ? 'text-emerald-700 dark:text-emerald-400'
                    : isMedium
                    ? 'text-amber-700 dark:text-amber-400'
                    : 'text-red-700 dark:text-red-400'
                }`}
              >
                {overallScore}
                <span className="text-xs font-normal text-[var(--text-3)]"> / 100</span>
              </div>
            </div>
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                isGood
                  ? 'bg-emerald-500/20 text-emerald-500'
                  : isMedium
                  ? 'bg-amber-500/20 text-amber-500'
                  : 'bg-red-500/20 text-red-500'
              }`}
            >
              <ShieldCheck className="w-7 h-7" />
            </div>
          </div>
        </div>

        {/* 6 Dimension Score Tiles */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-6 pt-6 border-t border-[var(--hairline)]">
          <ScoreTile
            title={lang === 'ar' ? 'التشفير والنقل (20%)' : 'Transport (20%)'}
            score={scores.https_transport_score}
            icon={Lock}
          />
          <ScoreTile
            title={lang === 'ar' ? 'ترويسات الحماية (25%)' : 'Headers (25%)'}
            score={scores.security_headers_score}
            icon={ShieldCheck}
          />
          <ScoreTile
            title={lang === 'ar' ? 'ملفات الارتباط (15%)' : 'Cookies (15%)'}
            score={scores.cookie_security_score}
            icon={Cookie}
          />
          <ScoreTile
            title={lang === 'ar' ? 'المتصفح والعزل (15%)' : 'Isolation (15%)'}
            score={scores.client_side_resources_score}
            icon={Layers}
          />
          <ScoreTile
            title={lang === 'ar' ? 'الخصوصية (15%)' : 'Privacy (15%)'}
            score={scores.privacy_consent_score}
            icon={UserCheck}
          />
          <ScoreTile
            title={lang === 'ar' ? 'الثقة والشفافية (10%)' : 'Trust (10%)'}
            score={scores.digital_trust_score}
            icon={Globe}
          />
        </div>
      </div>

      {/* Sub-tab Navigation */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar border-b border-[var(--hairline)]">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === tab.id
                ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
            }`}
          >
            {lang === 'ar' ? tab.labelAr : tab.labelEn}
          </button>
        ))}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* HTTPS Transport Card */}
          <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-[var(--text)] flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-500" />
                <span>{lang === 'ar' ? 'تشفير الاتصال والشهادات الرقمية' : 'HTTPS & TLS Transport'}</span>
              </h3>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  report.https_assessment?.is_https
                    ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30'
                    : 'bg-red-500/15 text-red-800 dark:text-red-300 border border-red-500/30'
                }`}
              >
                {report.https_assessment?.is_https ? 'HTTPS Enforced' : 'Insecure HTTP'}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-[var(--glass-inset)] space-y-1">
                <div className="text-[var(--text-3)] font-medium">HSTS (أمان النقل الصارم)</div>
                <div className="font-bold text-[var(--text)]">
                  {report.https_assessment?.hsts_present
                    ? `مفعل (max-age: ${report.https_assessment?.hsts_max_age || '31536000'})`
                    : 'غير مفعل'}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[var(--glass-inset)] space-y-1">
                <div className="text-[var(--text-3)] font-medium">HSTS Preload & SubDomains</div>
                <div className="font-bold text-[var(--text)]">
                  {report.https_assessment?.hsts_preload
                    ? 'قائمة التضمين المسبق (Preloaded)'
                    : report.https_assessment?.hsts_include_subdomains
                    ? 'يشمل النطاقات الفرعية'
                    : 'غير مشمول'}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[var(--glass-inset)] space-y-1">
                <div className="text-[var(--text-3)] font-medium">حالة الشهادة الرقمية TLS</div>
                <div className="font-bold text-[var(--text)]">
                  {report.tls_observations?.trusted_chain ? 'سلسلة موثوقة' : 'معاينة بدون أخطاء'}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Findings & Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-3">
              <h3 className="font-bold text-sm text-[var(--text)] flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                <span>{lang === 'ar' ? 'ملخص الملاحظات الدفاعية المرصودة' : 'Observed Security Findings'}</span>
              </h3>
              <div className="space-y-2">
                {(report.findings || []).slice(0, 4).map((f: any) => (
                  <div key={f.finding_id} className="p-3 rounded-xl bg-[var(--glass-inset)] flex items-start gap-2.5">
                    <span
                      className={`w-2 h-2 rounded-full shrink-0 mt-1.5 ${
                        f.severity === 'critical' || f.severity === 'high'
                          ? 'bg-red-500'
                          : f.severity === 'medium'
                          ? 'bg-orange-500'
                          : 'bg-blue-500'
                      }`}
                    />
                    <div className="text-xs space-y-0.5">
                      <div className="font-bold text-[var(--text)]">{lang === 'ar' ? f.title_ar : f.title}</div>
                      <div className="text-[var(--text-2)]">{lang === 'ar' ? f.description_ar : f.description}</div>
                    </div>
                  </div>
                ))}
                {(report.findings || []).length === 0 && (
                  <div className="p-4 text-center text-xs text-emerald-700 dark:text-emerald-400">
                    لم يتم رصد أي ثغرات أو إعدادات ناقصة حرجة.
                  </div>
                )}
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-3">
              <h3 className="font-bold text-sm text-[var(--text)] flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>{lang === 'ar' ? 'التوصيات التقنية المقترحة' : 'Top Remediation Recommendations'}</span>
              </h3>
              <div className="space-y-2">
                {(report.recommendations || []).slice(0, 4).map((r: any) => (
                  <div key={r.recommendation_id} className="p-3 rounded-xl bg-[var(--glass-inset)] space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[var(--text)]">{lang === 'ar' ? r.title_ar : r.title}</span>
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-orange-500/20 text-orange-950 dark:text-orange-200 border border-orange-500/30 font-bold uppercase">
                        {r.priority}
                      </span>
                    </div>
                    <div className="text-[11px] text-[var(--text-2)]">
                      {lang === 'ar' ? r.recommended_configuration_change_ar : r.recommended_configuration_change}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Security Headers */}
      {activeTab === 'headers' && (
        <div className="space-y-4">
          <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)]">
            <h3 className="font-bold text-sm text-[var(--text)] mb-3">
              {lang === 'ar' ? 'مصفوفة ترويسات الأمان الأساسية (8 ترويسات)' : 'HTTP Security Headers Matrix'}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-start">
                <thead>
                  <tr className="border-b border-[var(--hairline)] text-[var(--text-3)] font-semibold">
                    <th className="py-2.5 px-3 text-start">الترويسة (Header)</th>
                    <th className="py-2.5 px-3 text-start">الحالة</th>
                    <th className="py-2.5 px-3 text-start">القيمة المرصودة</th>
                    <th className="py-2.5 px-3 text-start">الإجراء العلاجي المقترح</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--hairline)]">
                  {(report.security_headers_assessment?.header_records || []).map((h: any) => (
                    <tr key={h.header_name} className="hover:bg-[var(--glass-inset)]">
                      <td className="py-3 px-3 font-mono font-bold text-[var(--text)]">{h.header_name}</td>
                      <td className="py-3 px-3">
                        {h.is_present ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400 font-bold">
                            <CheckCircle2 className="w-3.5 h-3.5" /> مفعلة
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-700 dark:text-red-400 font-bold">
                            <XCircle className="w-3.5 h-3.5" /> مفقودة
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 font-mono text-[11px] text-[var(--text-2)] max-w-xs truncate">
                        {h.observed_value || '—'}
                      </td>
                      <td className="py-3 px-3 text-[11px] text-[var(--text-2)] max-w-sm">
                        {lang === 'ar' ? h.remediation_recommendation_ar : h.remediation_recommendation}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Cookies */}
      {activeTab === 'cookies' && (
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-[var(--text)]">
              {lang === 'ar' ? 'تدقيق ملفات تعريف الارتباط (Cookies)' : 'Cookie Security Audit'}
            </h3>
            <span className="text-xs text-[var(--text-3)] font-mono">
              إجمالي الملفات المرصودة: {report.cookie_security_assessment?.total_cookies_observed ?? 0}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-start">
              <thead>
                <tr className="border-b border-[var(--hairline)] text-[var(--text-3)] font-semibold">
                  <th className="py-2.5 px-3 text-start">اسم الكعكة (Cookie Name)</th>
                  <th className="py-2.5 px-3 text-center">Secure</th>
                  <th className="py-2.5 px-3 text-center">HttpOnly</th>
                  <th className="py-2.5 px-3 text-center">SameSite</th>
                  <th className="py-2.5 px-3 text-start">الغرض المرصود</th>
                  <th className="py-2.5 px-3 text-start">القيمة</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--hairline)]">
                {(report.cookie_security_assessment?.cookie_records || []).map((c: any) => (
                  <tr key={c.name} className="hover:bg-[var(--glass-inset)]">
                    <td className="py-3 px-3 font-mono font-bold text-[var(--text)]">{c.name}</td>
                    <td className="py-3 px-3 text-center">
                      {c.is_secure ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500 mx-auto" />
                      )}
                    </td>
                    <td className="py-3 px-3 text-center">
                      {c.is_http_only ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500 mx-auto" />
                      )}
                    </td>
                    <td className="py-3 px-3 text-center font-mono">{c.same_site || 'NotSet'}</td>
                    <td className="py-3 px-3 text-[11px] text-[var(--text-2)]">{c.apparent_purpose}</td>
                    <td className="py-3 px-3 font-mono text-[10px] text-[var(--text-3)]">[REDACTED_SECRET]</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Isolation */}
      {activeTab === 'isolation' && (
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
          <h3 className="font-bold text-sm text-[var(--text)]">
            {lang === 'ar' ? 'عزل بيئة المتصفح والحماية من اختطاف النقر' : 'Browser Isolation Controls'}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-[var(--glass-inset)] space-y-2">
              <div className="font-bold text-[var(--text)]">حماية اختطاف النقر (Clickjacking)</div>
              <div className="text-[var(--text-2)]">
                الحالة: <span className="font-bold text-emerald-700 dark:text-emerald-400">{report.browser_isolation_assessment?.framing_protection_status_ar}</span>
              </div>
              <p className="text-[11px] text-[var(--text-3)]">
                يتم تقييم كل من CSP frame-ancestors وترويسة X-Frame-Options لمنع تضمين صفحات الموقع داخل إطارات خبيثة.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[var(--glass-inset)] space-y-2">
              <div className="font-bold text-[var(--text)]">سياسة الإحالة (Referrer-Policy)</div>
              <div className="text-[var(--text-2)]">
                القيمة: <span className="font-mono">{report.browser_isolation_assessment?.referrer_policy_value || 'غير محددة'}</span>
              </div>
              <p className="text-[11px] text-[var(--text-3)]">
                تمنع تسريب روابط الصفحات الداخلية ومعرفات الجلسات في ترويسات Referer عند الانتقال لمواقع أخرى.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Third Party */}
      {activeTab === 'third_party' && (
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
          <h3 className="font-bold text-sm text-[var(--text)]">
            {lang === 'ar' ? 'حصر النطاقات الخارجية والأطراف الثالثة' : 'Third-Party Origins & Trackers'}
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-start">
              <thead>
                <tr className="border-b border-[var(--hairline)] text-[var(--text-3)] font-semibold">
                  <th className="py-2.5 px-3 text-start">النطاق الخارجي (Origin)</th>
                  <th className="py-2.5 px-3 text-start">التصنيف</th>
                  <th className="py-2.5 px-3 text-center">مراجعة الخصوصية</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--hairline)]">
                {(report.third_party_resource_assessment?.third_party_origins_list || []).map((tp: any) => (
                  <tr key={tp.origin} className="hover:bg-[var(--glass-inset)]">
                    <td className="py-3 px-3 font-mono font-bold text-[var(--text)]">{tp.origin}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-[var(--hairline)] text-[11px] font-medium">
                        {tp.resource_category}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center">
                      {tp.requires_privacy_review ? (
                        <span className="text-amber-700 dark:text-amber-400 font-bold">تتطلب إفصاح</span>
                      ) : (
                        <span className="text-[var(--text-3)]">أصلية / مكتبات</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 6: Privacy */}
      {activeTab === 'privacy' && (
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
          <h3 className="font-bold text-sm text-[var(--text)]">
            {lang === 'ar' ? 'مؤشرات الشفافية وسياسات الخصوصية' : 'Privacy Disclosures & Legal Rights'}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <DisclosureCard
              title="سياسة الخصوصية (Privacy Policy)"
              status={report.privacy_signal_assessment?.privacy_policy_found}
              url={report.privacy_signal_assessment?.privacy_policy_url}
            />
            <DisclosureCard
              title="سياسة ملفات تعريف الارتباط (Cookie Policy)"
              status={report.privacy_signal_assessment?.cookie_policy_found}
              url={report.privacy_signal_assessment?.cookie_policy_url}
            />
            <DisclosureCard
              title="قناة التواصل لحماية البيانات (DPO / Privacy Contact)"
              status={report.privacy_signal_assessment?.privacy_contact_found}
            />
            <DisclosureCard
              title="إفصاحات حقوق المستخدمين القانونية (User Rights)"
              status={report.privacy_signal_assessment?.user_rights_mentioned}
            />
          </div>
        </div>
      )}

      {/* Tab 7: Remediation */}
      {activeTab === 'recs' && (
        <div className="p-5 rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] space-y-4">
          <h3 className="font-bold text-sm text-[var(--text)]">
            {lang === 'ar' ? 'خارطة التوصيات والإصلاحات التقنية ذات الأولوية' : 'Remediation Roadmap'}
          </h3>
          <div className="space-y-3">
            {(report.recommendations || []).map((r: any) => (
              <div key={r.recommendation_id} className="p-4 rounded-xl bg-[var(--glass-inset)] space-y-2 border border-[var(--hairline)]">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-[var(--text)]">{lang === 'ar' ? r.title_ar : r.title}</span>
                  <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-800 dark:text-amber-300 font-bold uppercase">
                    {r.priority}
                  </span>
                </div>
                <div className="text-xs text-[var(--text-2)] leading-relaxed">
                  {lang === 'ar' ? r.observed_issue_ar : r.observed_issue}
                </div>
                <div className="p-2.5 rounded-lg bg-[var(--bg)] font-mono text-[11px] text-emerald-800 dark:text-emerald-300">
                  {lang === 'ar' ? r.recommended_configuration_change_ar : r.recommended_configuration_change}
                </div>
                <div className="text-[11px] text-[var(--text-3)]">
                  <span className="font-bold text-[var(--text-2)]">طريقة التحقق: </span>
                  {lang === 'ar' ? r.verification_method_ar : r.verification_method}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ScoreTile({ title, score, icon: IconComp }: { title: string; score?: number; icon: any }) {
  const val = score ?? 0;
  return (
    <div className="p-3.5 rounded-2xl bg-[var(--glass-inset)] border border-[var(--hairline)] space-y-1">
      <div className="flex items-center justify-between text-[var(--text-3)]">
        <span className="text-[11px] font-medium">{title}</span>
        <IconComp className="w-3.5 h-3.5 text-amber-500" />
      </div>
      <div className="text-xl font-bold font-mono text-[var(--text)]">{val}</div>
    </div>
  );
}

function DisclosureCard({ title, status, url }: { title: string; status?: boolean; url?: string }) {
  return (
    <div className="p-3.5 rounded-xl bg-[var(--glass-inset)] flex items-center justify-between">
      <div className="space-y-0.5">
        <div className="font-bold text-[var(--text)]">{title}</div>
        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-[var(--accent)] hover:underline inline-flex items-center gap-1"
          >
            <span>{url}</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
      {status ? (
        <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
      ) : (
        <XCircle className="w-5 h-5 text-red-500 shrink-0" />
      )}
    </div>
  );
}
