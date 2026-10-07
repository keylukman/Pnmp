import { useState } from 'react';
import { Save, Database, Globe, Bell, Shield, Clock, Server, Wifi } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { id: 'general', label: 'General', icon: Server },
    { id: 'monitoring', label: 'Monitoring', icon: Wifi },
    { id: 'snmp', label: 'SNMP', icon: Database },
    { id: 'integrations', label: 'Integrations', icon: Globe },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Settings</h1>
          <p className="text-sm text-noc-text-muted">Platform configuration and preferences</p>
        </div>
      </div>

      <div className="flex gap-4">
        {/* Tabs */}
        <div className="w-48 flex-shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-noc-primary/10 text-noc-primary border-l-2 border-noc-primary'
                    : 'text-noc-text-muted hover:text-noc-text hover:bg-noc-surface'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 bg-noc-surface border border-noc-border rounded-lg p-6">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">General Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Application Name</label>
                  <input type="text" defaultValue="PNMP" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Organization</label>
                  <input type="text" defaultValue="PSSN - Universitas" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Timezone</label>
                  <select className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                    <option>Asia/Jakarta (WIB, UTC+7)</option>
                    <option>Asia/Makassar (WITA, UTC+8)</option>
                    <option>Asia/Jayapura (WIT, UTC+9)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Theme</label>
                  <select className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                    <option>Dark (NOC)</option>
                    <option>Light</option>
                    <option>System</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'monitoring' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">Monitoring Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Polling Interval (seconds)</label>
                  <input type="number" defaultValue={60} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                  <p className="text-[10px] text-noc-text-muted mt-1">Recommended: 30-60 seconds for resource-constrained environments</p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Timeout (seconds)</label>
                  <input type="number" defaultValue={5} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Retries</label>
                  <input type="number" defaultValue={2} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Data Retention (days)</label>
                  <input type="number" defaultValue={90} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="auto-discover" defaultChecked className="rounded border-noc-border" />
                  <label htmlFor="auto-discover" className="text-sm text-noc-text">Enable auto-discovery</label>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'snmp' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">SNMP Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Default SNMP Version</label>
                  <select className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                    <option>SNMPv2c</option>
                    <option>SNMPv3</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Default Community String</label>
                  <input type="password" defaultValue="••••••••" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                  <p className="text-[10px] text-noc-text-muted mt-1">Stored encrypted in database. Never sent to frontend.</p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">SNMP Port</label>
                  <input type="number" defaultValue={161} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div className="p-3 bg-noc-bg border border-noc-border rounded-lg">
                  <p className="text-xs text-noc-text-muted">SNMPv3 settings are configured per-device in device credentials.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">External Integrations</h3>
              <div className="space-y-4">
                <div className="p-4 bg-noc-bg border border-noc-border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-noc-text">Zabbix Integration</h4>
                    <span className="text-xs px-2 py-0.5 rounded bg-noc-warning/10 text-noc-warning">Not Configured</span>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-noc-text-muted mb-1">Zabbix URL</label>
                      <input type="text" placeholder="https://zabbix.example.com" className="w-full px-3 py-2 bg-noc-surface border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-noc-text-muted mb-1">API Token</label>
                      <input type="password" placeholder="Enter API token" className="w-full px-3 py-2 bg-noc-surface border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                    </div>
                    <button className="px-3 py-1.5 text-xs text-noc-text-muted border border-noc-border rounded-lg hover:bg-noc-surface transition-colors">Test Connection</button>
                  </div>
                </div>

                <div className="p-4 bg-noc-bg border border-noc-border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-noc-text">Aruba Central</h4>
                    <span className="text-xs px-2 py-0.5 rounded bg-noc-text-muted/10 text-noc-text-muted">Coming Soon</span>
                  </div>
                  <p className="text-xs text-noc-text-muted">Aruba Central API integration will be available in a future release.</p>
                </div>

                <div className="p-4 bg-noc-bg border border-noc-border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-noc-text">Syslog Receiver</h4>
                    <span className="text-xs px-2 py-0.5 rounded bg-noc-text-muted/10 text-noc-text-muted">Coming Soon</span>
                  </div>
                  <p className="text-xs text-noc-text-muted">Syslog integration for centralized logging.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">Notification Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-noc-bg border border-noc-border rounded-lg">
                  <div>
                    <p className="text-sm text-noc-text">Email Notifications</p>
                    <p className="text-xs text-noc-text-muted">Send alerts via email</p>
                  </div>
                  <div className="w-10 h-5 bg-noc-surface-2 rounded-full relative cursor-pointer">
                    <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-noc-text-muted rounded-full transition-transform" />
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 bg-noc-bg border border-noc-border rounded-lg">
                  <div>
                    <p className="text-sm text-noc-text">Telegram Notifications</p>
                    <p className="text-xs text-noc-text-muted">Send alerts via Telegram bot</p>
                  </div>
                  <div className="w-10 h-5 bg-noc-surface-2 rounded-full relative cursor-pointer">
                    <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-noc-text-muted rounded-full transition-transform" />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Minimum Severity for Notification</label>
                  <select className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                    <option>Critical Only</option>
                    <option>High and Above</option>
                    <option>Warning and Above</option>
                    <option>All</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">Security Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">JWT Token Expiry (hours)</label>
                  <input type="number" defaultValue={24} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Max Login Attempts</label>
                  <input type="number" defaultValue={5} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Lockout Duration (minutes)</label>
                  <input type="number" defaultValue={30} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">CORS Origins</label>
                  <input type="text" defaultValue="http://localhost:5173" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="audit-log" defaultChecked className="rounded border-noc-border" />
                  <label htmlFor="audit-log" className="text-sm text-noc-text">Enable Audit Logging</label>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="rate-limit" className="rounded border-noc-border" />
                  <label htmlFor="rate-limit" className="text-sm text-noc-text">Enable API Rate Limiting</label>
                </div>
              </div>
            </div>
          )}

          {/* Save button */}
          <div className="mt-6 pt-4 border-t border-noc-border flex justify-end">
            <button className="flex items-center gap-2 px-4 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
