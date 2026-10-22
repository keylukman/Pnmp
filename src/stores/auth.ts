import { create } from 'zustand';
import { apiService } from '../services/api';
import { getToken, getStoredUser, setStoredUser, clearSession } from '../services/session';

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
  restoreSession: () => Promise<void>;
  checkApiHealth: () => Promise<boolean>;
}

/**
 * Session persistence strategy:
 * - The JWT is stored in localStorage by apiService.setToken().
 * - The user profile is mirrored to localStorage ONLY so a page refresh can
 *   immediately re-render the app instead of bouncing to /login.
 * - On every app load we call restoreSession(): it re-validates the token
 *   against GET /users/me. If the backend rejects it (expired/invalid), the
 *   session is cleared and the user lands on the login page. Client-side
 *   state is NEVER an authorization source — the API enforces RBAC per request.
 */
export const useAuthStore = create<AuthState>((set) => ({
  // Hydrate synchronously from persisted session so ProtectedRoute does not
  // redirect to /login during the first render after a refresh.
  user: getStoredUser<User>(),
  isAuthenticated: !!getToken(),
  isLoading: false,
  apiAvailable: false,

  login: async (username: string, password: string) => {
    set({ isLoading: true });

    try {
      // Real API login only. There is intentionally NO demo-mode fallback
      // here: fabricated sessions were the reason refreshes lost state and
      // fake data looked live.
      const response = await apiService.login(username, password);
      apiService.setToken(response.access_token);

      const userInfo = await apiService.getCurrentUser();
      const user: User = {
        id: userInfo.id.toString(),
        username: userInfo.username,
        fullName: userInfo.full_name ?? userInfo.username,
        role: userInfo.role,
        email: userInfo.email ?? '',
      };
      setStoredUser(user);
      set({ user, isAuthenticated: true, isLoading: false, apiAvailable: true });
      return true;
    } catch (error) {
      apiService.setToken(null);
      setStoredUser(null);
      const msg = error instanceof Error ? error.message : '';
      if (msg === 'Unauthorized') {
        // Backend reachable but credentials rejected — stay on login, show error.
        set({ isLoading: false, apiAvailable: true });
      } else {
        // Network failure / backend down: explicit DISCONNECTED state.
        set({ isLoading: false, apiAvailable: false });
      }
      return false;
    }
  },

  logout: () => {
    apiService.setToken(null);
    clearSession();
    set({ user: null, isAuthenticated: false });
  },

  /** Called once at app start. Validates any persisted token against the API. */
  restoreSession: async () => {
    const token = getToken();
    if (!token) {
      set({ user: null, isAuthenticated: false, apiAvailable: false });
      return;
    }
    try {
      const userInfo = await apiService.getCurrentUser();
      const user: User = {
        id: userInfo.id.toString(),
        username: userInfo.username,
        fullName: userInfo.full_name ?? userInfo.username,
        role: userInfo.role,
        email: userInfo.email ?? '',
      };
      setStoredUser(user);
      set({ user, isAuthenticated: true, apiAvailable: true });
    } catch {
      // Token expired or backend unreachable → clear so UI shows login with
      // an honest DISCONNECTED hint rather than a half-restored fake session.
      clearSession();
      const healthy = await apiService.healthCheck();
      set({ user: null, isAuthenticated: false, apiAvailable: healthy });
    }
  },

  checkApiHealth: async () => {
    const isHealthy = await apiService.healthCheck();
    set({ apiAvailable: isHealthy });
    return isHealthy;
  },
}));
