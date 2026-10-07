import { useState } from 'react';
import { FileText, Download, Calendar, Filter, TrendingUp, BarChart3, PieChart, Clock } from 'lucide-react';
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
    legend: { data: ['Critical', 'High', 'Warning', 'Info'], textStyle: { color: '#8892a4', fontSize: 10 }, top: 0 },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category' as const, data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    yAxis: { type: 'value' as const, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    series: [
      { name: 'Critical', type: 'bar', stack: 'incidents', data: [0, 0, 1, 0, 0, 0, 0], itemStyle: { color: '#ef4444' } },
      { name: 'High', type: 'bar', stack: 'incidents', data: [1, 2, 1, 3, 1, 0, 1], itemStyle: { color: '#f59e0b' } },
      { name: 'Warning', type: 'bar', stack: 'incidents', data: [3, 2, 4, 2, 3, 1, 2], itemStyle: { color: '#eab308' } },
      { name: 'Info', type: 'bar', stack: 'incidents', data: [5, 4, 6, 3, 5, 2, 4], itemStyle: { color: '#3b82f6' } },
    ],
  };

  const slaChartOption = {
    tooltip: { trigger: 'axis' as const, backgroundColor: '#1a1f2e', borderColor: '#2d3548', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    legend: { data: ['Actual', 'SLA Target'], textStyle: { color: '#8892a4', fontSize: 10 }, top: 0 },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category' as const, data: ['ISP 1', 'ISP 2', 'ISP 3'], axisLine: { lineStyle: { color: '#2d3548' } }, axisLabel: { color: '#8892a4', fontSize: 10 } },
    yAxis: { type: 'value' as const, min: 98, max: 100, axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2535' } }, axisLabel: { color: '#8892a4', fontSize: 10, formatter: '{value}%' } },
    series: [
      { name: 'Actual', type: 'bar', data: [99.92, 99.97, 99.85], itemStyle: { color: '#0ea5e9', borderRadius: [3, 3, 0, 0] }, barWidth: '30%' },
      { name: 'SLA Target', type: 'line', data: [99.5, 99.5, 99.0], lineStyle: { color: '#ef4444', type: 'dashed', width: 2 }, itemStyle: { color: '#ef4444' }, symbol: 'diamond', symbolSize: 8 },
    ],
  };

  const reports = [
    { id: '1', name: 'Device Availability Report', description: 'Overall device availability for the selected period', type: 'availability', lastGenerated: '2026-01-15 08:00', icon: TrendingUp },
    { id: '2', name: 'Interface Utilization Report', description: 'Bandwidth utilization across all monitored interfaces', type: 'utilization', lastGenerated: '2026-01-15 08:00', icon: BarChart3 },
    { id: '3', name: 'Incident Summary', description: 'Summary of all incidents and alerts for the period', type: 'incidents', lastGenerated: '2026-01-15 08:00', icon: PieChart },
    { id: '4', name: 'WAN/ISP Availability', description: 'ISP link availability and SLA compliance report', type: 'wan', lastGenerated: '2026-01-14 08:00', icon: Clock },
    { id: '5', name: 'Device Downtime Report', description: 'Detailed downtime analysis per device', type: 'downtime', lastGenerated: '2026-01-14 08:00', icon: FileText },
    { id: '6', name: 'SLA Compliance Report', description: 'SLA target vs actual performance for all providers', type: 'sla', lastGenerated: '2026-01-13 08:00', icon: TrendingUp },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Reports</h1>
          <p className="text-sm text-noc-text-muted">Generate and export network reports</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={dateRange} onChange={(e) => setDateRange(e.target.value)} className="px-3 py-2 bg-noc-surface border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-3">Network Availability</h3>
          <ReactECharts option={availabilityChartOption} style={{ height: '200px' }} />
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-noc-text mb-3">Incidents by Severity</h3>
          <ReactECharts option={incidentChartOption} style={{ height: '200px' }} />
        </div>
      </div>

      {/* SLA Chart */}
      <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-noc-text mb-3">SLA Compliance - ISP Providers</h3>
        <ReactECharts option={slaChartOption} style={{ height: '200px' }} />
      </div>

      {/* Report list */}
      <div className="bg-noc-surface border border-noc-border rounded-lg">
        <div className="px-4 py-3 border-b border-noc-border flex items-center justify-between">
          <h3 className="text-sm font-semibold text-noc-text">Available Reports</h3>
          <span className="text-xs text-noc-text-muted">{reports.length} reports</span>
        </div>
        <div className="divide-y divide-noc-border/50">
          {reports.map((report) => (
            <div key={report.id} className="px-4 py-3 flex items-center gap-4 hover:bg-noc-surface-2/30 transition-colors">
              <div className="w-9 h-9 rounded-lg bg-noc-primary/10 flex items-center justify-center flex-shrink-0">
                <report.icon className="w-4 h-4 text-noc-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-noc-text">{report.name}</h4>
                <p className="text-xs text-noc-text-muted">{report.description}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-[10px] text-noc-text-muted">Last generated</p>
                <p className="text-xs text-noc-text-muted">{report.lastGenerated}</p>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <button className="px-2.5 py-1.5 text-xs text-noc-primary bg-noc-primary/10 rounded-lg hover:bg-noc-primary/20 transition-colors flex items-center gap-1">
                  <Download className="w-3 h-3" />
                  CSV
                </button>
                <button className="px-2.5 py-1.5 text-xs text-noc-text-muted bg-noc-surface-2 rounded-lg hover:bg-noc-border transition-colors flex items-center gap-1">
                  <FileText className="w-3 h-3" />
                  PDF
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-noc-success">99.85%</p>
          <p className="text-xs text-noc-text-muted mt-1">Avg Availability</p>
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-noc-text">12</p>
          <p className="text-xs text-noc-text-muted mt-1">Total Incidents</p>
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-noc-primary">4.2 min</p>
          <p className="text-xs text-noc-text-muted mt-1">Avg MTTR</p>
        </div>
        <div className="bg-noc-surface border border-noc-border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-noc-success">3/3</p>
          <p className="text-xs text-noc-text-muted mt-1">SLA Compliant</p>
        </div>
      </div>
    </div>
  );
}
