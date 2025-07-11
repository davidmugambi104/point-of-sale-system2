import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      await checkAuthStatus();
    } else {
      setLoading(false);
    }
  };

  const checkAuthStatus = async () => {
    try {
      await axios.get('/auth/verify');
      const token = localStorage.getItem('token');
      updateUserFromToken(token);
    } catch (error) {
      clearAuth();
    } finally {
      setLoading(false);
    }
  };

  const updateUserFromToken = (token) => {
    try {
      const decoded = jwtDecode(token);
      setUser(decoded);
    } catch (error) {
      clearAuth();
    }
  };

  const clearAuth = () => {
    delete axios.defaults.headers.common['Authorization'];
    localStorage.removeItem('token');
    setUser(null);
  };

  const login = async (credentials) => {
    const { data } = await axios.post('/auth/login', credentials);
    localStorage.setItem('token', data.token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${data.token}`;
    updateUserFromToken(data.token);
  };

  const logout = async () => {
    await axios.post('/auth/logout');
    clearAuth();
  };

  const isAuthenticated = () => !!user;

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};