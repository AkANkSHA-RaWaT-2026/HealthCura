import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const patientNavItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/upload', label: 'Documents' },
  { to: '/timeline', label: 'Timeline' },
  { to: '/chat', label: 'Ask HealthCura' },
];

const adminNavItems = [{ to: '/admin', label: 'Dashboard' }];

function Layout({ children }) {
  const { user, logoutUser } = useAuth();
  const location = useLocation();
  const navItems = user?.role === 'admin' ? adminNavItems : patientNavItems;

  return (
    <div className="min-h-screen bg-paper flex flex-col">
      <nav className="sticky top-0 z-10 bg-surface border-b border-line">
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between h-14">
          <div className="flex items-center gap-8">
            <span className="font-serif text-lg text-ink">HealthCura</span>
            <div className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`text-sm px-3 py-2 rounded ${
                      isActive ? 'text-teal font-medium bg-teal/5' : 'text-ink-muted hover:text-ink'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-ink-muted hidden sm:inline">{user?.full_name}</span>
            <button onClick={logoutUser} className="text-sm text-ink-muted hover:text-ink">
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="flex-1 flex flex-col">{children}</main>
    </div>
  );
}

export default Layout;