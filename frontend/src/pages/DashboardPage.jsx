import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getMyDocuments } from '../services/documentService';
import { downloadDischargeSummary } from '../services/dischargeService';

const KEYFRAMES = `
@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes drawPulse { from { stroke-dashoffset: 1200; } to { stroke-dashoffset: 0; } }
@keyframes breathe { 0%, 100% { opacity: 0.5; } 50% { opacity: 0.9; } }
.fade-up { animation: fadeUp 0.6s ease-out both; }
.draw-pulse { stroke-dasharray: 1200; animation: drawPulse 2.6s ease-out both; }
.breathe { animation: breathe 6s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) {
  .fade-up, .draw-pulse, .breathe { animation: none; }
  .draw-pulse { stroke-dasharray: none; }
}
`;

/**
 * Decorative hero artwork: concentric topographic rings with a heartbeat line.
 * Pure SVG, so it adds no image files or packages.
 */
function PulseAtlas() {
  const rings = [60, 110, 165, 225, 290, 360];

  return (
    <svg
      viewBox="0 0 800 400"
      className="pointer-events-none absolute inset-0 w-full h-full"
      preserveAspectRatio="xMaxYMid slice"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="pulseStroke" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="#A8DCC6" stopOpacity="0" />
          <stop offset="40%" stopColor="#A8DCC6" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#E9D3A0" stopOpacity="0.9" />
        </linearGradient>
      </defs>

      <g className="breathe" fill="none" stroke="#FFFFFF" strokeWidth="1">
        {rings.map((radius, index) => (
          <ellipse
            key={radius}
            cx="600"
            cy="200"
            rx={radius * 1.35}
            ry={radius * 0.85}
            opacity={0.14 - index * 0.015}
          />
        ))}
      </g>

      <path
        className="draw-pulse"
        d="M0 210 H250 L275 210 L292 150 L312 268 L332 110 L352 210 H480 L498 194 L512 226 L530 210 H800"
        fill="none"
        stroke="url(#pulseStroke)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <circle cx="332" cy="110" r="4" fill="#E9D3A0" opacity="0.9" />
    </svg>
  );
}

