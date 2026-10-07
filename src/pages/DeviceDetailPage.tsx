import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDeviceStore } from '../stores/devices';
import ReactECharts from 'echarts-for-react';
import {
  ArrowLeft, Server, CheckCircle, XCircle, AlertTriangle, Clock,
  Cpu, HardDrive, Thermometer, Clock as ClockIcon, Network,
  Radio, ArrowUpRight, ArrowDownRight, Activity, Shield,
  MapPin, Globe, Wifi, Settings, RefreshCw, MoreVertical
} from 'lucide-react';

export default function DeviceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { devices, interfaces, events, topologyLinks } = useDeviceStore();
  const [activeTab, setActiveTab] = useState('overview');

  const device = useMemo(() => devices.find(d => d.id === id), [devices, id]);
  const deviceInterfaces = useMemo(() => interfaces.filter(i => i.deviceId === id), [interfaces, id]);
  const deviceEvents = useMemo(() => events.filter(e => e.deviceId === id).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()), [events, id]);
  const connectedDevices = useMemo(() => {
    if (!id) return [];
    const links = topologyLinks.filter(l => l.sourceDeviceId === id || l.targetDeviceId === id);
    return links.map(link => {
      const otherDeviceId = link.sourceDeviceId === id ? link.targetDeviceId : link.sourceDeviceId;
      const otherDevice = devices.find(d => d.id === otherDeviceId);
      return { link, device: otherDevice };
    });
  }, [topologyLinks, devices, id]);

  if (!device) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Server className="w-12 h-12 text-noc-text-muted mx-auto mb-3" />
          <p className="text-noc-text-muted">Device not found</p>
          <button onClick={() => navigate('/devices')} className="mt-3 text-noc-primary text-sm hover:underline">
            Back to Devices
          </button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up': return 'text-noc-success';
      case 'down': return 'text-noc-danger';
      case 'warning': return 'text-noc-warning';
      case 'maintenance': return 'text-noc-info';
      default: return 'text-noc-text-muted';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'up': return 'bg-noc-success/10 border-noc-success/20 text-noc-success';
      case 'down': return 'bg-noc-danger/10 border-noc-danger/20 text-noc-danger';
      case 'warning': return 'bg-noc-warning/10 border-noc-warning/20 text-noc-warning';
      case 'maintenance': return 'bg-noc-info/10 border-noc-info/20 text-noc-info';
      default: return 'bg-noc-surface-2 text-noc-text-muted';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up': return <CheckCircle className="w-4 h-4" />;
      case 'down': return <XCircle className="w-4 h-4" />;
      case 'warning': return <AlertTriangle className="w-4 h-4" />;
      case 'maintenance': return <Clock className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1000;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  // CPU gauge chart
  const cpuGaugeOption = {
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: 100,
      splitNumber: 10,
      radius: '90%',
      itemStyle: { color: device.cpu > 80 ? '#ef4444' : device.cpu > 60 ? '#f59e0b' : '#0ea5e9' },
      progress: { show: true, width: 12, roundCap: true },
      pointer: { show: false },
      axisLine: { lineStyle: { width: 12, color: [[1, '#1e2535']] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      title: { show: true, offsetCenter: [0, '30%'], fontSize: 11, color: '#8892a4' },
      detail: { valueAnimation: true, fontSize: 24, fontWeight: 'bold', offsetCenter: [0, '-5%'], formatter: '{value}%', color: '#e2e8f0' },
      data: [{ value: device.cpu, name: 'CPU' }],
    }],
  };

  // Memory gauge chart
  const memGaugeOption = {
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: 100,
      splitNumber: 10,
      radius: '90%',
      itemStyle: { color: device.memory > 80 ? '#ef4444' : device.memory > 60 ? '#f59e0b' : '#8b5cf6' },
      progress: { show: true, width: 12, roundCap: true },
      pointer: { show: false },
      axisLine: { lineStyle: { width: 12, color: [[1, '#1e2535']] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      title: { show: true, offsetCenter: [0, '30%'], fontSize: 11, color: '#8892a4' },
      detail: { valueAnimation: true, fontSize: 24, fontWeight: 'bold', offsetCenter: [0, '-5%'], formatter: '{value}%', color: '#e2e8f0' },
      data: [{ value: device.memory, name: 'Memory' }],
    }],
  };

  // Interface traffic chart
  const trafficOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 11 } },
    legend: { data: ['RX', 'TX'], textStyle: { color: '#8892a4', fontSize: 10 }, top: 0 },
    grid: { left: 50, right: 20, top: 30, bottom: 25 },
    xAxis: { type: 'category' as const, data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 9 } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 9, formatter: '{value} Mbps' } },
    series: [
      { name: 'RX', type: 'line', smooth: true, data: [120, 95, 280, 450, 380, 290, 350], lineStyle: { color: '#0ea5e9', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(14,165,233,0.2)' }, { offset: 1, color: 'rgba(14,165,233,0)' }] } }, itemStyle: { color: '#0ea5e9' }, symbol: 'none' },
      { name: 'TX', type: 'line', smooth: true, data: [80, 65, 190, 320, 260, 200, 240], lineStyle: { color: '#22c55e', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(34,197,94,0.15)' }, { offset: 1, color: 'rgba(34,197,94,0)' }] } }, itemStyle: { color: '#22c55e' }, symbol: 'none' },
    ],
  };

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'interfaces', label: `Interfaces (${deviceInterfaces.length})` },
    { id: 'performance', label: 'Performance' },
    { id: 'events', label: `Events (${deviceEvents.length})` },
    { id: 'connections', label: `Connections (${connectedDevices.length})` },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/devices')} className="p-2 rounded-lg bg-noc-surface border border-noc-border hover:border-noc-primary/30 transition-colors">
          <ArrowLeft className="w-4 h-4 text-noc-text-muted" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-noc-text">{device.displayName}</h1>
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusBg(device.status)}`}>
              {getStatusIcon(device.status)}
              {device.status.toUpperCase()}
            </span>
          </div>
          <p className="text-sm text-noc-text-muted">{device.hostname} • {device.managementIp} • {device.vendor} {device.model}</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 rounded-lg bg-noc-surface border border-noc-border hover:border-noc-primary/30 transition-colors" title="Test Connection">
            <RefreshCw className="w-4 h-4 text-noc-text-muted" />
          </button>
          <button className="p-2 rounded-lg bg-noc-surface border border-noc-border hover:border-noc-primary/30 transition-colors" title="Settings">
            <Settings className="w-4 h-4 text-noc-text-muted" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-noc-surface border border-noc-border rounded-lg p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id ? 'bg-noc-primary/10 text-noc-primary' : 'text-noc-text-muted hover:text-noc-text hover:bg-noc-surface-2'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Device Info */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-noc-text mb-3 flex items-center gap-2">
                <Server className="w-4 h-4 text-noc-primary" />
                Device Information
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <InfoItem label="Hostname" value={device.hostname} />
                <InfoItem label="Management IP" value={device.managementIp} />
                <InfoItem label="Vendor" value={device.vendor} />
                <InfoItem label="Model" value={device.model} />
                <InfoItem label="Serial Number" value={device.serialNumber} />
                <InfoItem label="Firmware" value={device.firmwareVersion} />
                <InfoItem label="MAC Address" value={device.macAddress} />
                <InfoItem label="Device Type" value={device.deviceType} />
                <InfoItem label="Device Role" value={device.deviceRole.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} />
                <InfoItem label="Site" value={device.siteName} />
                <InfoItem label="Location" value={device.location} />
                <InfoItem label="Uptime" value={device.uptime} />
              </div>
            </div>

            {/* Performance Gauges */}
            <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-noc-text mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-noc-primary" />
                Performance Metrics
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="h-36">
                  <ReactECharts option={cpuGaugeOption} style={{ height: '100%' }} />
                </div>
                <div className="h-36">
                  <ReactECharts option={memGaugeOption} style={{ height: '100%' }} />
                </div>
                <div className="flex flex-col items-center justify-center p-3 bg-noc-bg rounded-lg">
                  <Thermometer className="w-5 h-5 text-noc-warning mb-2" />
                  <span className="text-2xl font-bold text-noc-text">{device.temperature}°C</span>
                  <span className="text-xs text-noc-text-muted mt-1">Temperature</span>
                </div>
                <div className="flex flex-col items-center justify-center p-3 bg-noc-bg rounded-lg">
                  <ClockIcon className="w-5 h-5 text-noc-info mb-2" />
                  <span className="text-lg font-bold text-noc-text">{device.uptime}</span>
                  <span className="text-xs text-noc-text-muted mt-1">Uptime</span>
                </div>
              </div>
            </div>

            {/* Traffic Chart */}
            <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-noc-text mb-3 flex items-center gap-2">
                <ArrowUpRight className="w-4 h-4 text-noc-primary" />
                Aggregate Traffic (24h)
              </h3>
              <div className="h-48">
                <ReactECharts option={trafficOption} style={{ height: '100%' }} />
              </div>
            </div>
          </div>

          {/* Sidebar Info */}
          <div className="space-y-4">
            {/* Quick Stats */}
            <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-noc-text mb-3">Quick Stats</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Interfaces</span>
                  <span className="text-sm font-medium text-noc-text">{deviceInterfaces.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Interfaces UP</span>
                  <span className="text-sm font-medium text-noc-success">{deviceInterfaces.filter(i => i.status === 'up').length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Interfaces DOWN</span>
                  <span className="text-sm font-medium text-noc-danger">{deviceInterfaces.filter(i => i.status === 'down').length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Total RX</span>
                  <span className="text-sm font-medium text-noc-text">{formatBytes(deviceInterfaces.reduce((sum, i) => sum + i.rxBytes, 0))}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Total TX</span>
                  <span className="text-sm font-medium text-noc-text">{formatBytes(deviceInterfaces.reduce((sum, i) => sum + i.txBytes, 0))}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Errors</span>
                  <span className="text-sm font-medium text-noc-warning">{deviceInterfaces.reduce((sum, i) => sum + i.rxErrors + i.txErrors, 0)}</span>
                </div>
              </div>
            </div>

            {/* Monitoring Status */}
            <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-noc-text mb-3">Monitoring</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Status</span>
                  <span className={`text-xs font-medium ${device.monitoringEnabled ? 'text-noc-success' : 'text-noc-text-muted'}`}>
                    {device.monitoringEnabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Last Seen</span>
                  <span className="text-xs text-noc-text-muted">{new Date(device.lastSeen).toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-noc-text-muted">Created</span>
                  <span className="text-xs text-noc-text-muted">{new Date(device.createdAt).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* Connected Devices */}
            <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-noc-text mb-3">Connected Devices</h3>
              <div className="space-y-2">
                {connectedDevices.length > 0 ? connectedDevices.map(({ link, device: connDevice }) => (
                  connDevice && (
                    <div key={link.id} className="flex items-center gap-2 p-2 bg-noc-bg rounded-md">
                      <div className={`w-2 h-2 rounded-full ${connDevice.status === 'up' ? 'bg-noc-success' : connDevice.status === 'down' ? 'bg-noc-danger' : 'bg-noc-warning'}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-noc-text truncate">{connDevice.displayName}</p>
                        <p className="text-[10px] text-noc-text-muted">{link.sourceInterface} → {link.targetInterface}</p>
                      </div>
                      <span className={`text-[10px] ${link.status === 'up' ? 'text-noc-success' : 'text-noc-danger'}`}>
                        {link.linkType.toUpperCase()}
                      </span>
                    </div>
                  )
                )) : (
                  <p className="text-xs text-noc-text-muted">No connections detected</p>
                )}
              </div>
            </div>

            {/* Description */}
            <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-noc-text mb-2">Description</h3>
              <p className="text-xs text-noc-text-muted">{device.description}</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'interfaces' && (
        <div className="bg-noc-surface border border-noc-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-noc-border bg-noc-surface-2/50">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-noc-text-muted uppercase tracking-wider">Interface</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-noc-text-muted uppercase tracking-wider">Description</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-noc-text-muted uppercase tracking-wider">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-noc-text-muted uppercase tracking-wider">Speed</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-noc-text-muted uppercase tracking-wider">RX</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-noc-text-muted uppercase tracking-wider">TX</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-noc-text-muted uppercase tracking-wider">Errors</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-noc-text-muted uppercase tracking-wider">Utilization</th>
                </tr>
              </thead>
              <tbody>
                {deviceInterfaces.map((iface) => (
                  <tr key={iface.id} className="border-b border-noc-border/50 hover:bg-noc-surface-2/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-noc-text">{iface.name}</td>
                    <td className="px-4 py-3 text-xs text-noc-text-muted">{iface.description}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium ${
                        iface.status === 'up' ? 'bg-noc-success/10 text-noc-success' : 'bg-noc-danger/10 text-noc-danger'
                      }`}>
                        {iface.status === 'up' ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        {iface.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-noc-text">{iface.speed}</td>
                    <td className="px-4 py-3 text-right text-xs text-noc-text font-mono">{formatBytes(iface.rxBytes)}</td>
                    <td className="px-4 py-3 text-right text-xs text-noc-text font-mono">{formatBytes(iface.txBytes)}</td>
                    <td className="px-4 py-3 text-right text-xs">
                      <span className={iface.rxErrors + iface.txErrors > 0 ? 'text-noc-warning' : 'text-noc-text-muted'}>
                        {iface.rxErrors + iface.txErrors}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1.5 bg-noc-bg rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${iface.utilization > 80 ? 'bg-noc-danger' : iface.utilization > 60 ? 'bg-noc-warning' : 'bg-noc-success'}`} style={{ width: `${iface.utilization}%` }} />
                        </div>
                        <span className={`text-xs font-mono ${iface.utilization > 80 ? 'text-noc-danger' : iface.utilization > 60 ? 'text-noc-warning' : 'text-noc-text'}`}>
                          {iface.utilization}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {deviceInterfaces.length === 0 && (
            <div className="p-8 text-center text-noc-text-muted text-sm">No interfaces data available</div>
          )}
        </div>
      )}

      {activeTab === 'performance' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
            <h3 className="text-sm font-semibold text-noc-text mb-3">CPU Utilization</h3>
            <div className="h-48 flex items-center justify-center">
              <ReactECharts option={cpuGaugeOption} style={{ height: '100%', width: '100%' }} />
            </div>
            <div className="mt-2 text-center">
              <span className={`text-sm font-medium ${device.cpu > 80 ? 'text-noc-danger' : device.cpu > 60 ? 'text-noc-warning' : 'text-noc-success'}`}>
                {device.cpu > 80 ? 'Critical' : device.cpu > 60 ? 'Warning' : 'Normal'}
              </span>
            </div>
          </div>
          <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
            <h3 className="text-sm font-semibold text-noc-text mb-3">Memory Utilization</h3>
            <div className="h-48 flex items-center justify-center">
              <ReactECharts option={memGaugeOption} style={{ height: '100%', width: '100%' }} />
            </div>
            <div className="mt-2 text-center">
              <span className={`text-sm font-medium ${device.memory > 80 ? 'text-noc-danger' : device.memory > 60 ? 'text-noc-warning' : 'text-noc-success'}`}>
                {device.memory > 80 ? 'Critical' : device.memory > 60 ? 'Warning' : 'Normal'}
              </span>
            </div>
          </div>
          <div className="lg:col-span-2 bg-noc-surface border border-noc-border rounded-lg p-4">
            <h3 className="text-sm font-semibold text-noc-text mb-3">Traffic History (24h)</h3>
            <div className="h-56">
              <ReactECharts option={trafficOption} style={{ height: '100%' }} />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'events' && (
        <div className="bg-noc-surface border border-noc-border rounded-lg">
          <div className="divide-y divide-noc-border/50">
            {deviceEvents.length > 0 ? deviceEvents.map((event) => (
              <div key={event.id} className="px-4 py-3 flex items-start gap-3 hover:bg-noc-surface-2/30 transition-colors">
                <div className={`mt-0.5 p-1 rounded ${
                  event.severity === 'critical' ? 'bg-noc-danger/10' :
                  event.severity === 'high' ? 'bg-orange-500/10' :
                  event.severity === 'warning' ? 'bg-noc-warning/10' : 'bg-noc-info/10'
                }`}>
                  {event.severity === 'critical' ? <XCircle className="w-3.5 h-3.5 text-noc-danger" /> :
                   event.severity === 'high' ? <AlertTriangle className="w-3.5 h-3.5 text-orange-500" /> :
                   event.severity === 'warning' ? <AlertTriangle className="w-3.5 h-3.5 text-noc-warning" /> :
                   <Activity className="w-3.5 h-3.5 text-noc-info" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-noc-text">{event.message}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-[10px] text-noc-text-muted">{new Date(event.timestamp).toLocaleString()}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted">{event.category}</span>
                    <span className="text-[10px] text-noc-text-muted">via {event.source}</span>
                  </div>
                </div>
              </div>
            )) : (
              <div className="p-8 text-center text-noc-text-muted text-sm">No events recorded</div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'connections' && (
        <div className="space-y-3">
          {connectedDevices.length > 0 ? connectedDevices.map(({ link, device: connDevice }) => (
            connDevice && (
              <div key={link.id} className="bg-noc-surface border border-noc-border rounded-lg p-4 hover:border-noc-primary/30 transition-colors">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    connDevice.status === 'up' ? 'bg-noc-success/10' : connDevice.status === 'down' ? 'bg-noc-danger/10' : 'bg-noc-warning/10'
                  }`}>
                    {connDevice.deviceRole === 'firewall' ? <Shield className="w-5 h-5 text-noc-text" /> :
                     connDevice.deviceRole === 'router' ? <Globe className="w-5 h-5 text-noc-text" /> :
                     connDevice.deviceRole === 'wireless_controller' ? <Radio className="w-5 h-5 text-noc-text" /> :
                     connDevice.deviceRole === 'access_point' ? <Wifi className="w-5 h-5 text-noc-text" /> :
                     <Server className="w-5 h-5 text-noc-text" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-noc-text">{connDevice.displayName}</span>
                      <span className={`w-2 h-2 rounded-full ${connDevice.status === 'up' ? 'bg-noc-success' : connDevice.status === 'down' ? 'bg-noc-danger' : 'bg-noc-warning'}`} />
                    </div>
                    <p className="text-xs text-noc-text-muted">{connDevice.vendor} {connDevice.model} • {connDevice.managementIp}</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-mono text-noc-text">{link.sourceDeviceId === id ? link.sourceInterface : link.targetInterface}</span>
                      <span className="text-noc-text-muted">↔</span>
                      <span className="font-mono text-noc-text">{link.sourceDeviceId === id ? link.targetInterface : link.sourceInterface}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted">{link.linkType.toUpperCase()}</span>
                      <span className="text-[10px] text-noc-text-muted">{link.bandwidth}</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          )) : (
            <div className="bg-noc-surface border border-noc-border rounded-lg p-8 text-center">
              <Network className="w-10 h-10 text-noc-text-muted mx-auto mb-3" />
              <p className="text-sm text-noc-text-muted">No LLDP/CDP connections detected</p>
              <p className="text-xs text-noc-text-muted mt-1">Topology links will appear here when discovered via LLDP/CDP</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-noc-text-muted mb-0.5">{label}</p>
      <p className="text-sm text-noc-text font-medium">{value}</p>
    </div>
  );
}
