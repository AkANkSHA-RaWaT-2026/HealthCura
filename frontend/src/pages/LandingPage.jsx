import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login as loginApi, signup as signupApi } from '../services/authService';
import { useAuth } from '../hooks/useAuth';

const KEYFRAMES = `
@keyframes floatY { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }
@keyframes drawLine { from { stroke-dashoffset: 400; } to { stroke-dashoffset: 0; } }
@keyframes fadeUp { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: translateY(0); } }
@keyframes modalIn { from { opacity: 0; transform: scale(0.96) translateY(8px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.float-slow { animation: floatY 7s ease-in-out infinite; }
.float-fast { animation: floatY 5s ease-in-out infinite; animation-delay: -2s; }
.draw-line { stroke-dasharray: 400; animation: drawLine 2.2s ease-out both; }
.fade-up { animation: fadeUp 0.8s ease-out both; }
.modal-in { animation: modalIn 0.25s ease-out both; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
`;

const STEPS = [
  { title: 'Upload', text: 'Add a photo or PDF of a lab report, prescription, or discharge summary.' },
  { title: 'Read', text: 'HealthCura reads the text from your document automatically.' },
  { title: 'Understand', text: 'You get a short summary written in plain language.' },
  { title: 'Track', text: 'Key results join your timeline, so you can see changes over time.' },
];

const FEATURES = [
  {
    title: 'Plain-language summaries',
    text: 'Each document is explained in simple words, with medical terms defined.',
    accent: 'bg-teal',
  },
  {
    title: 'Health timeline',
    text: 'Follow values like hemoglobin and platelets across all your reports.',
    accent: 'bg-[#E9C46A]',
  },
  {
    title: 'Ask your records',
    text: 'Ask "What was my glucose level?" and get answers from your own documents.',
    accent: 'bg-[#7DD3B0]',
  },
  {
    title: 'Discharge summary PDF',
    text: 'Download one organised summary of your records to show your doctor.',
    accent: 'bg-[#F4A261]',
  },
  {
    title: 'Private to you',
    text: 'Your documents are visible only to your account. Nobody else can open them.',
    accent: 'bg-[#5FA8D3]',
  },
  {
    title: 'A reference, not a diagnosis',
    text: 'HealthCura explains what your documents say. It does not replace your doctor.',
    accent: 'bg-[#B8A1E3]',
  },
];

function Field({ label, ...inputProps }) {
  return (
    <label className="block">
      <span className="block text-sm text-ink-muted mb-1.5">{label}</span>
      <input
        {...inputProps}
        className="w-full px-3.5 py-2.5 border border-line rounded-lg bg-paper/40 focus:bg-surface focus:outline-none focus:ring-2 focus:ring-teal transition"
      />
    </label>
  );
}

