import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/auth';
import { getToken } from './services/session';
import MainLayout from './layouts/MainLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DevicesPage from './pages/DevicesPage';
import DeviceDetailPage from './pages/DeviceDetailPage';
import InterfacesPage from './pages/InterfacesPage';
import AlertsPage from './pages/AlertsPage';
import TopologyPage from './pages/TopologyPage';
import WanPage from './pages/WanPage';
import SitesPage from './pages/SitesPage';
import ReportsPage from './pages/ReportsPage';
import UsersPage from './pages/UsersPage';
import SettingsPage from './pages/SettingsPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  // If no token is persisted we can boot immediately (login page); otherwise
  // wait for restoreSession() to validate the token against the backend.
  const [booted, setBooted] = useState(() => {
    const hasToken = !!getToken();
    if (!hasToken) useAuthStore.setState({ user: null, isAuthenticated: false });
    return !hasToken;
  });
  const restoreSession = useAuthStore((st) => st.restoreSession);

  // Validate any persisted token against the backend before rendering routes.
  // While booting we render a neutral splash so ProtectedRoute never bounces
  // a still-valid session to /login on refresh.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      await restoreSession();
      if (!cancelled) setBooted(true);
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!booted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-noc-bg text-noc-text">
        <div className="text-sm text-noc-text-dim animate-pulse">Restoring session…</div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="devices" element={<DevicesPage />} />
          <Route path="devices/:id" element={<DeviceDetailPage />} />
          <Route path="interfaces" element={<InterfacesPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="topology" element={<TopologyPage />} />
          <Route path="wan" element={<WanPage />} />
          <Route path="sites" element={<SitesPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

