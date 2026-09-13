import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getAdminStats, getPatients, exportPatientReport } from '../services/adminService';

function AdminPage() {
  const { logoutUser } = useAuth();
  const [stats, setStats] = useState(null);
  const [patients, setPatients] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [exportingId, setExportingId] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsData, patientsData] = await Promise.all([
          getAdminStats(),
          getPatients(),
        ]);
        setStats(statsData);
        setPatients(patientsData);
      } catch {
        setError('Unable to load admin dashboard.');
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []);

  const handleExport = async (patientId, patientName) => {
    setExportingId(patientId);
    setError('');
    try {
      const pdfBlob = await exportPatientReport(patientId);
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `HealthCura_Report_${patientName.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Unable to export report.');
    } finally {
      setExportingId(null);
    }
  };

  if (isLoading) {
    return <div className="min-h-screen bg-paper flex items-center justify-center text-ink-muted">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-paper">
      <div className="max-w-3xl mx-auto px-6 py-10">
        <header className="flex justify-between items-center pb-6 border-b border-line">
          <span className="font-serif text-xl text-ink">HealthCura Admin</span>
          <button onClick={logoutUser} className="text-sm text-ink-muted hover:text-ink">
            Log out
          </button>
        </header>

        <h1 className="font-serif text-2xl text-ink mt-8 mb-6">Dashboard</h1>

        {error && <p className="text-sm text-red-700 mb-4">{error}</p>}

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Patients', value: stats?.total_patients },
            { label: 'Documents', value: stats?.total_documents },
            { label: 'Health Records', value: stats?.total_health_records },
            { label: 'Chat Messages', value: stats?.total_chat_messages },
          ].map((stat) => (
            <div key={stat.label} className="bg-surface border border-line rounded-lg p-4">
              <p className="font-serif text-2xl text-teal">{stat.value ?? '-'}</p>
              <p className="text-xs text-ink-muted">{stat.label}</p>
            </div>
          ))}
        </div>

        <h2 className="font-serif text-xl text-ink mb-4">Patients</h2>

        {patients.length === 0 ? (
          <p className="text-ink-muted">No patients registered yet.</p>
        ) : (
          <div className="bg-surface border border-line rounded-lg divide-y divide-line">
            {patients.map((patient) => (
              <div key={patient.id} className="p-4 flex justify-between items-center">
                <div>
                  <p className="text-ink font-medium">{patient.full_name}</p>
                  <p className="text-sm text-ink-muted">{patient.email}</p>
                  <p className="text-xs text-ink-muted">
                    {patient.document_count} document{patient.document_count !== 1 ? 's' : ''}
                  </p>
                </div>
                <button
                  onClick={() => handleExport(patient.id, patient.full_name)}
                  disabled={exportingId === patient.id || patient.document_count === 0}
                  className="text-sm text-teal hover:text-teal-deep disabled:opacity-40"
                >
                  {exportingId === patient.id ? 'Exporting...' : 'Export report'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminPage;