import React, { useEffect, useState } from 'react';
import { useLang } from '../lib/i18n';
import { useTheme } from '../asaas-ui/lib/useTheme';
import { api } from '../lib/api';
import {
  Settings as SettingsIcon,
  Cpu,
  ShieldCheck,
  Languages,
  Moon,
  Sun,
  Server,
  Key,
  Info,
} from 'lucide-react';

export function Settings() {
  const { lang, setLang, t } = useLang();
  const [theme, toggleTheme] = useTheme();
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  useEffect(() => {
    api
      .getHealth()
      .then((data) => setHealthStatus(data.status || 'healthy'))
      .catch(() => setHealthStatus('disconnected'));
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="space-y-1 border-b border-[var(--hairline)] pb-5">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-sm border border-stone-800 dark:border-stone-200">
          <SettingsIcon className="w-3.5 h-3.5 text-stone-300 dark:text-stone-700" />
          <span>تفضيلات المنظومة وإعدادات التشغيل</span>
        </div>
        <h1 className="text-3xl font-extrabold text-[var(--text)] tracking-tight">
          {t('settings.title')}
        </h1>
        <p className="text-sm text-[var(--text-2)]">{t('settings.subtitle')}</p>
      </div>

      <div className="space-y-6">
        {/* Official AI Model Section */}
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-stone-900/10 text-stone-900 dark:bg-stone-100/10 dark:text-stone-100 border border-stone-800/20 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[var(--text)]">{t('settings.model_title')}</h2>
              <span className="font-mono text-xs font-bold text-[var(--accent)]">
                {t('settings.model_name')}
              </span>
            </div>
          </div>

          <p className="text-xs text-[var(--text-2)] leading-relaxed">
            {t('settings.model_desc')} تم تثبيت النموذج على مستوى النظام لمنع الاختلافات العشوائية وضمان موثوقية النتائج.
          </p>

          <div className="p-4 rounded-2xl bg-[var(--bg)] border border-[var(--hairline)] text-xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-[var(--text)]">{t('settings.quota_status')}:</span>
              <span className="font-mono text-[11px] text-amber-700 dark:text-amber-400 font-bold">
                Google Free Tier Daily Cap
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-3)] leading-relaxed">
              {t('settings.quota_desc')}
            </p>
          </div>
        </div>

        {/* Interface Preferences (Language & Theme) */}
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-5">
          <h2 className="text-base font-bold text-[var(--text)]">تخصيص الواجهة والعرض</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Language */}
            <div className="p-4 rounded-2xl bg-[var(--bg)] border border-[var(--hairline)] space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-bold text-[var(--text)]">
                <Languages className="w-4 h-4 text-amber-500" />
                <span>{t('settings.lang_title')}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setLang('ar')}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    lang === 'ar'
                      ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                      : 'border border-[var(--hairline)] text-[var(--text-2)]'
                  }`}
                >
                  العربية (RTL)
                </button>
                <button
                  onClick={() => setLang('en')}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    lang === 'en'
                      ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                      : 'border border-[var(--hairline)] text-[var(--text-2)]'
                  }`}
                >
                  English (LTR)
                </button>
              </div>
            </div>

            {/* Theme */}
            <div className="p-4 rounded-2xl bg-[var(--bg)] border border-[var(--hairline)] space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-bold text-[var(--text)]">
                {theme === 'dark' ? <Moon className="w-4 h-4 text-amber-400" /> : <Sun className="w-4 h-4 text-amber-500" />}
                <span>{t('settings.theme_title')}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => { if (theme !== 'light') toggleTheme(); }}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    theme === 'light'
                      ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                      : 'border border-[var(--hairline)] text-[var(--text-2)]'
                  }`}
                >
                  {t('settings.theme_light')}
                </button>
                <button
                  onClick={() => { if (theme !== 'dark') toggleTheme(); }}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    theme === 'dark'
                      ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                      : 'border border-[var(--hairline)] text-[var(--text-2)]'
                  }`}
                >
                  {t('settings.theme_dark')}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Backend & Environment Diagnostics */}
        <div className="p-6 rounded-3xl border border-[var(--hairline)] bg-[var(--glass-tint)] backdrop-blur-md space-y-4">
          <div className="flex items-center gap-2.5">
            <Server className="w-4 h-4 text-amber-500" />
            <h2 className="text-base font-bold text-[var(--text)]">حالة النظام والواجهة الخلفية (Backend Health)</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] space-y-1">
              <span className="text-[var(--text-3)] block">حالة الخادم:</span>
              <span className="font-mono font-bold text-emerald-700 dark:text-emerald-400 uppercase">
                {healthStatus}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] space-y-1">
              <span className="text-[var(--text-3)] block">بيئة المتصفح:</span>
              <span className="font-mono font-bold text-[var(--text)]">Playwright Chromium</span>
            </div>
            <div className="p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] space-y-1">
              <span className="text-[var(--text-3)] block">الإصدار المعتمد:</span>
              <span className="font-mono font-bold text-[var(--text)]">Site DNA v0.1.0</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
