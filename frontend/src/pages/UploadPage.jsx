// frontend/src/pages/UploadPage.jsx
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { uploadDocument, getMyDocuments } from '../services/documentService';

const ALLOWED_TYPES = ['.jpg', '.jpeg', '.png', '.pdf'];
const MAX_SIZE_MB = 10;

function UploadPage() {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const loadDocuments = async () => {
    try {
      const docs = await getMyDocuments();
      setDocuments(docs);
    } catch {
      setError('Unable to load your documents.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- async fetch-on-mount, setState only after await resolves
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

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    processFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="min-h-screen bg-paper">
      <div className="max-w-2xl mx-auto px-6 py-10">
        <header className="flex justify-between items-center pb-6 border-b border-line">
          <Link to="/dashboard" className="font-serif text-xl text-ink">
            HealthCura
          </Link>
          <Link to="/dashboard" className="text-sm text-ink-muted hover:text-ink">
            Dashboard
          </Link>
        </header>

        <h1 className="font-serif text-2xl text-ink mt-8 mb-6">Your documents</h1>

        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
          className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
            isDragging ? 'border-teal bg-teal/5' : 'border-line hover:border-teal/50'
          }`}
        >
          <p className="text-ink font-medium">
            {isUploading ? 'Processing document...' : 'Drop a file here, or click to choose one'}
          </p>
          <p className="text-sm text-ink-muted mt-1">
            Lab reports, prescriptions, discharge summaries · JPG, PNG, PDF · Max {MAX_SIZE_MB}MB
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_TYPES.join(',')}
            onChange={(e) => processFile(e.target.files[0])}
            disabled={isUploading}
            className="hidden"
          />
        </div>

        {error && <p className="mt-3 text-sm text-red-700">{error}</p>}

        <div className="mt-8">
          {isLoading ? (
            <p className="text-ink-muted">Loading...</p>
          ) : documents.length === 0 ? (
            <p className="text-ink-muted">No documents yet. Upload one above to get started.</p>
          ) : (
            <div className="divide-y divide-line">
              {documents.map((doc) => (
                <div key={doc.id} className="py-4">
                  <div className="flex justify-between items-baseline">
                    <p className="text-ink font-medium">{doc.original_filename}</p>
                    <p className="text-xs text-ink-muted">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {doc.ocr_text && (
                    <p className="text-sm text-ink-muted mt-1 line-clamp-2">
                      {doc.ocr_text.slice(0, 180)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default UploadPage;