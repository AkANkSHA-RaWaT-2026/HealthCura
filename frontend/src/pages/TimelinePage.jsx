import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getMyTimeline } from '../services/timelineService';

function TimelinePage() {
  const [records, setRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
  const loadTimeline = async () => {
    try {
      const data = await getMyTimeline();
      setRecords(data);
    } catch {
      setError('Unable to load your health timeline.');
    } finally {
      setIsLoading(false);
    }
  };
  loadTimeline();
}, []);

  const groupedByMetric = records.reduce((groups, record) => {
    const key = record.metric_name;
    if (!groups[key]) groups[key] = [];
    groups[key].push({
      // Fall back to created_at if no recorded_date was extracted from the document
      date: record.recorded_date || record.created_at.split('T')[0],
      value: record.value,
      unit: record.unit,
    });
    return groups;
  }, {});

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

        <h1 className="font-serif text-2xl text-ink mt-8 mb-2">Health Timeline</h1>
        <p className="text-sm text-ink-muted mb-6">
          Metrics automatically extracted from your uploaded documents.
        </p>

        {isLoading && <p className="text-ink-muted">Loading...</p>}
        {error && <p className="text-red-700">{error}</p>}

        {!isLoading && Object.keys(groupedByMetric).length === 0 && (
          <p className="text-ink-muted">
            No health metrics found yet. Upload a lab report to see trends here.
          </p>
        )}

        <div className="space-y-8">
          {Object.entries(groupedByMetric).map(([metricName, points]) => (
            <div key={metricName} className="bg-surface border border-line rounded-lg p-5">
              <h2 className="font-serif text-lg text-ink mb-1">{metricName}</h2>
              <p className="text-xs text-ink-muted mb-4">
                {points.length} reading{points.length !== 1 ? 's' : ''}
                {points[0]?.unit ? ` · ${points[0].unit}` : ''}
              </p>

              {points.length === 1 ? (
                <p className="text-2xl font-serif text-teal">
                  {points[0].value} <span className="text-sm text-ink-muted">{points[0].unit}</span>
                </p>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={points}>
                    <CartesianGrid stroke="#DDE5E1" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#5B6E68' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#5B6E68' }} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#2F6F5E"
                      strokeWidth={2}
                      dot={{ fill: '#2F6F5E', r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TimelinePage;