import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';
import {
  LayoutDashboard, Server, Network, AlertTriangle, Map, Globe,
  BarChart3, Users, Settings, LogOut, ChevronDown, ChevronRight,
  Menu, X, Shield, Radio, FileText
} from 'lucide-react';

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<string[]>(['monitoring', 'network', 'administration']);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const toggleSection = (section: string) => {
    setExpandedSections((prev) =>
      prev.includes(section) ? prev.filter((s) => s !== section) : [...prev, section]
    );
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-all duration-150 ${
      isActive
        ? 'bg-noc-primary/10 text-noc-primary border-l-2 border-noc-primary'
        : 'text-noc-text-muted hover:text-noc-text hover:bg-noc-surface'
    }`;

  const sectionHeaderClass = "flex items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wider text-noc-text-muted cursor-pointer hover:text-noc-text transition-colors";

  return (
    <div className="flex h-screen overflow-hidden bg-noc-bg">
      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-60' : 'w-16'} ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:relative z-50 h-full bg-noc-sidebar border-r border-noc-border transition-all duration-200 flex flex-col`}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-noc-border">
          <div className="w-8 h-8 rounded-lg bg-noc-primary flex items-center justify-center flex-shrink-0">
            <Network className="w-5 h-5 text-white" />
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <h1 className="text-sm font-bold text-noc-text tracking-wide">PNMP</h1>
              <p className="text-[10px] text-noc-text-muted">Network Management</p>
            </div>
          )}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="ml-auto hidden lg:block text-noc-text-muted hover:text-noc-text">
            <Menu className="w-4 h-4" />
          </button>
          <button onClick={() => setMobileMenuOpen(false)} className="ml-auto lg:hidden text-noc-text-muted hover:text-noc-text">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
          {/* Dashboard */}
          <NavLink to="/" className={navItemClass} end>
            <LayoutDashboard className="w-4 h-4 flex-shrink-0" />
            {sidebarOpen && <span>Dashboard</span>}
          </NavLink>

          {/* Monitoring Section */}
          {sidebarOpen && (
            <div className="pt-3">
              <div className={sectionHeaderClass} onClick={() => toggleSection('monitoring')}>
                <span>Monitoring</span>
                {expandedSections.includes('monitoring') ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              </div>
              {expandedSections.includes('monitoring') && (
                <div className="space-y-0.5 ml-2">
                  <NavLink to="/devices" className={navItemClass}>
                    <Server className="w-4 h-4 flex-shrink-0" />
                    <span>Devices</span>
                  </NavLink>
                  <NavLink to="/interfaces" className={navItemClass}>
                    <Radio className="w-4 h-4 flex-shrink-0" />
                    <span>Interfaces</span>
                  </NavLink>
                  <NavLink to="/alerts" className={navItemClass}>
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>Alerts</span>
                  </NavLink>
                </div>
              )}
            </div>
          )}

          {/* Network Section */}
          {sidebarOpen && (
            <div className="pt-3">
              <div className={sectionHeaderClass} onClick={() => toggleSection('network')}>
                <span>Network</span>
                {expandedSections.includes('network') ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              </div>
              {expandedSections.includes('network') && (
                <div className="space-y-0.5 ml-2">
                  <NavLink to="/topology" className={navItemClass}>
                    <Map className="w-4 h-4 flex-shrink-0" />
                    <span>Topology</span>
                  </NavLink>
                  <NavLink to="/wan" className={navItemClass}>
                    <Globe className="w-4 h-4 flex-shrink-0" />
                    <span>WAN Monitoring</span>
                  </NavLink>
                  <NavLink to="/sites" className={navItemClass}>
                    <Shield className="w-4 h-4 flex-shrink-0" />
                    <span>Sites</span>
                  </NavLink>
                </div>
              )}
            </div>
          )}

          {/* Reports */}
          {sidebarOpen && (
            <div className="pt-3">
              <NavLink to="/reports" className={navItemClass}>
                <FileText className="w-4 h-4 flex-shrink-0" />
                <span>Reports</span>
              </NavLink>
            </div>
          )}

          {/* Administration */}
          {sidebarOpen && (
            <div className="pt-3">
              <div className={sectionHeaderClass} onClick={() => toggleSection('administration')}>
                <span>Administration</span>
                {expandedSections.includes('administration') ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              </div>
              {expandedSections.includes('administration') && (
                <div className="space-y-0.5 ml-2">
                  <NavLink to="/users" className={navItemClass}>
                    <Users className="w-4 h-4 flex-shrink-0" />
                    <span>Users</span>
                  </NavLink>
                  <NavLink to="/settings" className={navItemClass}>
                    <Settings className="w-4 h-4 flex-shrink-0" />
                    <span>Settings</span>
                  </NavLink>
                </div>
              )}
            </div>
          )}
        </nav>

        {/* User section */}
        <div className="border-t border-noc-border p-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-noc-surface-2 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-noc-primary">
                {user?.fullName?.charAt(0) || 'U'}
              </span>
            </div>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-noc-text truncate">{user?.fullName}</p>
                <p className="text-[10px] text-noc-text-muted">{user?.role?.replace('_', ' ')}</p>
              </div>
            )}
            {sidebarOpen && (
              <button onClick={handleLogout} className="text-noc-text-muted hover:text-noc-danger transition-colors">
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-12 bg-noc-header border-b border-noc-border flex items-center justify-between px-4 flex-shrink-0">
          <button onClick={() => setMobileMenuOpen(true)} className="lg:hidden text-noc-text-muted hover:text-noc-text">
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-noc-success status-up"></div>
            <span className="text-xs text-noc-text-muted">System Online</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-noc-text-muted">
              {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-noc-text-muted" />
              <span className="text-xs text-noc-text-muted">v1.0.0</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
