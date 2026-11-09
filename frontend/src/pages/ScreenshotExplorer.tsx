import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useLang } from '../lib/i18n';
import {
  Camera,
  Monitor,
  Smartphone,
  Maximize2,
  X,
  ExternalLink,
  Download,
} from 'lucide-react';

export function ScreenshotExplorer({ runId }: { runId: string }) {
  const { t } = useLang();
  const [screenshots, setScreenshots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [deviceFilter, setDeviceFilter] = useState<'all' | 'desktop' | 'mobile'>('all');
  const [selectedImage, setSelectedImage] = useState<any | null>(null);

  useEffect(() => {
    api
      .getScreenshots(runId)
      .then((data) => {
        setScreenshots(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [runId]);

  const filtered = screenshots.filter((s) => {
    if (deviceFilter === 'all') return true;
    return s.device === deviceFilter;
  });

  return (
    <div className="space-y-6">
      {/* Device Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--hairline)] pb-4">
        <div>
          <h2 className="text-base font-bold text-[var(--text)]">{t('screens.title')}</h2>
          <p className="text-xs text-[var(--text-3)]">{t('screens.subtitle')}</p>
        </div>

        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[var(--hairline)]">
          <button
            onClick={() => setDeviceFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              deviceFilter === 'all'
                ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            {t('screens.filter_all')}
          </button>
          <button
            onClick={() => setDeviceFilter('desktop')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              deviceFilter === 'desktop'
                ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            <Monitor className="w-3.5 h-3.5" />
            <span>{t('screens.filter_desktop')}</span>
          </button>
          <button
            onClick={() => setDeviceFilter('mobile')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              deviceFilter === 'mobile'
                ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                : 'text-[var(--text-3)] hover:text-[var(--text)]'
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>{t('screens.filter_mobile')}</span>
          </button>
        </div>
      </div>

      {/* Gallery Grid */}
      {loading ? (
        <div className="py-16 text-center text-xs text-[var(--text-3)]">{t('common.loading')}</div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((item, idx) => (
            <div
              key={idx}
              className="group rounded-2xl border border-[var(--hairline)] bg-[var(--glass-tint)] overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col"
            >
              {/* Header Bar */}
              <div className="p-3 border-b border-[var(--hairline)] flex items-center justify-between text-xs bg-[var(--bg)]">
                <div className="flex items-center gap-1.5">
                  {item.device === 'desktop' ? (
                    <Monitor className="w-3.5 h-3.5 text-blue-500" />
                  ) : (
                    <Smartphone className="w-3.5 h-3.5 text-emerald-500" />
                  )}
                  <span className="font-semibold uppercase text-[10px] tracking-wide text-[var(--text-2)]">
                    {item.device}
                  </span>
                </div>
                <span className="font-mono text-[10px] text-[var(--text-3)] truncate max-w-[140px]">
                  {item.filename}
                </span>
              </div>

              {/* Image Thumbnail with Overlay */}
              <div
                className="relative aspect-video bg-black/10 overflow-hidden cursor-pointer"
                onClick={() => setSelectedImage(item)}
              >
                <img
                  src={item.api_url}
                  alt={item.filename}
                  loading="lazy"
                  className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 text-white">
                  <Maximize2 className="w-5 h-5" />
                  <span className="text-xs font-bold">{t('screens.preview')}</span>
                </div>
              </div>

              {/* Footer Info */}
              <div className="p-3 text-[11px] text-[var(--text-3)] truncate" title={item.page_url}>
                {item.page_url}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-16 text-center text-xs text-[var(--text-3)]">{t('screens.empty')}</div>
      )}

      {/* Lightbox / Fullscreen Image Preview Modal */}
      {selectedImage && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm p-4 flex items-center justify-center animate-in fade-in duration-200">
          <div className="relative max-w-5xl w-full max-h-[90vh] bg-[var(--bg)] rounded-3xl overflow-hidden border border-[var(--hairline)] shadow-2xl flex flex-col">
            {/* Modal Header */}
            <div className="p-4 border-b border-[var(--hairline)] flex items-center justify-between">
              <div>
                <div className="font-bold text-sm text-[var(--text)]">{selectedImage.filename}</div>
                <div className="text-xs text-[var(--text-3)]">{selectedImage.page_url}</div>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={selectedImage.api_url}
                  download={selectedImage.filename}
                  className="p-2 rounded-xl border border-[var(--hairline)] hover:bg-[var(--glass-inset)] text-[var(--text-2)] hover:text-[var(--text)]"
                  title="Download Image"
                >
                  <Download className="w-4 h-4" />
                </a>
                <button
                  onClick={() => setSelectedImage(null)}
                  className="p-2 rounded-xl border border-[var(--hairline)] hover:bg-[var(--glass-inset)] text-[var(--text-2)] hover:text-[var(--text)] cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Modal Scrollable Image */}
            <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-black/20">
              <img
                src={selectedImage.api_url}
                alt={selectedImage.filename}
                className="max-w-full max-h-[70vh] object-contain rounded-xl shadow-lg"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
