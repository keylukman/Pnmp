import { useState, useMemo } from 'react';
import { useDeviceStore } from '../stores/devices';
import { AlertTriangle, CheckCircle, XCircle, Clock, Filter, Bell, BellOff } from 'lucide-react';

export default function AlertsPage() {
  const { alerts, acknowledgeAlert } = useDeviceStore();
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      const matchSeverity = severityFilter === 'all' || a.severity === severityFilter;
      const matchStatus = statusFilter === 'all' || a.status === statusFilter;
      return matchSeverity && matchStatus;
    }).sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [alerts, severityFilter, statusFilter]);

  const counts = useMemo(() => ({
    critical: alerts.filter(a => a.severity === 'critical' && a.status === 'open').length,
    high: alerts.filter(a => a.severity === 'high' && a.status === 'open').length,
    warning: alerts.filter(a => a.severity === 'warning' && a.status === 'open').length,
    info: alerts.filter(a => a.severity === 'info' && a.status === 'open').length,
  }), [alerts]);

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-noc-danger/10 text-noc-danger border-noc-danger/20';
      case 'high': return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
      case 'warning': return 'bg-noc-warning/10 text-noc-warning border-noc-warning/20';
      case 'info': return 'bg-noc-info/10 text-noc-info border-noc-info/20';
      default: return 'bg-noc-surface-2 text-noc-text-muted';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open': return 'bg-noc-danger/10 text-noc-danger';
      case 'acknowledged': return 'bg-noc-warning/10 text-noc-warning';
      case 'resolved': return 'bg-noc-success/10 text-noc-success';
      default: return 'text-noc-text-muted';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Alerts</h1>
          <p className="text-sm text-noc-text-muted">{alerts.filter(a => a.status === 'open').length} active alerts</p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-noc-surface border border-noc-danger/20 rounded-lg p-3 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-noc-danger/10 flex items-center justify-center">
            <XCircle className="w-5 h-5 text-noc-danger" />
          </div>
          <div>
            <p className="text-xl font-bold text-noc-danger">{counts.critical}</p>
            <p className="text-xs text-noc-text-muted">Critical</p>
          </div>
        </div>
        <div className="bg-noc-surface border border-orange-500/20 rounded-lg p-3 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
          </div>
          <div>
            <p className="text-xl font-bold text-orange-500">{counts.high}</p>
            <p className="text-xs text-noc-text-muted">High</p>
          </div>
        </div>
        <div className="bg-noc-surface border border-noc-warning/20 rounded-lg p-3 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-noc-warning/10 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-noc-warning" />
          </div>
          <div>
            <p className="text-xl font-bold text-noc-warning">{counts.warning}</p>
            <p className="text-xs text-noc-text-muted">Warning</p>
          </div>
        </div>
        <div className="bg-noc-surface border border-noc-info/20 rounded-lg p-3 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-noc-info/10 flex items-center justify-center">
            <Bell className="w-5 h-5 text-noc-info" />
          </div>
          <div>
            <p className="text-xl font-bold text-noc-info">{counts.info}</p>
            <p className="text-xs text-noc-text-muted">Info</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-noc-surface border border-noc-border rounded-lg p-3">
        <Filter className="w-4 h-4 text-noc-text-muted" />
        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
          <option value="all">All Status</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      {/* Alert list */}
      <div className="space-y-2">
        {filteredAlerts.map((alert) => (
          <div key={alert.id} className="bg-noc-surface border border-noc-border rounded-lg p-4 hover:bg-noc-surface-2 transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 flex-1">
                <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getSeverityBadge(alert.severity)}`}>
                  {alert.severity}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-noc-text">{alert.title}</h4>
                  <p className="text-xs text-noc-text-muted mt-0.5">{alert.description}</p>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="text-xs text-noc-text-muted">Device: <span className="text-noc-text">{alert.deviceName}</span></span>
                    <span className="text-xs text-noc-text-muted">Source: {alert.source}</span>
                    <span className="text-xs text-noc-text-muted">{new Date(alert.createdAt).toLocaleString()}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${getStatusBadge(alert.status)}`}>
                  {alert.status}
                </span>
                {alert.status === 'open' && (
                  <button onClick={() => acknowledgeAlert(alert.id)} className="p-1.5 rounded hover:bg-noc-surface text-noc-text-muted hover:text-noc-primary transition-colors" title="Acknowledge">
                    <BellOff className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        {filteredAlerts.length === 0 && (
          <div className="bg-noc-surface border border-noc-border rounded-lg p-8 text-center">
            <CheckCircle className="w-8 h-8 text-noc-success mx-auto mb-2" />
            <p className="text-sm text-noc-text-muted">No alerts matching your filters.</p>
          </div>
        )}
      </div>
    </div>
  );
}
