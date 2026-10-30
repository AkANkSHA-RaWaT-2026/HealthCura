import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { signup as signupApi, login as loginApi } from '../services/authService';
import { useAuth } from '../hooks/useAuth';

function SignupPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'patient',
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await signupApi(formData);
      const loginData = await loginApi({
        email: formData.email,
        password: formData.password,
      });
      loginUser(loginData.access_token, loginData.user);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((d) => d.msg).join(', ')
        : detail || 'Unable to create account. Please try again.';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center px-6 py-10">
      <div className="w-full max-w-sm">
        <p className="font-serif text-2xl text-ink text-center mb-8">HealthCura</p>

        <div className="bg-surface border border-line rounded-lg p-8">
          <h1 className="font-serif text-xl text-ink mb-6">Create your account</h1>

          {error && <p className="text-sm text-red-700 mb-4">{error}</p>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-ink-muted mb-1">Full name</label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-line rounded focus:outline-none focus:ring-2 focus:ring-teal"
              />
            </div>

            <div>
              <label className="block text-sm text-ink-muted mb-1">Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-line rounded focus:outline-none focus:ring-2 focus:ring-teal"
              />
            </div>

            <div>
              <label className="block text-sm text-ink-muted mb-1">Password</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                minLength={8}
                className="w-full px-3 py-2 border border-line rounded focus:outline-none focus:ring-2 focus:ring-teal"
              />
              <p className="text-xs text-ink-muted mt-1">At least 8 characters</p>
            </div>

            <div>
              <label className="block text-sm text-ink-muted mb-1">I am a</label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-line rounded focus:outline-none focus:ring-2 focus:ring-teal bg-surface"
              >
                <option value="patient">Patient</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-teal text-white py-2 rounded font-medium hover:bg-teal-deep disabled:opacity-50"
            >
              {isSubmitting ? 'Creating account...' : 'Sign up'}
            </button>
          </form>

          <p className="mt-6 text-sm text-ink-muted text-center">
            Already have an account?{' '}
            <Link to="/login" className="text-teal hover:text-teal-deep">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default SignupPage;