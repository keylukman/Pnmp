import { useMemo } from 'react';
import { useDeviceStore } from '../stores/devices';
import { Server, AlertTriangle, CheckCircle, XCircle, Clock, Activity, ArrowUpRight, ArrowDownRight, Wifi } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

export default function DashboardPage() {
  const { devices, alerts, interfaces, events } = useDeviceStore();

  const stats = useMemo(() => ({
    total: devices.length,
    up: devices.filter((d) => d.status === 'up').length,
    down: devices.filter((d) => d.status === 'down').length,
    warning: devices.filter((d) => d.status === 'warning').length,
    maintenance: devices.filter((d) => d.status === 'maintenance').length,
    unknown: devices.filter((d) => d.status === 'unknown').length,
  }), [devices]);

  const openAlerts = useMemo(() => alerts.filter((a) => a.status === 'open'), [alerts]);

  const deviceTypeDistribution = useMemo(() => {
    const types: Record<string, number> = {};
    devices.forEach((d) => {
      types[d.deviceType] = (types[d.deviceType] || 0) + 1;
    });
    return Object.entries(types).map(([name, value]) => ({ name, value }));
  }, [devices]);

  const availability = useMemo(() => {
    const up = devices.filter((d) => d.status === 'up').length;
    return ((up / devices.length) * 100).toFixed(1);
  }, [devices]);

  // Chart options
  const donutOption = {
    tooltip: { trigger: 'item' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['55%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#1a1f2e', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 12, color: '#e2e8f0' } },
      data: deviceTypeDistribution,
      color: ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'],
    }],
  };

  const trafficOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 10, formatter: '{value} Mbps' } },
    series: [
      { name: 'Inbound', type: 'line', smooth: true, data: [420, 380, 650, 890, 780, 620, 750], lineStyle: { color: '#0ea5e9', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(14,165,233,0.3)' }, { offset: 1, color: 'rgba(14,165,233,0)' }] } }, itemStyle: { color: '#0ea5e9' }, symbol: 'none' },
      { name: 'Outbound', type: 'line', smooth: true, data: [280, 250, 450, 620, 540, 430, 520], lineStyle: { color: '#22c55e', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(34,197,94,0.2)' }, { offset: 1, color: 'rgba(34,197,94,0)' }] } }, itemStyle: { color: '#22c55e' }, symbol: 'none' },
    ],
  };

  const cpuMemoryOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: devices.filter(d => d.status === 'up').slice(0, 8).map(d => d.displayName.substring(0, 12)), axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 9, rotate: 30 } },
    yAxis: { type: 'value' as const, max: 100, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 10, formatter: '{value}%' } },
    series: [
      { name: 'CPU', type: 'bar', data: devices.filter(d => d.status === 'up').slice(0, 8).map(d => d.cpu), itemStyle: { color: '#0ea5e9', borderRadius: [3, 3, 0, 0] }, barWidth: '30%' },
      { name: 'Memory', type: 'bar', data: devices.filter(d => d.status === 'up').slice(0, 8).map(d => d.memory), itemStyle: { color: '#8b5cf6', borderRadius: [3, 3, 0, 0] }, barWidth: '30%' },
    ],
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up': return 'text-noc-success';
      case 'down': return 'text-noc-danger';
      case 'warning': return 'text-noc-warning';
      case 'maintenance': return 'text-noc-info';
      default: return 'text-noc-text-muted';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-noc-danger/10 text-noc-danger border-noc-danger/20';
      case 'high': return 'bg-noc-warning/10 text-noc-warning border-noc-warning/20';
      case 'warning': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'info': return 'bg-noc-info/10 text-noc-info border-noc-info/20';
      default: return 'bg-noc-surface-2 text-noc-text-muted';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">NOC Dashboard</h1>
          <p className="text-sm text-noc-text-muted">Network overview and real-time monitoring</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-noc-text-muted">
          <div className="w-2 h-2 rounded-full bg-noc-success animate-pulse"></div>
          <span>Live</span>
          <span className="ml-2">Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Server className="w-4 h-4 text-noc-text-muted" />
            <span className="text-xs text-noc-text-muted">Total</span>
          </div>
          <p className="text-2xl font-bold text-noc-text">{stats.total}</p>
        </div>

        <div className="card-gradient-up rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="w-4 h-4 text-noc-success" />
            <span className="text-xs text-noc-success">UP</span>
          </div>
          <p className="text-2xl font-bold text-noc-success">{stats.up}</p>
        </div>

        <div className="card-gradient-down rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <XCircle className="w-4 h-4 text-noc-danger" />
            <span className="text-xs text-noc-danger">DOWN</span>
          </div>
          <p className="text-2xl font-bold text-noc-danger">{stats.down}</p>
        </div>

        <div className="card-gradient-warning rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <AlertTriangle className="w-4 h-4 text-noc-warning" />
            <span className="text-xs text-noc-warning">Warning</span>
          </div>
          <p className="text-2xl font-bold text-noc-warning">{stats.warning}</p>
        </div>

        <div className="card-gradient-info rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-4 h-4 text-noc-info" />
            <span className="text-xs text-noc-info">Maint.</span>
          </div>
          <p className="text-2xl font-bold text-noc-info">{stats.maintenance}</p>
        </div>

        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Activity className="w-4 h-4 text-noc-primary" />
            <span className="text-xs text-noc-text-muted">Avail.</span>
          </div>
          <p className="text-2xl font-bold text-noc-primary">{availability}%</p>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Traffic chart */}
        <div className="lg:col-span-2 bg-noc-surface border border-noc-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-noc-text">Network Traffic</h3>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-noc-primary"></span> Inbound</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-noc-success"></span> Outbound</span>
            </div>
          </div>
          <ReactECharts option={trafficOption} style={{ height: '200px' }} />
        </div>

        {/* Device distribution */}
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-4">Device Distribution</h3>
          <ReactECharts option={donutOption} style={{ height: '200px' }} />
        </div>
      </div>

      {/* Performance + Alerts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* CPU/Memory */}
        <div className="lg:col-span-2 bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-4">Device Performance (CPU / Memory)</h3>
          <ReactECharts option={cpuMemoryOption} style={{ height: '220px' }} />
        </div>

        {/* Recent alerts */}
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-noc-text">Recent Alerts</h3>
            <span className="text-xs text-noc-danger bg-noc-danger/10 px-2 py-0.5 rounded-full">{openAlerts.length} open</span>
          </div>
          <div className="space-y-2 max-h-[220px] overflow-y-auto">
            {alerts.slice(0, 6).map((alert) => (
              <div key={alert.id} className={`p-2 rounded-lg border ${getSeverityColor(alert.severity)}`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-xs font-medium truncate">{alert.title}</p>
                    <p className="text-[10px] opacity-70 truncate">{alert.deviceName}</p>
                  </div>
                  <span className="text-[10px] opacity-60 whitespace-nowrap flex-shrink-0">
                    {new Date(alert.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top devices + Recent events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top devices by CPU */}
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-4">Top Devices by Resource Usage</h3>
          <div className="space-y-2">
            {devices
              .filter((d) => d.status === 'up')
              .sort((a, b) => (b.cpu + b.memory) - (a.cpu + a.memory))
              .slice(0, 6)
              .map((device) => (
                <div key={device.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-noc-surface-2 transition-colors">
                  <div className={`w-2 h-2 rounded-full ${device.status === 'up' ? 'bg-noc-success' : device.status === 'warning' ? 'bg-noc-warning' : 'bg-noc-danger'}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-noc-text truncate">{device.displayName}</p>
                    <p className="text-[10px] text-noc-text-muted">{device.vendor} {device.model}</p>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <div className="flex items-center gap-1">
                      <ArrowUpRight className="w-3 h-3 text-noc-primary" />
                      <span className={device.cpu > 60 ? 'text-noc-warning' : 'text-noc-text-muted'}>{device.cpu}%</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <ArrowDownRight className="w-3 h-3 text-noc-info" />
                      <span className={device.memory > 70 ? 'text-noc-warning' : 'text-noc-text-muted'}>{device.memory}%</span>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Recent events */}
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-4">Recent Events</h3>
          <div className="space-y-2 max-h-[280px] overflow-y-auto">
            {events.slice(0, 8).map((event) => (
              <div key={event.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-noc-surface-2 transition-colors">
                <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                  event.severity === 'critical' ? 'bg-noc-danger' :
                  event.severity === 'high' ? 'bg-noc-warning' :
                  event.severity === 'warning' ? 'bg-yellow-500' : 'bg-noc-info'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-noc-text">{event.message}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] text-noc-text-muted">{event.deviceName}</span>
                    <span className="text-[10px] text-noc-text-muted">•</span>
                    <span className="text-[10px] text-noc-text-muted">{event.category}</span>
                  </div>
                </div>
                <span className="text-[10px] text-noc-text-muted whitespace-nowrap flex-shrink-0">
                  {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Interface summary */}
      <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-noc-text">Interface Overview</h3>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1"><Wifi className="w-3 h-3 text-noc-success" /> {interfaces.filter(i => i.status === 'up').length} UP</span>
            <span className="flex items-center gap-1"><Wifi className="w-3 h-3 text-noc-danger" /> {interfaces.filter(i => i.status === 'down').length} DOWN</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="noc-table">
            <thead>
              <tr>
                <th>Interface</th>
                <th>Device</th>
                <th>Status</th>
                <th>Speed</th>
                <th>Utilization</th>
                <th>Errors</th>
              </tr>
            </thead>
            <tbody>
              {interfaces.slice(0, 8).map((iface) => (
                <tr key={iface.id}>
                  <td className="font-mono text-xs">{iface.name}</td>
                  <td className="text-xs">{iface.deviceName}</td>
                  <td>
                    <span className={`inline-flex items-center gap-1 text-xs ${getStatusColor(iface.status)}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${iface.status === 'up' ? 'bg-noc-success' : 'bg-noc-danger'}`} />
                      {iface.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="text-xs text-noc-text-muted">{iface.speed}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-noc-bg rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${iface.utilization > 80 ? 'bg-noc-danger' : iface.utilization > 60 ? 'bg-noc-warning' : 'bg-noc-success'}`}
                          style={{ width: `${iface.utilization}%` }}
                        />
                      </div>
                      <span className="text-xs text-noc-text-muted">{iface.utilization}%</span>
                    </div>
                  </td>
                  <td className="text-xs">
                    <span className={iface.rxErrors + iface.txErrors > 0 ? 'text-noc-warning' : 'text-noc-text-muted'}>
                      {iface.rxErrors + iface.txErrors}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
