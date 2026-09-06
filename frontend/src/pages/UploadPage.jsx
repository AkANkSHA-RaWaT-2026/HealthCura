import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { uploadDocument, getMyDocuments } from '../services/documentService';
import { useAuth } from '../hooks/useAuth';

const ALLOWED_TYPES = ['.jpg', '.jpeg', '.png', '.pdf'];
const MAX_SIZE_MB = 10;

function UploadPage() {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const { logoutUser } = useAuth();

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
  // eslint-disable-next-line react-hooks/set-state-in-effect -- async fetch-on-mount, setState only happens after await resolves
  loadDocuments();
}, []);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
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
      await loadDocuments(); // refresh the list to show the new upload
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
      e.target.value = ''; // allows re-selecting the same file if needed
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-slate-800">My Documents</h1>
          <div className="space-x-4">
            <Link to="/dashboard" className="text-blue-600 hover:underline">
              Dashboard
            </Link>
            <button onClick={logoutUser} className="text-red-600 hover:underline">
              Log out
            </button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Upload a lab report, prescription, or discharge summary
          </label>
          <input
            type="file"
            accept=".jpg,.jpeg,.png,.pdf"
            onChange={handleFileChange}
            disabled={isUploading}
            className="block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer"
          />
          <p className="text-xs text-slate-500 mt-2">
            Accepted: JPG, PNG, PDF · Max {MAX_SIZE_MB}MB
          </p>

          {isUploading && (
            <p className="mt-3 text-sm text-blue-600">
              Processing document (this can take a few seconds)...
            </p>
          )}
          {error && (
            <p className="mt-3 text-sm text-red-600">{error}</p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md">
          <h2 className="text-lg font-semibold text-slate-800 p-4 border-b">
            Uploaded Documents
          </h2>

          {isLoading ? (
            <p className="p-4 text-slate-500">Loading...</p>
          ) : documents.length === 0 ? (
            <p className="p-4 text-slate-500">No documents uploaded yet.</p>
          ) : (
            <ul className="divide-y">
              {documents.map((doc) => (
                <li key={doc.id} className="p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-slate-800">
                        {doc.original_filename}
                      </p>
                      <p className="text-xs text-slate-500">
                        {new Date(doc.created_at).toLocaleString()} · {doc.file_type.toUpperCase()}
                      </p>
                    </div>
                    <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-700">
                      {doc.ocr_status}
                    </span>
                  </div>
                  {doc.ocr_text && (
                    <p className="text-sm text-slate-600 mt-2 line-clamp-3">
                      {doc.ocr_text.slice(0, 200)}
                      {doc.ocr_text.length > 200 ? '...' : ''}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default UploadPage;