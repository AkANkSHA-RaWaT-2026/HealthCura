// frontend/src/context/AuthContext.jsx
import { useState, useEffect } from 'react';
import { AuthContext } from './AuthContextObject';
import { getCurrentUser } from '../services/authService';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // If there's no token at all, we're never "loading" - skip straight to false
  const [loading, setLoading] = useState(() => !!localStorage.getItem('access_token'));

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    getCurrentUser()
      .then((userData) => setUser(userData))
      .catch(() => {
        localStorage.removeItem('access_token');
      })
      .finally(() => setLoading(false));
  }, []);

  const loginUser = (token, userData) => {
    localStorage.setItem('access_token', token);
    setUser(userData);
  };

  const logoutUser = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, loginUser, logoutUser }}>
      {children}
    </AuthContext.Provider>
  );
}