function AuthModal({ mode, onModeChange, onClose }) {
  const [form, setForm] = useState({ fullName: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { loginUser } = useAuth();
  const navigate = useNavigate();
  const isSignup = mode === 'signup';

  // Escape closes the popup, the usual expectation for a dialog
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const updateField = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (isSignup) {
        // The backend defaults the role to "patient", so no role is sent
        await signupApi({
          full_name: form.fullName,
          email: form.email,
          password: form.password,
        });
      }
      const data = await loginApi({ email: form.email, password: form.password });
      loginUser(data.access_token, data.user);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      const fallback = isSignup
        ? 'Unable to create account. Please try again.'
        : 'Unable to log in. Check your details and try again.';
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg).join(', ')
        : detail || fallback;
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={isSignup ? 'Create account' : 'Log in'}
        onClick={(event) => event.stopPropagation()}
        className="modal-in relative w-full max-w-md bg-surface rounded-2xl shadow-2xl overflow-hidden"
      >
        <div className="h-1.5 bg-linear-to-r from-teal via-[#7DD3B0] to-[#E9C46A]" />

        <div className="p-8">
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="absolute top-5 right-5 text-ink-muted hover:text-ink text-xl leading-none"
          >
            ×
          </button>

          <div className="flex gap-1 p-1 bg-paper rounded-lg mb-6 w-fit">
            {['login', 'signup'].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => onModeChange(tab)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                  mode === tab ? 'bg-surface text-teal shadow-sm' : 'text-ink-muted hover:text-ink'
                }`}
              >
                {tab === 'login' ? 'Log in' : 'Sign up'}
              </button>
            ))}
          </div>

          <h2 className="font-serif text-2xl text-ink mb-1">
            {isSignup ? 'Create your free account' : 'Welcome back'}
          </h2>
          <p className="text-sm text-ink-muted mb-6">
            {isSignup
              ? 'Start keeping your medical records in one place.'
              : 'Log in to see your health records.'}
          </p>

          {error && (
            <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-4">
              {error}
            </p>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <Field
                label="Full name"
                name="fullName"
                type="text"
                value={form.fullName}
                onChange={updateField}
                required
              />
            )}
            <Field
              label="Email"
              name="email"
              type="email"
              value={form.email}
              onChange={updateField}
              required
            />
            <Field
              label="Password"
              name="password"
              type="password"
              value={form.password}
              onChange={updateField}
              required
              minLength={isSignup ? 8 : undefined}
            />
            {isSignup && <p className="text-xs text-ink-muted -mt-2">At least 8 characters</p>}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-teal text-white py-2.5 rounded-lg font-medium shadow-md shadow-teal/30 hover:bg-teal-deep hover:-translate-y-0.5 transition disabled:opacity-50"
            >
              {isSubmitting
                ? isSignup
                  ? 'Creating account...'
                  : 'Logging in...'
                : isSignup
                  ? 'Create account'
                  : 'Log in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function HeroPreview() {
  return (
    <div className="relative w-full max-w-md mx-auto fade-up" style={{ animationDelay: '0.2s' }}>
      <div className="float-slow bg-surface/95 backdrop-blur rounded-2xl shadow-2xl p-6">
        <div className="flex justify-between items-center mb-3">
          <p className="text-xs text-ink-muted">Example timeline</p>
          <span className="text-xs bg-teal/10 text-teal px-2.5 py-1 rounded-full">Hemoglobin</span>
        </div>
        <p className="font-serif text-4xl text-ink">
          13.8 <span className="text-base text-ink-muted">g/dL</span>
        </p>
        <svg viewBox="0 0 300 100" className="w-full h-28 mt-4">
          <defs>
            <linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#2F6F5E" stopOpacity="0.28" />
              <stop offset="100%" stopColor="#2F6F5E" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d="M0 70 C 50 60, 80 40, 120 50 S 200 30, 240 35 S 280 20, 300 15 L300 100 L0 100 Z"
            fill="url(#trendFill)"
          />
          <path
            className="draw-line"
            d="M0 70 C 50 60, 80 40, 120 50 S 200 30, 240 35 S 280 20, 300 15"
            fill="none"
            stroke="#2F6F5E"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <div className="float-fast absolute -left-6 top-10 bg-surface rounded-xl shadow-lg px-4 py-3 border border-line">
        <p className="text-xs text-ink-muted">Platelets</p>
        <p className="font-semibold text-ink">
          265 <span className="text-xs text-ink-muted">x10³/uL</span>
        </p>
      </div>

      <div className="float-slow absolute -right-4 bottom-6 bg-ink text-white rounded-xl shadow-lg px-4 py-3 max-w-[220px]">
        <p className="text-xs text-[#7DD3B0]">Summary ready</p>
        <p className="text-sm">Your report explained in plain language.</p>
      </div>
    </div>
  );
}

function LandingPage() {
  const [authMode, setAuthMode] = useState(null); // null, 'login', or 'signup'

  const openLogin = () => setAuthMode('login');
  const openSignup = () => setAuthMode('signup');
  const closeAuth = () => setAuthMode(null);

  return (
    <div className="min-h-screen bg-paper text-ink">
      <style>{KEYFRAMES}</style>

      {/* Hero */}
      <section className="relative overflow-hidden bg-linear-to-br from-teal-deep via-[#24594B] to-ink text-white">
        <div className="pointer-events-none absolute -top-32 -left-24 w-96 h-96 rounded-full bg-[#7DD3B0]/20 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 right-0 w-[28rem] h-[28rem] rounded-full bg-[#E9C46A]/15 blur-3xl" />

        <header className="relative z-10 max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
          <span className="font-serif text-2xl tracking-tight">HealthCura</span>
          <nav className="flex items-center gap-3 sm:gap-6 text-sm">
            <a href="#how-it-works" className="text-white/75 hover:text-white hidden sm:inline">
              How it works
            </a>
            <a href="#features" className="text-white/75 hover:text-white hidden sm:inline">
              Features
            </a>
            <button onClick={openLogin} className="text-white/85 hover:text-white">
              Log in
            </button>
            <button
              onClick={openSignup}
              className="bg-white text-teal-deep px-4 py-2 rounded-full font-medium hover:bg-[#E9F7F1] transition"
            >
              Sign up
            </button>
          </nav>
        </header>

        <div className="relative z-10 max-w-6xl mx-auto px-6 pt-10 pb-24 grid lg:grid-cols-2 gap-14 items-center">
          <div className="fade-up">
            <span className="inline-flex items-center gap-2 text-xs font-medium bg-white/10 border border-white/15 px-3 py-1.5 rounded-full mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-[#7DD3B0]" />
              Medical document intelligence for patients
            </span>
            <h1 className="font-serif text-5xl md:text-6xl leading-[1.05] mb-6">
              Your medical records,{' '}
              <span className="text-[#7DD3B0] italic">explained clearly.</span>
            </h1>
            <p className="text-lg text-white/75 max-w-xl mb-10">
              Upload lab reports and prescriptions. HealthCura reads them, tracks your key numbers
              over time, and answers your questions from your own documents.
            </p>

            <div className="flex flex-wrap gap-4">
              <button
                onClick={openSignup}
                className="bg-[#E9C46A] text-ink px-7 py-3.5 rounded-full font-semibold shadow-xl shadow-black/20 hover:-translate-y-0.5 hover:bg-[#F2D27F] transition"
              >
                Get started free
              </button>
              <button
                onClick={openLogin}
                className="border border-white/30 text-white px-7 py-3.5 rounded-full font-medium hover:bg-white/10 transition"
              >
                I already have an account
              </button>
            </div>

            <p className="mt-8 text-sm text-white/60">
              Private to your account · A reference aid, not a diagnosis
            </p>
          </div>

          <HeroPreview />
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="bg-surface py-24">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-sm font-medium text-teal mb-3">How it works</p>
          <h2 className="font-serif text-4xl text-ink mb-3">From paper report to clear answers</h2>
          <p className="text-ink-muted mb-14 max-w-xl">
            Four steps. Everything after the upload is generated from your own document.
          </p>

          <div className="relative grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
            <div className="hidden lg:block absolute top-6 left-[12%] right-[12%] h-px bg-linear-to-r from-teal/10 via-teal/40 to-teal/10" />
            {STEPS.map((step, index) => (
              <div key={step.title} className="relative">
                <div className="relative z-10 w-12 h-12 rounded-full bg-teal text-white flex items-center justify-center font-serif text-lg shadow-lg shadow-teal/30">
                  {index + 1}
                </div>
                <h3 className="font-serif text-2xl text-ink mt-6 mb-2">{step.title}</h3>
                <p className="text-sm text-ink-muted leading-relaxed">{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-sm font-medium text-teal mb-3">Features</p>
          <h2 className="font-serif text-4xl text-ink mb-14">Everything starts from your documents</h2>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="group relative bg-surface border border-line rounded-2xl p-7 overflow-hidden hover:-translate-y-1 hover:shadow-xl transition duration-300"
              >
                <div className={`absolute top-0 left-0 h-1 w-full ${feature.accent} opacity-80`} />
                <h3 className="font-serif text-xl text-ink mb-2">{feature.title}</h3>
                <p className="text-sm text-ink-muted leading-relaxed">{feature.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Closing call to action */}
      <section className="px-6 pb-24">
        <div className="max-w-6xl mx-auto relative overflow-hidden rounded-3xl bg-linear-to-br from-teal-deep to-ink text-white p-12 md:p-16 text-center">
          <div className="pointer-events-none absolute -top-20 right-0 w-80 h-80 rounded-full bg-[#E9C46A]/20 blur-3xl" />
          <h2 className="relative font-serif text-4xl md:text-5xl mb-4">Start with one report.</h2>
          <p className="relative text-white/75 mb-8 max-w-lg mx-auto">
            Upload it once and see the summary, the timeline, and your questions answered from the
            same document.
          </p>
          <button
            onClick={openSignup}
            className="relative bg-[#E9C46A] text-ink px-8 py-3.5 rounded-full font-semibold hover:-translate-y-0.5 hover:bg-[#F2D27F] transition"
          >
            Create a free account
          </button>
        </div>
      </section>

      <footer className="border-t border-line bg-surface">
        <div className="max-w-6xl mx-auto px-6 py-8 text-sm text-ink-muted flex flex-col sm:flex-row justify-between gap-3">
          <span className="font-serif text-lg text-ink">HealthCura</span>
          <span>HealthCura is an AI reference tool. It does not diagnose or replace medical advice.</span>
        </div>
      </footer>

      {authMode && (
        <AuthModal mode={authMode} onModeChange={setAuthMode} onClose={closeAuth} />
      )}
    </div>
  );
}

export default LandingPage;