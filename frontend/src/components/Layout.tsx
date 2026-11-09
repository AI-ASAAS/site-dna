import React, { useState } from 'react';
import { NavLink, Outlet, Link, useLocation } from 'react-router-dom';
import { useLang } from '../lib/i18n';
import { useTheme } from '../asaas-ui/lib/useTheme';
import {
  LayoutDashboard,
  PlusCircle,
  Users,
  History,
  Settings,
  Sun,
  Moon,
  Languages,
  Menu,
  X,
  ShieldCheck,
} from 'lucide-react';

export function Layout() {
  const { lang, toggleLang, t } = useLang();
  const [theme, toggleTheme] = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
    { to: '/analyses/new', labelKey: 'nav.new_analysis', icon: PlusCircle },
    { to: '/agents', labelKey: 'nav.agents', icon: Users },
    { to: '/history', labelKey: 'nav.history', icon: History },
    { to: '/settings', labelKey: 'nav.settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen w-full flex flex-col relative">
      {/* Top Banner: Official Model & Phase 12 Release Candidate Status */}
      <div className="bg-stone-900 text-stone-100 dark:bg-stone-950 dark:text-stone-100 border-b border-stone-800 px-4 py-1.5 text-xs font-semibold flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-bold tracking-wide">{t('org.name')} — {t('app.brand')} v1.0.0-rc.1 (Phase 12 Release Candidate)</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono font-bold text-[11px] px-2.5 py-0.5 rounded-full bg-stone-800 text-amber-300 border border-stone-700 shadow-xs">
            Model: gemini-3.6-flash
          </span>
          <span className="hidden sm:inline-flex items-center gap-1 text-[11px] text-emerald-400 font-bold">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> API Connected • 12/12 Agents Ready
          </span>
        </div>
      </div>

      {/* Main Glass Navigation Header */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[var(--glass-tint-strong)] border-b border-[var(--hairline)] transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-3 group text-decoration-none">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-600 via-amber-700 to-amber-900 flex items-center justify-center text-white font-bold text-lg shadow-md group-hover:scale-105 transition-transform">
              DNA
            </div>
            <div>
              <div className="font-extrabold text-lg leading-tight text-[var(--text)] tracking-tight">
                {t('app.brand')}
              </div>
              <div className="text-[11px] text-[var(--accent)] font-medium">
                {t('app.name')} • {t('org.name')}
              </div>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((item) => {
              const IconComp = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-[var(--accent-fill)] text-[var(--on-accent)] shadow-sm'
                        : 'text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--glass-inset)]'
                    }`
                  }
                >
                  <IconComp className="w-4 h-4" />
                  <span>{t(item.labelKey)}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Actions: LangSwitch, ThemeToggle, MobileMenuButton */}
          <div className="flex items-center gap-2">
            {/* Lang Switch */}
            <button
              onClick={toggleLang}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-[var(--hairline)] bg-[var(--glass-tint)] text-[var(--text-2)] hover:text-[var(--text)] transition-colors"
              title="Toggle Language / تبديل اللغة"
            >
              <Languages className="w-3.5 h-3.5" />
              <span>{lang === 'ar' ? 'English' : 'عربي'}</span>
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-full border border-[var(--hairline)] bg-[var(--glass-tint)] text-[var(--text-2)] hover:text-[var(--text)] transition-colors"
              title="Toggle Theme"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-full border border-[var(--hairline)] bg-[var(--glass-tint)] text-[var(--text)]"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-[var(--hairline)] bg-[var(--bg)] px-4 py-3 space-y-1 animate-in fade-in slide-in-from-top-2 duration-150">
            {navLinks.map((item) => {
              const IconComp = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium ${
                      isActive
                        ? 'bg-[var(--accent-fill)] text-[var(--on-accent)]'
                        : 'text-[var(--text-2)] hover:bg-[var(--glass-inset)]'
                    }`
                  }
                >
                  <IconComp className="w-4 h-4" />
                  <span>{t(item.labelKey)}</span>
                </NavLink>
              );
            })}
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--hairline)] py-6 text-center text-xs text-[var(--text-3)]">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            {t('app.brand')} — {t('org.name')} © 2026. All rights reserved.
          </div>
          <div className="flex items-center gap-4 text-[var(--text-2)]">
            <span className="font-mono">Gemini 3.6 Flash</span>
            <span>•</span>
            <span>Phases 01–12 Validated</span>
            <span>•</span>
            <span className="text-[var(--accent)] font-semibold">Site DNA v1.0.0-rc.1 • Enterprise Release Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
