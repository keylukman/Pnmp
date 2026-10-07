import { useState } from 'react';
import { useDeviceStore, Site } from '../stores/devices';
import { Plus, MapPin, Server, Edit2, Trash2 } from 'lucide-react';

export default function SitesPage() {
  const { sites, devices, addSite } = useDeviceStore();
  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Sites</h1>
          <p className="text-sm text-noc-text-muted">{sites.length} sites managed</p>
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
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button className="p-1 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-danger transition-colors">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-noc-text-muted flex items-center gap-1"><Server className="w-3 h-3" /> Devices</span>
                  <span className="text-noc-text font-medium">{siteDevices.length}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-noc-text-muted">UP</span>
                  <span className="text-noc-success font-medium">{upCount}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-noc-text-muted">DOWN</span>
                  <span className={`font-medium ${downCount > 0 ? 'text-noc-danger' : 'text-noc-text-muted'}`}>{downCount}</span>
                </div>
                <div className="pt-2 border-t border-noc-border">
                  <div className="flex gap-1">
                    {siteDevices.slice(0, 8).map((d) => (
                      <div key={d.id} className={`w-2 h-2 rounded-full ${d.status === 'up' ? 'bg-noc-success' : d.status === 'down' ? 'bg-noc-danger' : d.status === 'warning' ? 'bg-noc-warning' : 'bg-noc-text-muted'}`} title={d.displayName} />
                    ))}
                    {siteDevices.length > 8 && <span className="text-[9px] text-noc-text-muted">+{siteDevices.length - 8}</span>}
                  </div>
                </div>
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
            <form onSubmit={(e) => { e.preventDefault(); setShowAddModal(false); }} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-noc-text-muted mb-1">Site Name *</label>
                <input type="text" required className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" placeholder="e.g., Data Center" />
              </div>
              <div>
                <label className="block text-xs font-medium text-noc-text-muted mb-1">Description</label>
                <textarea rows={2} className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary resize-none" placeholder="Site description..." />
              </div>
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-noc-border">
                <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 text-sm text-noc-text-muted hover:text-noc-text border border-noc-border rounded-lg transition-colors">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm text-white bg-noc-primary hover:bg-noc-primary/90 rounded-lg transition-colors">Add Site</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
