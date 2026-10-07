import { create } from 'zustand';

export type DeviceStatus = 'up' | 'down' | 'warning' | 'unknown' | 'maintenance';
export type DeviceRole = 'core_switch' | 'distribution_switch' | 'access_switch' | 'router' | 'firewall' | 'wireless_controller' | 'access_point' | 'server' | 'load_balancer' | 'other';

export interface Device {
  id: string;
  hostname: string;
  displayName: string;
  managementIp: string;
  vendor: string;
  model: string;
  serialNumber: string;
  deviceType: string;
  deviceRole: DeviceRole;
  siteId: string;
  siteName: string;
  location: string;
  status: DeviceStatus;
  monitoringEnabled: boolean;
  description: string;
  firmwareVersion: string;
  macAddress: string;
  uptime: string;
  cpu: number;
  memory: number;
  temperature: number;
  lastSeen: string;
  createdAt: string;
}

export interface Site {
  id: string;
  name: string;
  description: string;
  deviceCount: number;
}

export interface Alert {
  id: string;
  deviceId: string;
  deviceName: string;
  severity: 'critical' | 'high' | 'warning' | 'info';
  title: string;
  description: string;
  source: string;
  status: 'open' | 'acknowledged' | 'resolved';
  createdAt: string;
}

export interface InterfaceData {
  id: string;
  deviceId: string;
  deviceName: string;
  name: string;
  description: string;
  status: 'up' | 'down' | 'admin_down';
  speed: string;
  rxBytes: number;
  txBytes: number;
  rxErrors: number;
  txErrors: number;
  rxDiscards: number;
  txDiscards: number;
  utilization: number;
}

export interface EventLog {
  id: string;
  deviceId: string;
  deviceName: string;
  category: string;
  severity: 'critical' | 'high' | 'warning' | 'info';
  message: string;
  timestamp: string;
  source: string;
}

export interface TopologyLink {
  id: string;
  sourceDeviceId: string;
  sourceInterface: string;
  targetDeviceId: string;
  targetInterface: string;
  linkType: 'lldp' | 'cdp' | 'manual';
  bandwidth: string;
  status: 'up' | 'down';
}

interface DeviceState {
  devices: Device[];
  sites: Site[];
  alerts: Alert[];
  interfaces: InterfaceData[];
  events: EventLog[];
  topologyLinks: TopologyLink[];
  selectedDevice: Device | null;
  setSelectedDevice: (device: Device | null) => void;
  addDevice: (device: Device) => void;
  updateDevice: (id: string, updates: Partial<Device>) => void;
  deleteDevice: (id: string) => void;
  addSite: (site: Site) => void;
  acknowledgeAlert: (id: string) => void;
  resolveAlert: (id: string) => void;
}

// Demo data
const demoSites: Site[] = [
  { id: '1', name: 'Data Center', description: 'Main data center facility with redundant power and cooling', deviceCount: 3 },
  { id: '2', name: 'Gedung PSSN', description: 'Pusat Sistem dan Sumber Informasi Nasional', deviceCount: 8 },
  { id: '3', name: 'Gedung Akademik', description: 'Academic Building - Faculty and classrooms', deviceCount: 12 },
  { id: '4', name: 'Gedung Administrasi', description: 'Administration Building', deviceCount: 5 },
  { id: '5', name: 'Dormitory', description: 'Student Dormitory Complex', deviceCount: 6 },
  { id: '6', name: 'Internet Gateway', description: 'ISP Gateway Point - Multi-homed connection', deviceCount: 4 },
];

