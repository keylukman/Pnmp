import { useState } from 'react';
import { FileText, Download, Calendar, Filter } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

export default function ReportsPage() {
  const [dateRange, setDateRange] = useState('7d');

  const availabilityChartOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    yAxis: { type: 'value' as const, min: 95, max: 100, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 10, formatter: '{value}%' } },
    series: [{ name: 'Availability', type: 'line', smooth: true, data: [99.8, 99.9, 99.7, 99.5, 99.8, 99.9, 99.85], lineStyle: { color: '#22c55e', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(34,197,94,0.3)' }, { offset: 1, color: 'rgba(34,197,94,0)' }] } }, itemStyle: { color: '#22c55e' }, symbol: 'circle', symbolSize: 6 }],
  };

  const incidentChartOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    series: [
      { name: 'Critical', type: 'bar', stack: 'incidents', data: [0, 0, 1, 0, 0, 0, 0], itemStyle: { color: '#ef4444' } },
      { name: 'High', type: 'bar', stack: 'incidents', data: [1, 2, 1, 3, 1, 0, 1], itemStyle: { color: '#f59e0b' } },
      { name: 'Warning', type: 'bar', stack: 'incidents', data: [3, 2, 4, 2, 3, 1, 2], itemStyle: { color: '#eab308' } },
      { name: 'Info', type: 'bar', stack: 'incidents', data: [5, 4, 6, 3, 5, 2, 4], itemStyle: { color: '#3b82f6' } },
    ],
  };

  const reports = [
    { id: '1', name: 'Device Availability Report', description: 'Overall device availability for the selected period', type: 'availability', lastGenerated: '2026-01-15 08:00' },
    { id: '2', name: 'Interface Utilization Report', description: 'Interface bandwidth utilization analysis', type: 'utilization', lastGenerated: '2026-01-15 08:00' },
    { id: '3', name: 'Device Downtime Report', description: 'Detailed downtime events and duration', type: 'downtime', lastGenerated: '2026-01-14 22:00' },
    { id: '4', name: 'WAN Availability Report', description: 'ISP link availability and SLA compliance', type: 'wan', lastGenerated: '2026-01-15 08:00' },
    { id: '5', name: 'Incident Summary', description: 'Summary of all incidents and resolution times', type: 'incident', lastGenerated: '2026-01-15 08:00' },
    { id: '6', name: 'SLA Compliance Report', description: 'SLA target vs actual performance', type: 'sla', lastGenerated: '2026-01-15 08:00' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Reports</h1>
          <p className="text-sm text-noc-text-muted">Generate and export network reports</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-noc-surface border border-noc-border rounded-lg p-3">
        <Calendar className="w-4 h-4 text-noc-text-muted" />
        <select value={dateRange} onChange={(e) => setDateRange(e.target.value)} className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
          <option value="1y">Last Year</option>
        </select>
        <Filter className="w-4 h-4 text-noc-text-muted ml-2" />
        <select className="px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
          <option>All Sites</option>
          <option>Data Center</option>
          <option>Gedung PSSN</option>
          <option>Gedung Akademik</option>
        </select>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-4">Network Availability (7 days)</h3>
          <ReactECharts option={availabilityChartOption} style={{ height: '200px' }} />
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-4">Incidents by Severity (7 days)</h3>
          <ReactECharts option={incidentChartOption} style={{ height: '200px' }} />
        </div>
      </div>

      {/* Report list */}
      <div className="bg-noc-surface border border-noc-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-noc-border">
          <h3 className="text-sm font-semibold text-noc-text">Available Reports</h3>
        </div>
        <div className="divide-y divide-noc-border">
          {reports.map((report) => (
            <div key={report.id} className="flex items-center justify-between p-4 hover:bg-noc-surface-2 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-noc-primary/10 flex items-center justify-center">
                  <FileText className="w-4 h-4 text-noc-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-noc-text">{report.name}</p>
                  <p className="text-xs text-noc-text-muted">{report.description}</p>
                  <p className="text-[10px] text-noc-text-muted mt-0.5">Last generated: {report.lastGenerated}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-noc-text-muted hover:text-noc-text border border-noc-border rounded-lg hover:bg-noc-surface transition-colors">
                  <Download className="w-3 h-3" />
                  CSV
                </button>
                <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-white bg-noc-primary hover:bg-noc-primary/90 rounded-lg transition-colors">
                  <Download className="w-3 h-3" />
                  Generate
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