function Icon({ children }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className="w-5 h-5"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

const ICONS = {
  document: (
    <Icon>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
    </Icon>
  ),
  chart: (
    <Icon>
      <path d="M3 3v18h18" />
      <path d="M7 15l4-4 3 3 5-6" />
    </Icon>
  ),
  chat: (
    <Icon>
      <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" />
    </Icon>
  ),
  download: (
    <Icon>
      <path d="M12 3v12" />
      <path d="M7 10l5 5 5-5" />
      <path d="M5 21h14" />
    </Icon>
  ),
  arrow: (
    <Icon>
      <path d="M5 12h14" />
      <path d="M13 6l6 6-6 6" />
    </Icon>
  ),
};

const QUICK_LINKS = [
  {
    to: '/upload',
    title: 'Documents',
    text: 'View and upload your medical records.',
    icon: 'document',
    iconClass: 'bg-teal/10 text-teal',
    accent: 'bg-teal',
  },
  {
    to: '/timeline',
    title: 'Health timeline',
    text: 'Track your vitals and lab trends over time.',
    icon: 'chart',
    iconClass: 'bg-gold-soft text-[#7A5E22]',
    accent: 'bg-gold',
  },
  {
    to: '/chat',
    title: 'Ask HealthCura',
    text: 'Ask questions and get answers from your own records.',
    icon: 'chat',
    iconClass: 'bg-mint/40 text-teal-deep',
    accent: 'bg-mint',
  },
];

function QuickLinkCard({ link }) {
  return (
    <Link
      to={link.to}
      className="group relative bg-surface border border-line rounded-2xl p-6 overflow-hidden hover:-translate-y-1 hover:shadow-xl hover:shadow-teal/5 transition duration-300"
    >
      <div className={`absolute top-0 left-0 h-1 w-full ${link.accent}`} />
      <div className="flex items-start justify-between gap-4">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${link.iconClass}`}>
          {ICONS[link.icon]}
        </div>
        <span className="text-ink-muted group-hover:text-teal group-hover:translate-x-1 transition">
          {ICONS.arrow}
        </span>
      </div>
      <h2 className="font-serif text-xl text-ink mt-5 mb-1">{link.title}</h2>
      <p className="text-sm text-ink-muted leading-relaxed">{link.text}</p>
    </Link>
  );
}

function DashboardPage() {
  const { user } = useAuth();
  const [documentCount, setDocumentCount] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState('');

  useEffect(() => {
    getMyDocuments()
      .then((docs) => setDocumentCount(docs.length))
      .catch(() => setDocumentCount(0));
  }, []);

  const handleDownloadSummary = async () => {
    setIsDownloading(true);
    setDownloadError('');
    try {
      const pdfBlob = await downloadDischargeSummary();
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'HealthCura_Summary.pdf';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setDownloadError(detail || 'Unable to generate summary. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const firstName = user?.full_name?.split(' ')[0];
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const hasDocuments = documentCount !== null && documentCount > 0;

  return (
    <div className="min-h-screen bg-paper">
      <style>{KEYFRAMES}</style>

      <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        {/* Hero */}
        <section className="fade-up relative overflow-hidden rounded-3xl bg-linear-to-br from-teal-deep via-teal to-[#0F2F28] text-white p-8 md:p-12 min-h-[260px]">
          <PulseAtlas />
          <div className="pointer-events-none absolute -bottom-28 -right-10 w-96 h-96 rounded-full bg-gold/20 blur-3xl" />

          <div className="relative flex flex-col md:flex-row md:items-end md:justify-between gap-8">
            <div>
              <p className="text-sm tracking-wide text-mint mb-3">{greeting}</p>
              <h1 className="font-serif text-4xl md:text-5xl leading-tight">
                Welcome back, {firstName}
              </h1>
              <p className="text-white/70 mt-4 max-w-md leading-relaxed">
                {hasDocuments
                  ? 'Your records are organised and ready. Pick up where you left off.'
                  : 'Upload your first lab report to get a plain-language summary and timeline.'}
              </p>
            </div>

            <Link
              to="/upload"
              className="self-start md:self-auto inline-flex items-center gap-2 bg-gold text-ink px-6 py-3 rounded-full font-semibold shadow-xl shadow-black/25 hover:-translate-y-0.5 hover:bg-[#D6B56D] transition"
            >
              Upload a document
              {ICONS.arrow}
            </Link>
          </div>

          <div className="relative mt-10 inline-flex items-center gap-4 bg-white/10 backdrop-blur-sm border border-white/15 rounded-2xl px-6 py-4">
            <span className="font-serif text-4xl text-mint">
              {documentCount === null ? '–' : documentCount}
            </span>
            <span className="text-sm text-white/80">
              {documentCount === 1 ? 'document in your records' : 'documents in your records'}
            </span>
          </div>
        </section>

        {/* Quick links */}
        <section className="fade-up grid md:grid-cols-3 gap-6" style={{ animationDelay: '0.1s' }}>
          {QUICK_LINKS.map((link) => (
            <QuickLinkCard key={link.to} link={link} />
          ))}
        </section>

        {/* Discharge summary */}
        <section
          className="fade-up relative overflow-hidden bg-surface border border-line rounded-2xl p-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6"
          style={{ animationDelay: '0.2s' }}
        >
          <div className="absolute top-0 left-0 h-1 w-full bg-coral" />
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 shrink-0 rounded-xl bg-coral-soft text-[#A04E2A] flex items-center justify-center">
              {ICONS.download}
            </div>
            <div>
              <h2 className="font-serif text-2xl text-ink mb-1">Discharge summary</h2>
              <p className="text-sm text-ink-muted max-w-lg leading-relaxed">
                Download one organised PDF of your health records, ready to show your doctor. It is
                AI-generated and is not an official medical document.
              </p>
            </div>
          </div>

          <div className="flex flex-col items-start md:items-end gap-2">
            <button
              onClick={handleDownloadSummary}
              disabled={isDownloading || !hasDocuments}
              className="inline-flex items-center gap-2 bg-teal text-white px-6 py-3 rounded-full font-medium shadow-md shadow-teal/25 hover:bg-teal-deep hover:-translate-y-0.5 transition disabled:opacity-50 disabled:hover:translate-y-0"
            >
              {isDownloading ? 'Generating PDF...' : 'Download PDF'}
              {!isDownloading && ICONS.download}
            </button>
            {!hasDocuments && documentCount !== null && (
              <p className="text-xs text-ink-muted">Upload a document first.</p>
            )}
            {downloadError && <p className="text-sm text-red-700">{downloadError}</p>}
          </div>
        </section>
      </div>
    </div>
  );
}

export default DashboardPage;