const demoDevices: Device[] = [
  { id: '1', hostname: 'FG-200G-DC', displayName: 'FortiGate 200G', managementIp: '10.0.0.1', vendor: 'Fortinet', model: 'FortiGate 200G', serialNumber: 'FG200G-XXXX', deviceType: 'Firewall', deviceRole: 'firewall', siteId: '1', siteName: 'Data Center', location: 'Rack A1', status: 'up', monitoringEnabled: true, description: 'Main perimeter firewall - Active', firmwareVersion: '7.4.2', macAddress: '00:1A:2B:3C:4D:01', uptime: '45d 12h 30m', cpu: 23, memory: 45, temperature: 42, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-06-01T00:00:00Z' },
  { id: '2', hostname: 'FG-101F-DC', displayName: 'FortiGate 101F', managementIp: '10.0.0.2', vendor: 'Fortinet', model: 'FortiGate 101F', serialNumber: 'FG101F-XXXX', deviceType: 'Firewall', deviceRole: 'firewall', siteId: '1', siteName: 'Data Center', location: 'Rack A2', status: 'up', monitoringEnabled: true, description: 'Secondary firewall - Standby', firmwareVersion: '7.4.1', macAddress: '00:1A:2B:3C:4D:02', uptime: '30d 8h 15m', cpu: 18, memory: 38, temperature: 39, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-06-01T00:00:00Z' },
  { id: '3', hostname: 'FAZ-150G-DC', displayName: 'FortiAnalyzer 150G', managementIp: '10.0.0.3', vendor: 'Fortinet', model: 'FortiAnalyzer 150G', serialNumber: 'FAZ150G-XXXX', deviceType: 'Security', deviceRole: 'server', siteId: '1', siteName: 'Data Center', location: 'Rack A3', status: 'up', monitoringEnabled: true, description: 'Security log analytics and reporting', firmwareVersion: '7.4.1', macAddress: '00:1A:2B:3C:4D:03', uptime: '60d 2h 45m', cpu: 55, memory: 72, temperature: 44, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-06-01T00:00:00Z' },
  { id: '4', hostname: 'LSN-C3750-DIST-STSN-Lt3-01', displayName: 'Cisco 3750 Distribution', managementIp: '10.1.3.1', vendor: 'Cisco', model: 'Catalyst 3750', serialNumber: 'C3750-XXXX', deviceType: 'Switch', deviceRole: 'distribution_switch', siteId: '2', siteName: 'Gedung PSSN', location: 'Floor 3, Rack B1', status: 'up', monitoringEnabled: true, description: 'Distribution switch Layer 3', firmwareVersion: '15.0(2)SE11', macAddress: '00:1A:2B:3C:4D:04', uptime: '120d 5h 20m', cpu: 12, memory: 45, temperature: 38, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-03-15T00:00:00Z' },
  { id: '5', hostname: 'SSR-DMZSW', displayName: 'SSR (DMZ Switch)', managementIp: '10.1.3.2', vendor: 'Cisco', model: 'Catalyst 2960', serialNumber: 'C2960-XXXX', deviceType: 'Switch', deviceRole: 'access_switch', siteId: '2', siteName: 'Gedung PSSN', location: 'Floor 3, Rack B2', status: 'warning', monitoringEnabled: true, description: 'DMZ access switch - High load', firmwareVersion: '15.0(2)SE9', macAddress: '00:1A:2B:3C:4D:05', uptime: '90d 14h 10m', cpu: 67, memory: 82, temperature: 52, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-03-15T00:00:00Z' },
  { id: '6', hostname: 'CCR-01', displayName: 'Cloud Core Router 01', managementIp: '10.2.0.1', vendor: 'MikroTik', model: 'CCR2004', serialNumber: 'MT-CCR01', deviceType: 'Router', deviceRole: 'router', siteId: '6', siteName: 'Internet Gateway', location: 'Rack C1', status: 'up', monitoringEnabled: true, description: 'Core router ISP 1 - Telkomsel', firmwareVersion: '7.12', macAddress: '00:1A:2B:3C:4D:06', uptime: '180d 3h 45m', cpu: 35, memory: 52, temperature: 48, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-01-10T00:00:00Z' },
  { id: '7', hostname: 'CCR-02', displayName: 'Cloud Core Router 02', managementIp: '10.2.0.2', vendor: 'MikroTik', model: 'CCR2004', serialNumber: 'MT-CCR02', deviceType: 'Router', deviceRole: 'router', siteId: '6', siteName: 'Internet Gateway', location: 'Rack C2', status: 'up', monitoringEnabled: true, description: 'Core router ISP 2 - Biznet', firmwareVersion: '7.12', macAddress: '00:1A:2B:3C:4D:07', uptime: '180d 3h 44m', cpu: 32, memory: 48, temperature: 46, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-01-10T00:00:00Z' },
  { id: '8', hostname: 'PEPLINK-B710', displayName: 'Peplink Balance 710', managementIp: '10.2.0.3', vendor: 'Peplink', model: 'Balance 710', serialNumber: 'PB710-XXXX', deviceType: 'Router', deviceRole: 'load_balancer', siteId: '6', siteName: 'Internet Gateway', location: 'Rack C3', status: 'up', monitoringEnabled: true, description: 'SD-WAN Load Balancer', firmwareVersion: '8.3.0', macAddress: '00:1A:2B:3C:4D:08', uptime: '90d 18h 20m', cpu: 28, memory: 42, temperature: 41, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-05-20T00:00:00Z' },
  { id: '9', hostname: 'ARUBA-CX-CORE', displayName: 'Aruba CX Core Switch', managementIp: '10.1.0.1', vendor: 'Aruba', model: 'CX 8325', serialNumber: 'ACX8325-XXXX', deviceType: 'Switch', deviceRole: 'core_switch', siteId: '2', siteName: 'Gedung PSSN', location: 'Floor 1, Rack A1', status: 'up', monitoringEnabled: true, description: 'Core switch AOS-CX - Primary', firmwareVersion: '10.11', macAddress: '00:1A:2B:3C:4D:09', uptime: '60d 10h 5m', cpu: 15, memory: 35, temperature: 36, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-08-01T00:00:00Z' },
  { id: '10', hostname: 'ARUBA-WLC-01', displayName: 'Aruba Wireless Controller', managementIp: '10.1.0.2', vendor: 'Aruba', model: '7010', serialNumber: 'AWLC7010-XXXX', deviceType: 'Wireless Controller', deviceRole: 'wireless_controller', siteId: '2', siteName: 'Gedung PSSN', location: 'Floor 1, Rack A2', status: 'up', monitoringEnabled: true, description: 'Mobility Controller - 24 APs managed', firmwareVersion: '8.11', macAddress: '00:1A:2B:3C:4D:10', uptime: '45d 6h 30m', cpu: 42, memory: 58, temperature: 44, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-08-01T00:00:00Z' },
  { id: '11', hostname: 'CLEARPASS-01', displayName: 'Aruba ClearPass', managementIp: '10.1.0.3', vendor: 'Aruba', model: 'ClearPass 3500', serialNumber: 'CPP3500-XXXX', deviceType: 'Security', deviceRole: 'server', siteId: '2', siteName: 'Gedung PSSN', location: 'Floor 1, Rack A3', status: 'up', monitoringEnabled: true, description: 'Network Access Control - RADIUS/TACACS+', firmwareVersion: '6.11', macAddress: '00:1A:2B:3C:4D:11', uptime: '90d 12h 15m', cpu: 38, memory: 65, temperature: 40, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-08-01T00:00:00Z' },
  { id: '12', hostname: 'R2911-INT01', displayName: 'Cisco 2911 Router', managementIp: '10.1.4.1', vendor: 'Cisco', model: 'ISR 2911', serialNumber: 'C2911-XXXX', deviceType: 'Router', deviceRole: 'router', siteId: '2', siteName: 'Gedung PSSN', location: 'Floor 2, Rack D1', status: 'down', monitoringEnabled: true, description: 'Internal router - UNREACHABLE', firmwareVersion: '15.7(3)M5', macAddress: '00:1A:2B:3C:4D:12', uptime: '0d 0h 0m', cpu: 0, memory: 0, temperature: 0, lastSeen: '2026-01-15T08:15:00Z', createdAt: '2024-02-01T00:00:00Z' },
  { id: '13', hostname: 'MT-SWOS-01', displayName: 'MikroTik SwOS', managementIp: '10.1.5.1', vendor: 'MikroTik', model: 'CRS328', serialNumber: 'MT-CRS328-XXXX', deviceType: 'Switch', deviceRole: 'access_switch', siteId: '3', siteName: 'Gedung Akademik', location: 'Floor 1, Rack E1', status: 'up', monitoringEnabled: true, description: 'Access switch SwOS managed', firmwareVersion: '2.16', macAddress: '00:1A:2B:3C:4D:13', uptime: '150d 8h 40m', cpu: 8, memory: 28, temperature: 35, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-04-10T00:00:00Z' },
  { id: '14', hostname: 'AP-PSSN-01', displayName: 'Aruba AP PSSN-01', managementIp: '10.1.6.1', vendor: 'Aruba', model: 'AP-515', serialNumber: 'AAP515-XXXX', deviceType: 'Access Point', deviceRole: 'access_point', siteId: '2', siteName: 'Gedung PSSN', location: 'Floor 2, Hallway', status: 'up', monitoringEnabled: true, description: 'Access point Floor 2 - 5GHz/2.4GHz', firmwareVersion: '8.10', macAddress: '00:1A:2B:3C:4D:14', uptime: '30d 4h 20m', cpu: 22, memory: 45, temperature: 38, lastSeen: '2026-01-15T10:30:00Z', createdAt: '2024-09-01T00:00:00Z' },
  { id: '15', hostname: 'AP-AKAD-01', displayName: 'Aruba AP Akademik-01', managementIp: '10.1.7.1', vendor: 'Aruba', model: 'AP-535', serialNumber: 'AAP535-XXXX', deviceType: 'Access Point', deviceRole: 'access_point', siteId: '3', siteName: 'Gedung Akademik', location: 'Floor 3, Room 301', status: 'maintenance', monitoringEnabled: false, description: 'Access point Akademik Floor 3 - Maintenance', firmwareVersion: '8.10', macAddress: '00:1A:2B:3C:4D:15', uptime: '0d 0h 0m', cpu: 0, memory: 0, temperature: 0, lastSeen: '2026-01-14T16:00:00Z', createdAt: '2024-09-01T00:00:00Z' },
];

const demoAlerts: Alert[] = [
  { id: '1', deviceId: '12', deviceName: 'Cisco 2911 Router', severity: 'critical', title: 'Device DOWN', description: 'Device unreachable via SNMP and ping for 2+ hours', source: 'monitoring', status: 'open', createdAt: '2026-01-15T08:15:00Z' },
  { id: '2', deviceId: '5', deviceName: 'SSR (DMZ Switch)', severity: 'high', title: 'High CPU Usage', description: 'CPU utilization exceeded 65% threshold for 15 minutes', source: 'monitoring', status: 'open', createdAt: '2026-01-15T09:45:00Z' },
  { id: '3', deviceId: '5', deviceName: 'SSR (DMZ Switch)', severity: 'high', title: 'High Memory Usage', description: 'Memory utilization exceeded 80% threshold', source: 'monitoring', status: 'acknowledged', createdAt: '2026-01-15T09:50:00Z' },
  { id: '4', deviceId: '9', deviceName: 'Aruba CX Core Switch', severity: 'warning', title: 'Interface Flapping', description: 'Interface 1/1/48 link up/down detected 5 times in 10 minutes', source: 'monitoring', status: 'open', createdAt: '2026-01-15T10:00:00Z' },
  { id: '5', deviceId: '3', deviceName: 'FortiAnalyzer 150G', severity: 'warning', title: 'Disk Usage High', description: 'Log storage at 85% capacity - Consider archive or cleanup', source: 'monitoring', status: 'acknowledged', createdAt: '2026-01-14T22:30:00Z' },
  { id: '6', deviceId: '10', deviceName: 'Aruba Wireless Controller', severity: 'info', title: 'AP Reassociation', description: '3 APs reassociated to controller during roaming', source: 'monitoring', status: 'resolved', createdAt: '2026-01-14T18:00:00Z' },
  { id: '7', deviceId: '6', deviceName: 'Cloud Core Router 01', severity: 'warning', title: 'BGP Peer Down', description: 'BGP peer 10.255.0.1 state changed to Idle', source: 'monitoring', status: 'open', createdAt: '2026-01-15T07:20:00Z' },
  { id: '8', deviceId: '15', deviceName: 'Aruba AP Akademik-01', severity: 'info', title: 'Maintenance Mode', description: 'Device placed in maintenance mode by admin', source: 'system', status: 'acknowledged', createdAt: '2026-01-14T16:00:00Z' },
  { id: '9', deviceId: '1', deviceName: 'FortiGate 200G', severity: 'warning', title: 'HA Sync Warning', description: 'HA heartbeat delay detected between FG-200G and FG-101F', source: 'api', status: 'open', createdAt: '2026-01-15T10:15:00Z' },
  { id: '10', deviceId: '11', deviceName: 'Aruba ClearPass', severity: 'info', title: 'Certificate Expiring', description: 'RADIUS server certificate expires in 30 days', source: 'monitoring', status: 'open', createdAt: '2026-01-15T06:00:00Z' },
];

const demoInterfaces: InterfaceData[] = [
  { id: '1', deviceId: '9', deviceName: 'Aruba CX Core Switch', name: '1/1/1', description: 'Uplink to CCR-01', status: 'up', speed: '10Gbps', rxBytes: 1250000000, txBytes: 890000000, rxErrors: 0, txErrors: 0, rxDiscards: 2, txDiscards: 0, utilization: 45 },
  { id: '2', deviceId: '9', deviceName: 'Aruba CX Core Switch', name: '1/1/2', description: 'Uplink to CCR-02', status: 'up', speed: '10Gbps', rxBytes: 980000000, txBytes: 750000000, rxErrors: 0, txErrors: 0, rxDiscards: 0, txDiscards: 1, utilization: 38 },
  { id: '3', deviceId: '9', deviceName: 'Aruba CX Core Switch', name: '1/1/48', description: 'Downlink to DIST-SW', status: 'up', speed: '1Gbps', rxBytes: 450000000, txBytes: 320000000, rxErrors: 12, txErrors: 3, rxDiscards: 5, txDiscards: 2, utilization: 72 },
  { id: '4', deviceId: '4', deviceName: 'Cisco 3750 Distribution', name: 'Gi1/0/1', description: 'Uplink to Core', status: 'up', speed: '1Gbps', rxBytes: 320000000, txBytes: 450000000, rxErrors: 0, txErrors: 0, rxDiscards: 0, txDiscards: 0, utilization: 55 },
  { id: '5', deviceId: '4', deviceName: 'Cisco 3750 Distribution', name: 'Gi1/0/24', description: 'Server VLAN', status: 'up', speed: '1Gbps', rxBytes: 780000000, txBytes: 620000000, rxErrors: 0, txErrors: 0, rxDiscards: 0, txDiscards: 0, utilization: 82 },
  { id: '6', deviceId: '6', deviceName: 'Cloud Core Router 01', name: 'ether1', description: 'ISP 1 WAN - Telkomsel', status: 'up', speed: '1Gbps', rxBytes: 2500000000, txBytes: 1800000000, rxErrors: 0, txErrors: 0, rxDiscards: 15, txDiscards: 8, utilization: 68 },
  { id: '7', deviceId: '7', deviceName: 'Cloud Core Router 02', name: 'ether1', description: 'ISP 2 WAN - Biznet', status: 'up', speed: '1Gbps', rxBytes: 2100000000, txBytes: 1500000000, rxErrors: 0, txErrors: 0, rxDiscards: 5, txDiscards: 3, utilization: 55 },
  { id: '8', deviceId: '1', deviceName: 'FortiGate 200G', name: 'port1', description: 'WAN Interface', status: 'up', speed: '10Gbps', rxBytes: 5200000000, txBytes: 3800000000, rxErrors: 0, txErrors: 0, rxDiscards: 0, txDiscards: 0, utilization: 42 },
  { id: '9', deviceId: '1', deviceName: 'FortiGate 200G', name: 'port2', description: 'LAN Interface', status: 'up', speed: '10Gbps', rxBytes: 3800000000, txBytes: 5200000000, rxErrors: 0, txErrors: 0, rxDiscards: 0, txDiscards: 0, utilization: 38 },
  { id: '10', deviceId: '12', deviceName: 'Cisco 2911 Router', name: 'Gi0/0', description: 'Internal Network', status: 'down', speed: '1Gbps', rxBytes: 0, txBytes: 0, rxErrors: 0, txErrors: 0, rxDiscards: 0, txDiscards: 0, utilization: 0 },
  { id: '11', deviceId: '13', deviceName: 'MikroTik SwOS', name: 'port1', description: 'Uplink to Core', status: 'up', speed: '1Gbps', rxBytes: 280000000, txBytes: 190000000, rxErrors: 0, txErrors: 0, rxDiscards: 0, txDiscards: 0, utilization: 28 },
  { id: '12', deviceId: '5', deviceName: 'SSR (DMZ Switch)', name: 'Gi0/1', description: 'DMZ Uplink', status: 'up', speed: '1Gbps', rxBytes: 560000000, txBytes: 420000000, rxErrors: 2, txErrors: 1, rxDiscards: 8, txDiscards: 4, utilization: 78 },
  { id: '13', deviceId: '8', deviceName: 'Peplink Balance 710', name: 'WAN1', description: 'ISP 1 Connection', status: 'up', speed: '1Gbps', rxBytes: 1800000000, txBytes: 1200000000, rxErrors: 0, txErrors: 0, rxDiscards: 3, txDiscards: 1, utilization: 48 },
  { id: '14', deviceId: '8', deviceName: 'Peplink Balance 710', name: 'WAN2', description: 'ISP 2 Connection', status: 'up', speed: '1Gbps', rxBytes: 1500000000, txBytes: 1000000000, rxErrors: 0, txErrors: 0, rxDiscards: 1, txDiscards: 0, utilization: 38 },
  { id: '15', deviceId: '10', deviceName: 'Aruba Wireless Controller', name: 'ge0/0/0', description: 'Management Uplink', status: 'up', speed: '10Gbps', rxBytes: 890000000, txBytes: 650000000, rxErrors: 0, txErrors: 0, rxDiscards: 0, txDiscards: 0, utilization: 32 },
];

const demoEvents: EventLog[] = [
  { id: '1', deviceId: '12', deviceName: 'Cisco 2911 Router', category: 'Connectivity', severity: 'critical', message: 'Device DOWN - No response to ICMP/SNMP for 2+ hours', timestamp: '2026-01-15T08:15:00Z', source: 'monitoring' },
  { id: '2', deviceId: '9', deviceName: 'Aruba CX Core Switch', category: 'Interface', severity: 'warning', message: 'Interface 1/1/48 link down', timestamp: '2026-01-15T10:05:00Z', source: 'snmp' },
  { id: '3', deviceId: '9', deviceName: 'Aruba CX Core Switch', category: 'Interface', severity: 'info', message: 'Interface 1/1/48 link up', timestamp: '2026-01-15T10:02:00Z', source: 'snmp' },
  { id: '4', deviceId: '9', deviceName: 'Aruba CX Core Switch', category: 'Interface', severity: 'warning', message: 'Interface 1/1/48 link down', timestamp: '2026-01-15T10:00:00Z', source: 'snmp' },
  { id: '5', deviceId: '5', deviceName: 'SSR (DMZ Switch)', category: 'Performance', severity: 'high', message: 'CPU utilization at 67% - Threshold: 65%', timestamp: '2026-01-15T09:45:00Z', source: 'monitoring' },
  { id: '6', deviceId: '5', deviceName: 'SSR (DMZ Switch)', category: 'Performance', severity: 'high', message: 'Memory utilization at 82% - Threshold: 80%', timestamp: '2026-01-15T09:50:00Z', source: 'monitoring' },
  { id: '7', deviceId: '6', deviceName: 'Cloud Core Router 01', category: 'Routing', severity: 'warning', message: 'BGP peer 10.255.0.1 state changed to Idle', timestamp: '2026-01-15T07:20:00Z', source: 'snmp' },
  { id: '8', deviceId: '10', deviceName: 'Aruba Wireless Controller', category: 'Wireless', severity: 'info', message: 'AP-515-001 reassociated from WLC', timestamp: '2026-01-14T18:00:00Z', source: 'api' },
  { id: '9', deviceId: '10', deviceName: 'Aruba Wireless Controller', category: 'Wireless', severity: 'info', message: 'AP-535-002 reassociated from WLC', timestamp: '2026-01-14T18:01:00Z', source: 'api' },
  { id: '10', deviceId: '15', deviceName: 'Aruba AP Akademik-01', category: 'System', severity: 'info', message: 'Device placed in maintenance mode by admin', timestamp: '2026-01-14T16:00:00Z', source: 'system' },
  { id: '11', deviceId: '1', deviceName: 'FortiGate 200G', category: 'Security', severity: 'info', message: 'IPS signature database updated to v74.231', timestamp: '2026-01-14T03:00:00Z', source: 'api' },
  { id: '12', deviceId: '11', deviceName: 'Aruba ClearPass', category: 'Authentication', severity: 'info', message: 'RADIUS: 1,247 successful authentications in last hour', timestamp: '2026-01-15T10:00:00Z', source: 'api' },
  { id: '13', deviceId: '1', deviceName: 'FortiGate 200G', category: 'HA', severity: 'warning', message: 'HA heartbeat delay: 2.5s (threshold: 2s)', timestamp: '2026-01-15T10:15:00Z', source: 'api' },
  { id: '14', deviceId: '3', deviceName: 'FortiAnalyzer 150G', category: 'Storage', severity: 'warning', message: 'Disk usage at 85% - Log partition', timestamp: '2026-01-14T22:30:00Z', source: 'monitoring' },
  { id: '15', deviceId: '11', deviceName: 'Aruba ClearPass', category: 'Certificate', severity: 'info', message: 'RADIUS server certificate expires in 30 days', timestamp: '2026-01-15T06:00:00Z', source: 'monitoring' },
];

const demoTopologyLinks: TopologyLink[] = [
  { id: '1', sourceDeviceId: '6', sourceInterface: 'ether2', targetDeviceId: '1', targetInterface: 'port1', linkType: 'lldp', bandwidth: '10Gbps', status: 'up' },
  { id: '2', sourceDeviceId: '7', sourceInterface: 'ether2', targetDeviceId: '2', targetInterface: 'port1', linkType: 'lldp', bandwidth: '10Gbps', status: 'up' },
  { id: '3', sourceDeviceId: '1', sourceInterface: 'port2', targetDeviceId: '9', targetInterface: '1/1/1', linkType: 'lldp', bandwidth: '10Gbps', status: 'up' },
  { id: '4', sourceDeviceId: '2', sourceInterface: 'port2', targetDeviceId: '9', targetInterface: '1/1/2', linkType: 'lldp', bandwidth: '10Gbps', status: 'up' },
  { id: '5', sourceDeviceId: '9', sourceInterface: '1/1/48', targetDeviceId: '4', targetInterface: 'Gi1/0/1', linkType: 'lldp', bandwidth: '1Gbps', status: 'up' },
  { id: '6', sourceDeviceId: '9', sourceInterface: '1/1/47', targetDeviceId: '10', targetInterface: 'ge0/0/0', linkType: 'lldp', bandwidth: '10Gbps', status: 'up' },
  { id: '7', sourceDeviceId: '4', sourceInterface: 'Gi1/0/24', targetDeviceId: '5', targetInterface: 'Gi0/1', linkType: 'lldp', bandwidth: '1Gbps', status: 'up' },
  { id: '8', sourceDeviceId: '4', sourceInterface: 'Gi1/0/48', targetDeviceId: '12', targetInterface: 'Gi0/0', linkType: 'lldp', bandwidth: '1Gbps', status: 'down' },
  { id: '9', sourceDeviceId: '9', sourceInterface: '1/1/46', targetDeviceId: '11', targetInterface: 'eth0', linkType: 'lldp', bandwidth: '1Gbps', status: 'up' },
  { id: '10', sourceDeviceId: '10', sourceInterface: 'ge0/0/1', targetDeviceId: '14', targetInterface: 'eth0', linkType: 'manual', bandwidth: '1Gbps', status: 'up' },
  { id: '11', sourceDeviceId: '8', sourceInterface: 'LAN', targetDeviceId: '9', targetInterface: '1/1/3', linkType: 'manual', bandwidth: '10Gbps', status: 'up' },
  { id: '12', sourceDeviceId: '4', sourceInterface: 'Gi1/0/47', targetDeviceId: '13', targetInterface: 'port1', linkType: 'lldp', bandwidth: '1Gbps', status: 'up' },
];

export const useDeviceStore = create<DeviceState>((set) => ({
  devices: demoDevices,
  sites: demoSites,
  alerts: demoAlerts,
  interfaces: demoInterfaces,
  events: demoEvents,
  topologyLinks: demoTopologyLinks,
  selectedDevice: null,
  setSelectedDevice: (device) => set({ selectedDevice: device }),
  addDevice: (device) => set((state) => ({ devices: [...state.devices, device] })),
  updateDevice: (id, updates) => set((state) => ({
    devices: state.devices.map((d) => d.id === id ? { ...d, ...updates } : d),
  })),
  deleteDevice: (id) => set((state) => ({
    devices: state.devices.filter((d) => d.id !== id),
  })),
  addSite: (site) => set((state) => ({ sites: [...state.sites, site] })),
  acknowledgeAlert: (id) => set((state) => ({
    alerts: state.alerts.map((a) => a.id === id ? { ...a, status: 'acknowledged' as const } : a),
  })),
  resolveAlert: (id) => set((state) => ({
    alerts: state.alerts.map((a) => a.id === id ? { ...a, status: 'resolved' as const } : a),
  })),
}));
