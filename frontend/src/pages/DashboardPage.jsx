// frontend/src/pages/DashboardPage.jsx
import { useAuth } from '../hooks/useAuth';

function DashboardPage() {
  const { user, logoutUser } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">
          Welcome, {user?.full_name}
        </h1>
        <p className="text-slate-600 mb-4">
          Email: {user?.email} · Role: {user?.role}
        </p>
        <button
          onClick={logoutUser}
          className="bg-red-600 text-white px-4 py-2 rounded font-medium hover:bg-red-700"
        >
          Log out
        </button>
      </div>
    </div>
  );
}

export default DashboardPage;