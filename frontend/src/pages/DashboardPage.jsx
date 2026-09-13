import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getMyDocuments } from '../services/documentService';

const upcomingFeatures = [
  { name: 'Ask HealthCura', description: 'Chat with your medical records' },
  { name: 'Discharge Summary', description: 'Generate a summary for your next visit' },
];

function DashboardPage() {
  const { user, logoutUser } = useAuth();
  const [documentCount, setDocumentCount] = useState(null);

  useEffect(() => {
    getMyDocuments()
      .then((docs) => setDocumentCount(docs.length))
      .catch(() => setDocumentCount(0));
  }, []);

  const firstName = user?.full_name?.split(' ')[0];
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="min-h-screen bg-paper">
      <div className="max-w-2xl mx-auto px-6 py-10">
        <header className="flex justify-between items-center pb-6 border-b border-line">
          <span className="font-serif text-xl text-ink">HealthCura</span>
          <button
            onClick={logoutUser}
            className="text-sm text-ink-muted hover:text-ink"
          >
            Log out
          </button>
        </header>

        <div className="mt-8 mb-10">
          <h1 className="font-serif text-3xl text-ink">
            {greeting}, {firstName}
          </h1>
          <p className="text-ink-muted mt-1">{user?.email}</p>
        </div>

        <Link
          to="/upload"
          className="block bg-surface border border-line rounded-lg p-6 hover:border-teal transition-colors"
        >
          <div className="flex justify-between items-start">
            <div>
              <h2 className="font-serif text-xl text-ink mb-1">Documents</h2>
              <p className="text-sm text-ink-muted">
                View and upload your medical records
              </p>
            </div>
            <span className="font-serif text-3xl text-teal">
              {documentCount === null ? '–' : documentCount}
            </span>
          </div>
        </Link>

        <Link
          to="/timeline"
          className="block bg-surface border border-line rounded-lg p-6 hover:border-teal transition-colors mt-4"
        >
          <h2 className="font-serif text-xl text-ink mb-1">Health Timeline</h2>
          <p className="text-sm text-ink-muted">
            Track your vitals and lab trends over time
          </p>
        </Link>

        <Link
          to="/chat"
          className="block bg-surface border border-line rounded-lg p-6 hover:border-teal transition-colors mt-4"
        >
          <h2 className="font-serif text-xl text-ink mb-1">Ask HealthCura</h2>
          <p className="text-sm text-ink-muted">Chat with your medical records</p>
        </Link>

        <div className="mt-6 space-y-px">
          {upcomingFeatures.map((feature) => (
            <div
              key={feature.name}
              className="flex justify-between items-center py-4 px-6 bg-surface/50"
            >
              <div>
                <p className="text-ink-muted font-medium">{feature.name}</p>
                <p className="text-sm text-ink-muted/70">{feature.description}</p>
              </div>
              <span className="text-xs text-ink-muted/60 border border-line rounded px-2 py-1">
                Not yet available
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;