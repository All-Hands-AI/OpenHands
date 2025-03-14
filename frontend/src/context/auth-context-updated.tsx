import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => void;
  githubTokenIsSet: boolean;
  setGitHubTokenIsSet: (value: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
  initialGithubTokenIsSet?: boolean;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ 
  children, 
  initialGithubTokenIsSet = false 
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [githubTokenIsSet, setGitHubTokenIsSet] = useState(initialGithubTokenIsSet);

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setLoading(false);
        return;
      }
      
      try {
        // Set default auth header for all requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        // Get user profile
        const response = await axios.get('/api/auth/profile');
        setUser(response.data);
      } catch (err) {
        console.error('Auth check error:', err);
        // Clear invalid token
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Use FormData for OAuth2 password flow compatibility
      const formData = new FormData();
      formData.append('username', email); // OAuth2 uses username field for email
      formData.append('password', password);

      const response = await axios.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      // Store token
      const token = response.data.access_token;
      localStorage.setItem('token', token);
      
      // Set default auth header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Get user profile
      const profileResponse = await axios.get('/api/auth/profile');
      setUser(profileResponse.data);
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (
    username: string, 
    email: string, 
    password: string, 
    confirmPassword: string
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      await axios.post('/api/auth/register', {
        username,
        email,
        password,
        confirm_password: confirmPassword,
      });
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(err.response?.data?.detail || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    // Clear token and user data
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    githubTokenIsSet,
    setGitHubTokenIsSet,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
