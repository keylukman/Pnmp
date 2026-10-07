import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';
import { useDeviceStore } from '../stores/devices';
import {
  LayoutDashboard, Server, Network, AlertTriangle, Map, Globe,
  BarChart3, Users, Settings, LogOut, ChevronDown, ChevronRight,
  Menu, X, Shield, Radio, FileText, Bell, User
} from 'lucide-react';

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<string[]>(['monitoring', 'network', 'administration']);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { user, logout } = useAuthStore();
  const { alerts } = useDeviceStore();
  const navigate = useNavigate();

  const openAlertCount = alerts.filter(a => a.status === 'open').length;

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
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-noc-primary to-blue-600 flex items-center justify-center flex-shrink-0">
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
                  <NavLink to="/alerts" className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-all duration-150 ${
                      isActive
                        ? 'bg-noc-primary/10 text-noc-primary border-l-2 border-noc-primary'
                        : 'text-noc-text-muted hover:text-noc-text hover:bg-noc-surface'
                    }`
                  }>
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>Alerts</span>
                    {openAlertCount > 0 && (
                      <span className="ml-auto bg-noc-danger/20 text-noc-danger text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                        {openAlertCount}
                      </span>
                    )}
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
                    <span>WAN</span>
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
                <BarChart3 className="w-4 h-4 flex-shrink-0" />
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

        {/* Sidebar footer */}
        {sidebarOpen && (
          <div className="p-3 border-t border-noc-border">
            <div className="flex items-center gap-2 px-2 py-2 rounded-lg bg-noc-surface/50">
              <div className="w-2 h-2 rounded-full bg-noc-success animate-pulse" />
              <span className="text-[10px] text-noc-text-muted">System Healthy</span>
              <span className="ml-auto text-[10px] text-noc-text-muted">v1.0.0</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-noc-header border-b border-noc-border flex items-center justify-between px-4 lg:px-6 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileMenuOpen(true)} className="lg:hidden p-2 rounded-lg hover:bg-noc-surface text-noc-text-muted">
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden md:block">
              <p className="text-xs text-noc-text-muted">PSSN Network Management Platform</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Alerts indicator */}
            <button className="relative p-2 rounded-lg hover:bg-noc-surface text-noc-text-muted hover:text-noc-text transition-colors">
              <Bell className="w-4 h-4" />
              {openAlertCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-noc-danger text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                  {openAlertCount}
                </span>
              )}
            </button>

            {/* User menu */}
            <div className="relative">
              <button onClick={() => setShowUserMenu(!showUserMenu)} className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-noc-surface transition-colors">
                <div className="w-7 h-7 rounded-full bg-noc-primary/20 flex items-center justify-center">
                  <User className="w-3.5 h-3.5 text-noc-primary" />
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-xs font-medium text-noc-text">{user?.fullName || 'Admin'}</p>
                  <p className="text-[10px] text-noc-text-muted">{user?.role === 'super_admin' ? 'Super Admin' : user?.role?.replace(/_/g, ' ')}</p>
                </div>
                <ChevronDown className="w-3 h-3 text-noc-text-muted hidden md:block" />
              </button>

              {showUserMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                  <div className="absolute right-0 top-full mt-1 w-48 bg-noc-surface border border-noc-border rounded-lg shadow-xl z-50 py-1">
                    <div className="px-3 py-2 border-b border-noc-border">
                      <p className="text-sm font-medium text-noc-text">{user?.fullName}</p>
                      <p className="text-xs text-noc-text-muted">{user?.email}</p>
                    </div>
                    <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-noc-text-muted hover:text-noc-text hover:bg-noc-surface-2 transition-colors">
                      <Settings className="w-3.5 h-3.5" />
                      Settings
                    </button>
                    <button onClick={handleLogout} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-noc-danger hover:bg-noc-danger/10 transition-colors">
                      <LogOut className="w-3.5 h-3.5" />
                      Logout
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
