import { useMemo } from 'react';
import { useDeviceStore } from '../stores/devices';
import { Globe, ArrowDownRight, ArrowUpRight, Activity, Clock, Signal } from 'lucide-react';
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
      },
      {
        id: '3',
        ispName: 'ISP 3 - Indosat (Backup)',
        device: devices.find(d => d.id === '8') || devices[0],
        interface: interfaces.find(i => i.id === '8') || interfaces[0],
        bandwidth: 200,
        latency: 12.5,
        packetLoss: 0.08,
        availability: 98.5,
        slaTarget: 99.0,
      },
    ];
  }, [devices, interfaces]);

  const latencyChartOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00', 'Now'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 10, formatter: '{value} ms' } },
    series: [
      { name: 'ISP 1', type: 'line', smooth: true, data: [5.1, 4.8, 5.5, 6.2, 7.1, 5.8, 5.2, 4.9, 5.2], lineStyle: { color: '#0ea5e9', width: 2 }, itemStyle: { color: '#0ea5e9' }, symbol: 'none' },
      { name: 'ISP 2', type: 'line', smooth: true, data: [3.5, 3.2, 3.8, 4.5, 5.2, 4.1, 3.6, 3.4, 3.8], lineStyle: { color: '#22c55e', width: 2 }, itemStyle: { color: '#22c55e' }, symbol: 'none' },
      { name: 'ISP 3', type: 'line', smooth: true, data: [11.2, 10.5, 12.8, 15.2, 18.5, 14.2, 12.1, 11.5, 12.5], lineStyle: { color: '#f59e0b', width: 2 }, itemStyle: { color: '#f59e0b' }, symbol: 'none' },
    ],
  };

  const bandwidthChartOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00', 'Now'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 10, formatter: '{value} Mbps' } },
    series: [
      { name: 'Total In', type: 'bar', stack: 'traffic', data: [120, 80, 150, 280, 350, 310, 250, 180, 270], itemStyle: { color: '#0ea5e9', borderRadius: [0, 0, 0, 0] } },
      { name: 'Total Out', type: 'bar', stack: 'traffic', data: [80, 50, 100, 200, 250, 220, 180, 120, 190], itemStyle: { color: '#22c55e', borderRadius: [3, 3, 0, 0] } },
    ],
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">WAN Monitoring</h1>
          <p className="text-sm text-noc-text-muted">ISP link monitoring and SLA tracking</p>
        </div>
      </div>

      {/* WAN Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {wanLinks.map((link) => (
          <div key={link.id} className="bg-noc-surface border border-noc-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-noc-primary" />
                <h3 className="text-sm font-semibold text-noc-text">{link.ispName}</h3>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded ${link.availability >= link.slaTarget ? 'bg-noc-success/10 text-noc-success' : 'bg-noc-danger/10 text-noc-danger'}`}>
                {link.availability >= link.slaTarget ? 'SLA PASS' : 'SLA FAIL'}
              </span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted">Device</span>
                <span className="text-noc-text">{link.device?.displayName}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted">Interface</span>
                <span className="text-noc-text font-mono">{link.interface?.name}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted">Bandwidth</span>
                <span className="text-noc-text">{link.bandwidth} Mbps</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted flex items-center gap-1"><ArrowDownRight className="w-3 h-3" /> RX</span>
                <span className="text-noc-text">{link.interface ? (link.interface.rxBytes / 1000000).toFixed(0) : 0} Mbps</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted flex items-center gap-1"><ArrowUpRight className="w-3 h-3" /> TX</span>
                <span className="text-noc-text">{link.interface ? (link.interface.txBytes / 1000000).toFixed(0) : 0} Mbps</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted">Utilization</span>
                <span className={`font-medium ${link.interface && link.interface.utilization > 70 ? 'text-noc-warning' : 'text-noc-text'}`}>
                  {link.interface?.utilization || 0}%
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted">Latency</span>
                <span className={link.latency > 10 ? 'text-noc-warning' : 'text-noc-success'}>{link.latency} ms</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted">Packet Loss</span>
                <span className={link.packetLoss > 0.05 ? 'text-noc-warning' : 'text-noc-success'}>{link.packetLoss}%</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-noc-text-muted">Availability</span>
                <span className={`font-medium ${link.availability >= link.slaTarget ? 'text-noc-success' : 'text-noc-danger'}`}>{link.availability}%</span>
              </div>
              <div className="pt-2 border-t border-noc-border">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-noc-text-muted">SLA Target</span>
                  <span className="text-noc-text">{link.slaTarget}%</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-4">WAN Latency (24h)</h3>
          <ReactECharts option={latencyChartOption} style={{ height: '200px' }} />
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-4">Bandwidth Usage (24h)</h3>
          <ReactECharts option={bandwidthChartOption} style={{ height: '200px' }} />
        </div>
      </div>

      {/* SLA Summary */}
      <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-noc-text mb-4">SLA Compliance Summary</h3>
        <div className="overflow-x-auto">
          <table className="noc-table">
            <thead>
              <tr>
                <th>ISP Provider</th>
                <th>Target Availability</th>
                <th>Actual Availability</th>
                <th>Target Latency</th>
                <th>Avg Latency</th>
                <th>Target Packet Loss</th>
                <th>Avg Packet Loss</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {wanLinks.map((link) => (
                <tr key={link.id}>
                  <td className="text-sm font-medium">{link.ispName}</td>
                  <td className="text-xs">{link.slaTarget}%</td>
                  <td className={`text-xs font-medium ${link.availability >= link.slaTarget ? 'text-noc-success' : 'text-noc-danger'}`}>{link.availability}%</td>
                  <td className="text-xs">&lt; 20 ms</td>
                  <td className={`text-xs ${link.latency > 10 ? 'text-noc-warning' : 'text-noc-success'}`}>{link.latency} ms</td>
                  <td className="text-xs">&lt; 0.1%</td>
                  <td className={`text-xs ${link.packetLoss > 0.05 ? 'text-noc-warning' : 'text-noc-success'}`}>{link.packetLoss}%</td>
                  <td>
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${link.availability >= link.slaTarget ? 'bg-noc-success/10 text-noc-success' : 'bg-noc-danger/10 text-noc-danger'}`}>
                      {link.availability >= link.slaTarget ? 'PASS' : 'FAIL'}
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
