import { create } from 'zustand';

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
  login: (username: string, password: string) => boolean;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  login: (username: string, _password: string) => {
    // Demo authentication - in production this calls the API
    if (username && _password) {
      set({
        user: {
          id: '1',
          username,
          fullName: username === 'admin' ? 'Super Administrator' : 'Network Engineer',
          role: username === 'admin' ? 'super_admin' : 'network_engineer',
          email: `${username}@pssn.ac.id`,
        },
        isAuthenticated: true,
      });
      return true;
    }
    return false;
  },
  logout: () => set({ user: null, isAuthenticated: false }),
}));
