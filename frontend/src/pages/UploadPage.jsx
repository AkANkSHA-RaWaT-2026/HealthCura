import { useState, useEffect, useRef } from 'react';
import {
  uploadDocument,
  getMyDocuments,
  generateSummary,
  deleteDocument,
} from '../services/documentService';
import { getSavedSummary } from '../services/summaryService';

const ALLOWED_TYPES = ['.jpg', '.jpeg', '.png', '.webp', '.pdf'];
const MAX_SIZE_MB = 10;

const KEYFRAMES = `
@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes scanSweep { 0% { transform: translateY(-10%); opacity: 0; } 15% { opacity: 1; } 85% { opacity: 1; } 100% { transform: translateY(110%); opacity: 0; } }
@keyframes spin { to { transform: rotate(360deg); } }
.fade-up { animation: fadeUp 0.5s ease-out both; }
.scan-line { animation: scanSweep 2.4s ease-in-out infinite; }
.spin-slow { animation: spin 1.6s linear infinite; }
@media (prefers-reduced-motion: reduce) {
  .fade-up, .scan-line, .spin-slow { animation: none; }
}
`;

/**
 * Decorative drop-zone artwork: a glass microscope slide with a faint cell
 * pattern. The scan line only animates while a file is being dragged over it.
 */
function SpecimenSlide({ active }) {
  const cells = [
    [90, 60, 22], [160, 110, 14], [230, 58, 18], [300, 120, 26], [370, 72, 16],
    [125, 150, 12], [265, 160, 20], [340, 168, 10], [60, 130, 9], [410, 150, 13],
  ];

  return (
    <svg viewBox="0 0 480 200" className="w-full max-w-xs h-auto" aria-hidden="true">
      <defs>
        <linearGradient id="slideGlass" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#E7EFEA" stopOpacity="0.9" />
        </linearGradient>
        <linearGradient id="scanGlow" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#C9A55A" stopOpacity="0" />
          <stop offset="50%" stopColor="#C9A55A" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#C9A55A" stopOpacity="0" />
        </linearGradient>
      </defs>

      <rect x="40" y="40" width="400" height="120" rx="10" fill="url(#slideGlass)" stroke="#1F5E4F" strokeOpacity="0.25" />
      <rect x="40" y="40" width="400" height="120" rx="10" fill="none" stroke="#FFFFFF" strokeWidth="2" />

      <g fill="#1F5E4F" opacity="0.12">
        {cells.map(([cx, cy, r], index) => (
          <circle key={index} cx={cx + 40} cy={cy - 10} r={r / 2} />
        ))}
      </g>
      <g fill="none" stroke="#1F5E4F" strokeOpacity="0.18" strokeWidth="1">
        {cells.map(([cx, cy, r], index) => (
          <circle key={`ring-${index}`} cx={cx + 40} cy={cy - 10} r={r} />
        ))}
      </g>

      {active && (
        <g style={{ clipPath: 'inset(0 round 10px)' }}>
          <rect x="40" y="40" width="400" height="22" fill="url(#scanGlow)" className="scan-line" />
        </g>
      )}

      <line x1="440" y1="60" x2="460" y2="60" stroke="#C9A55A" strokeWidth="2" strokeLinecap="round" />
      <line x1="440" y1="140" x2="460" y2="140" stroke="#C9A55A" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** Returns the file extension in uppercase, or "FILE" if the name has none. */
function fileTypeLabel(filename) {
  const parts = (filename || '').split('.');
  const extension = parts.length > 1 ? parts.pop().toUpperCase() : '';
  return extension || 'FILE';
}

function UploadPage() {
  const [documents, setDocuments] = useState([]);
  const [summaries, setSummaries] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [generatingId, setGeneratingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  /** Loads the saved summary (with flagged results) for each document that has one. */
  const loadSavedSummaries = async (docs) => {
    const documentsWithSummary = docs.filter((doc) => doc.ai_summary);
    const results = await Promise.allSettled(
      documentsWithSummary.map((doc) => getSavedSummary(doc.id))
    );

    const nextSummaries = {};
    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        nextSummaries[documentsWithSummary[index].id] = result.value;
      }
    });
    setSummaries(nextSummaries);
  };

  const loadDocuments = async () => {
    try {
      const docs = await getMyDocuments();
      setDocuments(docs);
      await loadSavedSummaries(docs);
    } catch {
      setError('Unable to load your documents.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const processFile = async (file) => {
    if (!file) return;
    setError('');

    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_TYPES.includes(extension)) {
      setError(`File type not allowed. Accepted: ${ALLOWED_TYPES.join(', ')}`);
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_SIZE_MB}MB.`);
      return;
    }

    setIsUploading(true);
    try {
      await uploadDocument(file);
      await loadDocuments();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    processFile(event.dataTransfer.files[0]);
  };

  /**
   * Generates the summary on the server, then reloads the document list.
   * The response is stored separately, because it is a summary, not a document.
   */
  const handleGenerateSummary = async (documentId) => {
    setError('');
    setGeneratingId(documentId);
    try {
      const result = await generateSummary(documentId);
      setSummaries((prev) => ({ ...prev, [documentId]: result }));
      const docs = await getMyDocuments();
      setDocuments(docs);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Unable to generate summary.');
    } finally {
      setGeneratingId(null);
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Delete this document? This cannot be undone.')) return;

    setDeletingId(documentId);
    try {
      await deleteDocument(documentId);
      setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
      setSummaries((prev) => {
        const next = { ...prev };
        delete next[documentId];
        return next;
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Unable to delete document.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-paper">
      <style>{KEYFRAMES}</style>

      <div className="max-w-3xl mx-auto px-6 py-12 w-full">
        <header className="fade-up mb-10">
          <p className="text-sm tracking-wide text-teal mb-2">Your library</p>
          <div className="flex items-end justify-between gap-4">
            <h1 className="font-serif text-4xl text-ink">Your documents</h1>
            {!isLoading && (
              <span className="text-sm text-ink-muted pb-1">
                {documents.length} {documents.length === 1 ? 'file' : 'files'}
              </span>
            )}
          </div>
        </header>

        {/* Drop zone */}
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
          className={`fade-up group relative overflow-hidden rounded-3xl border-2 border-dashed p-10 text-center cursor-pointer transition duration-300 ${
            isDragging
              ? 'border-teal bg-teal/5 scale-[1.01]'
              : 'border-line bg-surface hover:border-teal/50 hover:bg-surface'
          } ${isUploading ? 'pointer-events-none' : ''}`}
        >
          <div className="flex flex-col items-center">
            <SpecimenSlide active={isDragging || isUploading} />

            <div className="mt-6 flex items-center gap-3">
              {isUploading && (
                <span className="spin-slow inline-block w-4 h-4 rounded-full border-2 border-teal border-t-transparent" />
              )}
              <p className="text-ink font-medium">
                {isUploading ? 'Reading your document...' : 'Drop a file here, or click to choose one'}
              </p>
            </div>
            <p className="text-sm text-ink-muted mt-2">
              Lab reports and prescriptions · JPG, PNG, WebP, PDF · Max {MAX_SIZE_MB}MB
            </p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_TYPES.join(',')}
            onChange={(event) => processFile(event.target.files[0])}
            disabled={isUploading}
            className="hidden"
          />
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-700 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
            {error}
          </p>
        )}

        {/* Document list */}
        <div className="mt-10">
          {isLoading ? (
            <p className="text-ink-muted">Loading...</p>
          ) : documents.length === 0 ? (
            <div className="text-center py-12 text-ink-muted">
              <p className="font-serif text-xl text-ink mb-1">No documents yet</p>
              <p className="text-sm">Upload a lab report above to get started.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {documents.map((doc, index) => {
                const summary = summaries[doc.id];
                const summaryText = summary?.summary || doc.ai_summary;
                const flagged = summary?.flagged || [];

                return (
                  <article
                    key={doc.id}
                    className="fade-up bg-surface border border-line rounded-2xl p-6 hover:shadow-lg hover:shadow-teal/5 transition duration-300"
                    style={{ animationDelay: `${index * 0.05}s` }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-4 min-w-0">
                        <div className="shrink-0 w-12 h-14 rounded-lg bg-teal/10 border border-teal/15 flex flex-col items-center justify-center">
                          <span className="text-[10px] font-semibold tracking-wider text-teal">
                            {fileTypeLabel(doc.original_filename)}
                          </span>
                          <span className="mt-1 w-5 h-px bg-gold" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-ink font-medium truncate">
                            {doc.original_filename || 'Untitled document'}
                          </p>
                          <p className="text-xs text-ink-muted mt-0.5">
                            {doc.document_type && <span className="mr-2">{doc.document_type}</span>}
                            {doc.created_at && new Date(doc.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDelete(doc.id)}
                        disabled={deletingId === doc.id}
                        className="shrink-0 text-xs text-ink-muted hover:text-red-700 px-3 py-1.5 rounded-full hover:bg-red-50 transition disabled:opacity-50"
                      >
                        {deletingId === doc.id ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>

                    {doc.document_type === 'Other' && (
                      <div className="mt-5 rounded-xl bg-gold-soft px-4 py-3">
                        <p className="text-sm text-ink">
                          We couldn't read any supported blood test values in this document.
                          Try a clearer photo or scan. The document is still stored and can be
                          searched in chat.
                        </p>
                      </div>
                    )}

                    {summaryText ? (
                      <div className="mt-5 relative bg-paper rounded-xl pl-5 pr-4 py-4">
                        <div className="absolute left-0 top-3 bottom-3 w-1 rounded-full bg-teal" />
                        <p className="text-xs font-semibold tracking-wide text-teal mb-2">AI summary</p>
                        <p className="text-sm text-ink leading-relaxed">{summaryText}</p>

                        {flagged.length > 0 && (
                          <div className="mt-4">
                            <p className="text-xs font-semibold tracking-wide text-coral mb-2">
                              Outside the reference range
                            </p>
                            <ul className="space-y-1.5">
                              {flagged.map((item) => (
                                <li key={item} className="text-sm text-ink flex gap-2">
                                  <span className="text-coral">•</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {summary?.disclaimer && (
                          <p className="mt-4 text-xs text-ink-muted leading-relaxed">
                            {summary.disclaimer}
                          </p>
                        )}
                      </div>
                    ) : (
                      <div className="mt-5 flex items-center justify-between gap-4 rounded-xl border border-dashed border-line px-4 py-3">
                        <p className="text-sm text-ink-muted">No summary yet for this document.</p>
                        <button
                          onClick={() => handleGenerateSummary(doc.id)}
                          disabled={generatingId === doc.id}
                          className="shrink-0 bg-teal text-white text-sm px-4 py-2 rounded-full font-medium hover:bg-teal-deep transition disabled:opacity-50"
                        >
                          {generatingId === doc.id ? 'Generating...' : 'Generate summary'}
                        </button>
                      </div>
                    )}

                    {doc.ocr_text && !summaryText && (
                      <p className="text-sm text-ink-muted mt-3 line-clamp-2">
                        {doc.ocr_text.slice(0, 180)}
                      </p>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default UploadPage;