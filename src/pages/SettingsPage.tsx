import { useState } from 'react';
import { Save, Database, Globe, Bell, Shield, Clock, Server, Wifi, Check, AlertCircle } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

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
        {saved && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-noc-success/10 border border-noc-success/20 rounded-lg">
            <Check className="w-4 h-4 text-noc-success" />
            <span className="text-sm text-noc-success">Settings saved</span>
          </div>
        )}
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
                    ? 'bg-noc-primary/10 text-noc-primary border border-noc-primary/20'
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Application Name</label>
                  <input type="text" defaultValue="PNMP" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Organization</label>
                  <input type="text" defaultValue="PSSN - Unit Teknologi Informasi" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Timezone</label>
                  <select className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                    <option>Asia/Jakarta (WIB, UTC+7)</option>
                    <option>Asia/Makassar (WITA, UTC+8)</option>
                    <option>Asia/Jayapura (WIT, UTC+9)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Date Format</label>
                  <select className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                    <option>YYYY-MM-DD HH:mm:ss</option>
                    <option>DD/MM/YYYY HH:mm:ss</option>
                    <option>MM/DD/YYYY HH:mm:ss</option>
                  </select>
                </div>
              </div>
              <div className="pt-4 border-t border-noc-border">
                <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
              </div>
            </div>
          )}

          {activeTab === 'monitoring' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">Monitoring Configuration</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Polling Interval (seconds)</label>
                  <input type="number" defaultValue={60} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                  <p className="text-[10px] text-noc-text-muted mt-1">How often to poll devices for metrics</p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Timeout (seconds)</label>
                  <input type="number" defaultValue={5} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Retries</label>
                  <input type="number" defaultValue={2} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Data Retention (days)</label>
                  <input type="number" defaultValue={90} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
              </div>
              <div className="space-y-3 pt-4 border-t border-noc-border">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <div>
                    <p className="text-sm text-noc-text">Enable ICMP Ping</p>
                    <p className="text-[10px] text-noc-text-muted">Use ICMP ping for basic connectivity check</p>
                  </div>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <div>
                    <p className="text-sm text-noc-text">Enable SNMP Polling</p>
                    <p className="text-[10px] text-noc-text-muted">Collect metrics via SNMP protocol</p>
                  </div>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <div>
                    <p className="text-sm text-noc-text">Enable WebSocket Updates</p>
                    <p className="text-[10px] text-noc-text-muted">Real-time dashboard updates via WebSocket</p>
                  </div>
                </label>
              </div>
              <div className="pt-4 border-t border-noc-border">
                <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
              </div>
            </div>
          )}

          {activeTab === 'snmp' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">SNMP Configuration</h3>
              <div className="p-3 bg-noc-info/10 border border-noc-info/20 rounded-lg flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-noc-info flex-shrink-0 mt-0.5" />
                <p className="text-xs text-noc-info">SNMP credentials are stored encrypted. Default community string can be set here and will be used when device-specific credentials are not configured.</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Default SNMP Version</label>
                  <select className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                    <option>SNMPv2c</option>
                    <option>SNMPv3</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Default Community String</label>
                  <input type="password" defaultValue="••••••••" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">SNMP Port</label>
                  <input type="number" defaultValue={161} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Timeout (seconds)</label>
                  <input type="number" defaultValue={5} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
              </div>
              <div className="pt-4 border-t border-noc-border">
                <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">Integrations</h3>
              
              {/* Zabbix */}
              <div className="border border-noc-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-noc-primary/10 flex items-center justify-center">
                      <Globe className="w-5 h-5 text-noc-primary" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-noc-text">Zabbix Integration</h4>
                      <p className="text-xs text-noc-text-muted">Connect to Zabbix for additional monitoring data</p>
                    </div>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" className="rounded" />
                    <span className="text-xs text-noc-text-muted">Enabled</span>
                  </label>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Zabbix URL</label>
                    <input type="url" placeholder="https://zabbix.example.com" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text placeholder-noc-text-muted/50 focus:outline-none focus:border-noc-primary" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-noc-text-muted mb-1.5">API Token</label>
                    <input type="password" placeholder="••••••••••••••••" className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text placeholder-noc-text-muted/50 focus:outline-none focus:border-noc-primary" />
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-3">
                  <button className="px-3 py-1.5 text-xs text-noc-primary bg-noc-primary/10 rounded-lg hover:bg-noc-primary/20 transition-colors">
                    Test Connection
                  </button>
                  <button className="px-3 py-1.5 text-xs text-noc-text-muted bg-noc-surface-2 rounded-lg hover:bg-noc-border transition-colors">
                    Sync Hosts
                  </button>
                </div>
              </div>

              {/* Aruba Central */}
              <div className="border border-noc-border rounded-lg p-4 opacity-60">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-noc-surface-2 flex items-center justify-center">
                      <Wifi className="w-5 h-5 text-noc-text-muted" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-noc-text">Aruba Central</h4>
                      <p className="text-xs text-noc-text-muted">Cloud management for Aruba devices</p>
                    </div>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted">Coming Soon</span>
                </div>
              </div>

              {/* Syslog */}
              <div className="border border-noc-border rounded-lg p-4 opacity-60">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-noc-surface-2 flex items-center justify-center">
                      <Database className="w-5 h-5 text-noc-text-muted" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-noc-text">Syslog Receiver</h4>
                      <p className="text-xs text-noc-text-muted">Collect syslog messages from network devices</p>
                    </div>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted">Coming Soon</span>
                </div>
              </div>

              <div className="pt-4 border-t border-noc-border">
                <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">Notification Settings</h3>
              <div className="space-y-4">
                <label className="flex items-center justify-between p-3 bg-noc-bg rounded-lg cursor-pointer">
                  <div>
                    <p className="text-sm text-noc-text">Email Notifications</p>
                    <p className="text-[10px] text-noc-text-muted">Send alerts via email</p>
                  </div>
                  <input type="checkbox" defaultChecked className="rounded" />
                </label>
                <label className="flex items-center justify-between p-3 bg-noc-bg rounded-lg cursor-pointer">
                  <div>
                    <p className="text-sm text-noc-text">Critical Alerts Only</p>
                    <p className="text-[10px] text-noc-text-muted">Only notify for critical and high severity</p>
                  </div>
                  <input type="checkbox" className="rounded" />
                </label>
                <label className="flex items-center justify-between p-3 bg-noc-bg rounded-lg cursor-pointer">
                  <div>
                    <p className="text-sm text-noc-text">Daily Summary</p>
                    <p className="text-[10px] text-noc-text-muted">Send daily network health summary</p>
                  </div>
                  <input type="checkbox" defaultChecked className="rounded" />
                </label>
              </div>
              <div className="pt-4 border-t border-noc-border">
                <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h3 className="text-sm font-semibold text-noc-text">Security Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Session Timeout (minutes)</label>
                  <input type="number" defaultValue={30} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Max Login Attempts</label>
                  <input type="number" defaultValue={5} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
              </div>
              <div className="space-y-3 pt-4 border-t border-noc-border">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <div>
                    <p className="text-sm text-noc-text">Enable Audit Logging</p>
                    <p className="text-[10px] text-noc-text-muted">Log all user actions for compliance</p>
                  </div>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <div>
                    <p className="text-sm text-noc-text">Encrypt Credentials at Rest</p>
                    <p className="text-[10px] text-noc-text-muted">All device credentials encrypted in database</p>
                  </div>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" className="rounded" />
                  <div>
                    <p className="text-sm text-noc-text">Enable 2FA</p>
                    <p className="text-[10px] text-noc-text-muted">Two-factor authentication for all users</p>
                  </div>
                </label>
              </div>
              <div className="pt-4 border-t border-noc-border">
                <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
