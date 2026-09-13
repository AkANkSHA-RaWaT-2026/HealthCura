import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getMyDocuments } from '../services/documentService';
import { downloadDischargeSummary } from '../services/dischargeService';

function DashboardPage() {
  const { user, logoutUser } = useAuth();
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

        <div className="bg-surface border border-line rounded-lg p-6 mt-4">
          <h2 className="font-serif text-xl text-ink mb-1">Discharge Summary</h2>
          <p className="text-sm text-ink-muted mb-3">
            Download an AI-generated summary of your health records
          </p>
          <button
            onClick={handleDownloadSummary}
            disabled={isDownloading}
            className="text-sm text-teal hover:text-teal-deep disabled:opacity-50"
          >
            {isDownloading ? 'Generating PDF...' : 'Download summary'}
          </button>
          {downloadError && <p className="text-sm text-red-700 mt-2">{downloadError}</p>}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;