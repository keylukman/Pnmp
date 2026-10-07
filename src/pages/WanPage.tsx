import { useMemo } from 'react';
import { useDeviceStore } from '../stores/devices';
import { Globe, ArrowDownRight, ArrowUpRight, Activity, Clock, Signal, CheckCircle, XCircle, TrendingUp } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

export default function WanPage() {
  const { devices, interfaces } = useDeviceStore();

  const wanLinks = useMemo(() => {
    return [
      {
        id: '1',
        ispName: 'ISP 1 - Telkomsel',
        device: devices.find(d => d.id === '6') || devices[0],
        interface: interfaces.find(i => i.id === '6') || interfaces[0],
        bandwidth: 400,
        latency: 5.2,
        packetLoss: 0.01,
        availability: 99.92,
        slaTarget: 99.5,
        slaLatency: 20,
        slaPacketLoss: 0.1,
      },
      {
        id: '2',
        ispName: 'ISP 2 - Biznet',
        device: devices.find(d => d.id === '7') || devices[0],
        interface: interfaces.find(i => i.id === '7') || interfaces[0],
        bandwidth: 400,
        latency: 3.8,
        packetLoss: 0.005,
        availability: 99.97,
        slaTarget: 99.5,
        slaLatency: 15,
        slaPacketLoss: 0.05,
      },
      {
        id: '3',
        ispName: 'ISP 3 - Indosat (Backup)',
        device: devices.find(d => d.id === '8') || devices[0],
        interface: interfaces.find(i => i.id === '13') || interfaces[0],
        bandwidth: 200,
        latency: 8.5,
        packetLoss: 0.02,
        availability: 99.85,
        slaTarget: 99.0,
        slaLatency: 30,
        slaPacketLoss: 0.5,
      },
    ];
  }, [devices, interfaces]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1000;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getAvailabilityColor = (avail: number, target: number) => {
    if (avail >= target) return 'text-noc-success';
    if (avail >= target - 0.5) return 'text-noc-warning';
    return 'text-noc-danger';
  };

  const getSLAStatus = (avail: number, target: number) => {
    if (avail >= target) return { text: 'PASS', color: 'bg-noc-success/10 text-noc-success border-noc-success/20' };
    return { text: 'FAIL', color: 'bg-noc-danger/10 text-noc-danger border-noc-danger/20' };
  };

  // Traffic chart
  const trafficOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 11 } },
    legend: { data: ['ISP 1', 'ISP 2', 'ISP 3'], textStyle: { color: '#8892a4', fontSize: 10 }, top: 0 },
    grid: { left: 50, right: 20, top: 30, bottom: 25 },
    xAxis: { type: 'category' as const, data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 9 } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 9, formatter: '{value} Mbps' } },
    series: [
      { name: 'ISP 1', type: 'line', smooth: true, data: [280, 220, 350, 380, 340, 290, 320], lineStyle: { color: '#0ea5e9', width: 2 }, itemStyle: { color: '#0ea5e9' }, symbol: 'none' },
      { name: 'ISP 2', type: 'line', smooth: true, data: [200, 180, 300, 320, 280, 240, 270], lineStyle: { color: '#22c55e', width: 2 }, itemStyle: { color: '#22c55e' }, symbol: 'none' },
      { name: 'ISP 3', type: 'line', smooth: true, data: [50, 40, 80, 120, 100, 70, 90], lineStyle: { color: '#f59e0b', width: 2 }, itemStyle: { color: '#f59e0b' }, symbol: 'none' },
    ],
  };

  // Latency chart
  const latencyOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 11 } },
    legend: { data: ['ISP 1', 'ISP 2', 'ISP 3'], textStyle: { color: '#8892a4', fontSize: 10 }, top: 0 },
    grid: { left: 50, right: 20, top: 30, bottom: 25 },
    xAxis: { type: 'category' as const, data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 9 } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 9, formatter: '{value} ms' } },
    series: [
      { name: 'ISP 1', type: 'line', smooth: true, data: [4.8, 4.2, 5.5, 6.1, 5.8, 5.0, 5.2], lineStyle: { color: '#0ea5e9', width: 2 }, itemStyle: { color: '#0ea5e9' }, symbol: 'circle', symbolSize: 4 },
      { name: 'ISP 2', type: 'line', smooth: true, data: [3.2, 3.0, 4.1, 4.5, 4.2, 3.6, 3.8], lineStyle: { color: '#22c55e', width: 2 }, itemStyle: { color: '#22c55e' }, symbol: 'circle', symbolSize: 4 },
      { name: 'ISP 3', type: 'line', smooth: true, data: [7.5, 7.0, 9.2, 10.1, 9.5, 8.2, 8.5], lineStyle: { color: '#f59e0b', width: 2 }, itemStyle: { color: '#f59e0b' }, symbol: 'circle', symbolSize: 4 },
    ],
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">WAN Monitoring</h1>
          <p className="text-sm text-noc-text-muted">ISP link status, performance, and SLA compliance</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-noc-text-muted">
          <Signal className="w-3.5 h-3.5 text-noc-success" />
          <span>All links operational</span>
        </div>
      </div>

      {/* WAN Link cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {wanLinks.map((link) => {
          const sla = getSLAStatus(link.availability, link.slaTarget);
          return (
            <div key={link.id} className="bg-noc-surface border border-noc-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-noc-primary" />
                  <h3 className="text-sm font-semibold text-noc-text">{link.ispName}</h3>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold border ${sla.color}`}>
                  SLA: {sla.text}
                </span>
              </div>

              <div className="space-y-3">
                {/* Device info */}
                <div className="flex items-center gap-2 p-2 bg-noc-bg rounded-md">
                  <div className="w-2 h-2 rounded-full bg-noc-success" />
                  <div className="flex-1">
                    <p className="text-xs font-medium text-noc-text">{link.device.displayName}</p>
                    <p className="text-[10px] text-noc-text-muted">{link.interface.name} • {link.interface.description}</p>
                  </div>
                </div>

                {/* Metrics grid */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 bg-noc-bg rounded-md">
                    <p className="text-[10px] text-noc-text-muted">Bandwidth</p>
                    <p className="text-sm font-bold text-noc-text">{link.bandwidth} <span className="text-[10px] text-noc-text-muted">Mbps</span></p>
                  </div>
                  <div className="p-2 bg-noc-bg rounded-md">
                    <p className="text-[10px] text-noc-text-muted">Utilization</p>
                    <p className="text-sm font-bold text-noc-text">{link.interface.utilization}%</p>
                  </div>
                  <div className="p-2 bg-noc-bg rounded-md">
                    <p className="text-[10px] text-noc-text-muted">Latency</p>
                    <p className="text-sm font-bold text-noc-text">{link.latency} <span className="text-[10px] text-noc-text-muted">ms</span></p>
                  </div>
                  <div className="p-2 bg-noc-bg rounded-md">
                    <p className="text-[10px] text-noc-text-muted">Packet Loss</p>
                    <p className="text-sm font-bold text-noc-text">{link.packetLoss}%</p>
                  </div>
                </div>

                {/* Traffic */}
                <div className="flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1">
                    <ArrowDownRight className="w-3 h-3 text-noc-primary" />
                    <span className="text-noc-text-muted">RX:</span>
                    <span className="text-noc-text font-medium">{formatBytes(link.interface.rxBytes)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <ArrowUpRight className="w-3 h-3 text-noc-success" />
                    <span className="text-noc-text-muted">TX:</span>
                    <span className="text-noc-text font-medium">{formatBytes(link.interface.txBytes)}</span>
                  </div>
                </div>

                {/* SLA */}
                <div className="pt-2 border-t border-noc-border">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-noc-text-muted">Availability</span>
                    <span className={`text-xs font-bold ${getAvailabilityColor(link.availability, link.slaTarget)}`}>
                      {link.availability}% / {link.slaTarget}%
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-noc-bg rounded-full mt-1.5 overflow-hidden">
                    <div className={`h-full rounded-full ${link.availability >= link.slaTarget ? 'bg-noc-success' : 'bg-noc-danger'}`} style={{ width: `${Math.min(link.availability, 100)}%` }} />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-3">Aggregate WAN Traffic</h3>
          <ReactECharts option={trafficOption} style={{ height: '200px' }} />
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-3">Latency (ms)</h3>
          <ReactECharts option={latencyOption} style={{ height: '200px' }} />
        </div>
      </div>

      {/* SLA Summary Table */}
      <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-noc-text mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-noc-primary" />
          SLA Compliance Summary
        </h3>
        <div className="overflow-x-auto">
          <table className="noc-table">
            <thead>
              <tr>
                <th>ISP Provider</th>
                <th>Bandwidth</th>
                <th>Availability</th>
                <th>SLA Target</th>
                <th>Latency</th>
                <th>Packet Loss</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {wanLinks.map((link) => {
                const sla = getSLAStatus(link.availability, link.slaTarget);
                return (
                  <tr key={link.id}>
                    <td className="text-xs font-medium text-noc-text">{link.ispName}</td>
                    <td className="text-xs text-noc-text-muted">{link.bandwidth} Mbps</td>
                    <td className={`text-xs font-bold ${getAvailabilityColor(link.availability, link.slaTarget)}`}>{link.availability}%</td>
                    <td className="text-xs text-noc-text-muted">{link.slaTarget}%</td>
                    <td className="text-xs text-noc-text">{link.latency} ms</td>
                    <td className="text-xs text-noc-text">{link.packetLoss}%</td>
                    <td>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold border ${sla.color}`}>
                        {sla.text}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
