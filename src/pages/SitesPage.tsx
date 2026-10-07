import { useState } from 'react';
import { useDeviceStore, Site } from '../stores/devices';
import { Plus, MapPin, Server, Edit2, Trash2, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

export default function SitesPage() {
  const { sites, devices, addSite } = useDeviceStore();
  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Sites</h1>
          <p className="text-sm text-noc-text-muted">{sites.length} sites managed • {devices.length} total devices</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="flex items-center gap-2 px-3 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
          <Plus className="w-4 h-4" />
          Add Site
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sites.map((site) => {
          const siteDevices = devices.filter(d => d.siteId === site.id);
          const upCount = siteDevices.filter(d => d.status === 'up').length;
          const downCount = siteDevices.filter(d => d.status === 'down').length;
          const warningCount = siteDevices.filter(d => d.status === 'warning').length;
          const maintenanceCount = siteDevices.filter(d => d.status === 'maintenance').length;
          const availability = siteDevices.length > 0 ? ((upCount / siteDevices.length) * 100).toFixed(0) : '0';

          return (
            <div key={site.id} className="bg-noc-surface border border-noc-border rounded-lg p-4 hover:border-noc-primary/30 transition-colors">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-noc-primary/10 flex items-center justify-center">
                    <MapPin className="w-4 h-4 text-noc-primary" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-noc-text">{site.name}</h3>
                    <p className="text-[10px] text-noc-text-muted">{site.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button className="p-1 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-warning transition-colors">
                    <Edit2 className="w-3 h-3" />
                  </button>
                  <button className="p-1 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-danger transition-colors">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-2 mb-3">
                <div className="text-center p-1.5 bg-noc-bg rounded">
                  <p className="text-sm font-bold text-noc-text">{siteDevices.length}</p>
                  <p className="text-[9px] text-noc-text-muted">Total</p>
                </div>
                <div className="text-center p-1.5 bg-noc-bg rounded">
                  <p className="text-sm font-bold text-noc-success">{upCount}</p>
                  <p className="text-[9px] text-noc-text-muted">UP</p>
                </div>
                <div className="text-center p-1.5 bg-noc-bg rounded">
                  <p className="text-sm font-bold text-noc-danger">{downCount}</p>
                  <p className="text-[9px] text-noc-text-muted">DOWN</p>
                </div>
                <div className="text-center p-1.5 bg-noc-bg rounded">
                  <p className="text-sm font-bold text-noc-warning">{warningCount + maintenanceCount}</p>
                  <p className="text-[9px] text-noc-text-muted">Warn</p>
                </div>
              </div>

              {/* Availability bar */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-noc-text-muted">Availability</span>
                  <span className={`text-[10px] font-medium ${Number(availability) >= 95 ? 'text-noc-success' : Number(availability) >= 80 ? 'text-noc-warning' : 'text-noc-danger'}`}>
                    {availability}%
                  </span>
                </div>
                <div className="w-full h-1.5 bg-noc-bg rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${Number(availability) >= 95 ? 'bg-noc-success' : Number(availability) >= 80 ? 'bg-noc-warning' : 'bg-noc-danger'}`}
                    style={{ width: `${availability}%` }}
                  />
                </div>
              </div>

              {/* Device list preview */}
              <div className="space-y-1">
                {siteDevices.slice(0, 3).map(device => (
                  <div key={device.id} className="flex items-center gap-2 text-[10px]">
                    <span className={`w-1.5 h-1.5 rounded-full ${device.status === 'up' ? 'bg-noc-success' : device.status === 'down' ? 'bg-noc-danger' : 'bg-noc-warning'}`} />
                    <span className="text-noc-text truncate flex-1">{device.displayName}</span>
                    <span className="text-noc-text-muted font-mono">{device.managementIp}</span>
                  </div>
                ))}
                {siteDevices.length > 3 && (
                  <p className="text-[10px] text-noc-text-muted pl-3.5">+{siteDevices.length - 3} more devices</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Site Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-noc-surface border border-noc-border rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-noc-text mb-4">Add New Site</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              const form = e.target as HTMLFormElement;
              const name = (form.elements.namedItem('name') as HTMLInputElement).value;
              const description = (form.elements.namedItem('description') as HTMLTextAreaElement).value;
              addSite({ id: Date.now().toString(), name, description, deviceCount: 0 });
              setShowAddModal(false);
            }} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Site Name *</label>
                <input name="name" type="text" required className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" placeholder="e.g., Data Center, Gedung Akademik" />
              </div>
              <div>
                <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Description</label>
                <textarea name="description" rows={3} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary resize-none" placeholder="Brief description of the site" />
              </div>
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-noc-border">
                <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 text-sm text-noc-text-muted hover:text-noc-text border border-noc-border rounded-lg transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 text-sm text-white bg-noc-primary hover:bg-noc-primary/90 rounded-lg transition-colors">
                  Add Site
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
