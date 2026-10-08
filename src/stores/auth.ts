import { create } from 'zustand';
import { apiService } from '../services/api';

export interface User {
  id: string;
  username: string;
  fullName: string;
  role: 'super_admin' | 'admin' | 'network_engineer' | 'operator' | 'viewer';
  email: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  apiAvailable: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkApiHealth: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('pnmp_token'),
  isLoading: false,
  apiAvailable: false,
  
  login: async (username: string, password: string) => {
    set({ isLoading: true });
    
    try {
      // Try API login first
      const response = await apiService.login(username, password);
      apiService.setToken(response.access_token);
      
      // Get user info
      try {
        const userInfo = await apiService.getCurrentUser();
        set({
          user: {
            id: userInfo.id.toString(),
            username: userInfo.username,
            fullName: userInfo.full_name,
            role: userInfo.role,
            email: userInfo.email,
          },
          isAuthenticated: true,
          isLoading: false,
          apiAvailable: true,
        });
      } catch {
        // Fallback if /me endpoint fails
        set({
          user: {
            id: '1',
            username,
            fullName: username === 'admin' ? 'Super Administrator' : 'User',
            role: username === 'admin' ? 'super_admin' : 'network_engineer',
            email: `${username}@pssn.ac.id`,
          },
          isAuthenticated: true,
          isLoading: false,
          apiAvailable: true,
        });
      }
      
      return true;
    } catch (error) {
      // API not available, use demo mode
      console.warn('Backend API not available, using demo mode');
      
      if (username && password) {
        set({
          user: {
            id: '1',
            username,
            fullName: username === 'admin' ? 'Super Administrator' : 'Network Engineer',
            role: username === 'admin' ? 'super_admin' : 'network_engineer',
            email: `${username}@pssn.ac.id`,
          },
          isAuthenticated: true,
          isLoading: false,
          apiAvailable: false,
        });
        return true;
      }
      
      set({ isLoading: false });
      return false;
    }
  },
  
  logout: () => {
    apiService.setToken(null);
    set({ user: null, isAuthenticated: false });
  },
  
  checkApiHealth: async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/health');
      const isHealthy = response.ok;
      set({ apiAvailable: isHealthy });
      return isHealthy;
    } catch {
      set({ apiAvailable: false });
      return false;
    }
  },
}));
