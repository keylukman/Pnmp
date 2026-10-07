import { useState } from 'react';
import { Plus, Edit2, Trash2, Shield, User, Eye } from 'lucide-react';

interface UserData {
  id: string;
  username: string;
  fullName: string;
  email: string;
  role: string;
  lastLogin: string;
  status: 'active' | 'inactive';
}

const demoUsers: UserData[] = [
  { id: '1', username: 'admin', fullName: 'Super Administrator', email: 'admin@pssn.ac.id', role: 'Super Admin', lastLogin: '2026-01-15 10:30', status: 'active' },
  { id: '2', username: 'neteng1', fullName: 'Ahmad Network Engineer', email: 'ahmad@pssn.ac.id', role: 'Network Engineer', lastLogin: '2026-01-15 09:15', status: 'active' },
  { id: '3', username: 'neteng2', fullName: 'Budi Network Engineer', email: 'budi@pssn.ac.id', role: 'Network Engineer', lastLogin: '2026-01-14 16:45', status: 'active' },
  { id: '4', username: 'operator1', fullName: 'Citra Operator', email: 'citra@pssn.ac.id', role: 'Operator', lastLogin: '2026-01-15 08:00', status: 'active' },
  { id: '5', username: 'viewer1', fullName: 'Dewi Viewer', email: 'dewi@pssn.ac.id', role: 'Viewer', lastLogin: '2026-01-10 14:20', status: 'inactive' },
];

const permissions = {
  'Super Admin': ['device.view', 'device.create', 'device.edit', 'device.delete', 'device.monitor', 'alert.view', 'alert.acknowledge', 'configuration.view', 'report.view', 'user.manage'],
  'Admin': ['device.view', 'device.create', 'device.edit', 'device.delete', 'device.monitor', 'alert.view', 'alert.acknowledge', 'configuration.view', 'report.view'],
  'Network Engineer': ['device.view', 'device.create', 'device.edit', 'device.monitor', 'alert.view', 'alert.acknowledge', 'configuration.view', 'report.view'],
  'Operator': ['device.view', 'device.monitor', 'alert.view', 'alert.acknowledge', 'report.view'],
  'Viewer': ['device.view', 'alert.view'],
};

export default function UsersPage() {
  const [users] = useState<UserData[]>(demoUsers);
  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-noc-text">Users</h1>
          <p className="text-sm text-noc-text-muted">{users.length} users registered</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="flex items-center gap-2 px-3 py-2 bg-noc-primary hover:bg-noc-primary/90 text-white text-sm font-medium rounded-lg transition-colors">
          <Plus className="w-4 h-4" />
          Add User
        </button>
      </div>

      {/* Users table */}
      <div className="bg-noc-surface border border-noc-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="noc-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Username</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last Login</th>
                <th>Permissions</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-noc-surface-2 flex items-center justify-center">
                        <span className="text-xs font-bold text-noc-primary">{user.fullName.charAt(0)}</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-noc-text">{user.fullName}</p>
                        <p className="text-[10px] text-noc-text-muted">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="font-mono text-xs text-noc-text-muted">{user.username}</td>
                  <td>
                    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-noc-surface-2 text-noc-text">
                      <Shield className="w-3 h-3" />
                      {user.role}
                    </span>
                  </td>
                  <td>
                    <span className={`text-xs px-2 py-0.5 rounded ${user.status === 'active' ? 'bg-noc-success/10 text-noc-success' : 'bg-noc-text-muted/10 text-noc-text-muted'}`}>
                      {user.status}
                    </span>
                  </td>
                  <td className="text-xs text-noc-text-muted">{user.lastLogin}</td>
                  <td>
                    <span className="text-xs text-noc-text-muted">
                      {permissions[user.role as keyof typeof permissions]?.length || 0} permissions
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button className="p-1.5 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-primary transition-colors">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-warning transition-colors">
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 rounded hover:bg-noc-surface-2 text-noc-text-muted hover:text-noc-danger transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Role permissions reference */}
      <div className="bg-noc-surface border border-noc-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-noc-text mb-4">Role Permissions Reference</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(permissions).map(([role, perms]) => (
            <div key={role} className="bg-noc-bg border border-noc-border rounded-lg p-3">
              <h4 className="text-xs font-semibold text-noc-text mb-2 flex items-center gap-1">
                <User className="w-3 h-3 text-noc-primary" />
                {role}
              </h4>
              <div className="space-y-1">
                {perms.map((perm) => (
                  <div key={perm} className="text-[10px] text-noc-text-muted font-mono">{perm}</div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-noc-surface border border-noc-border rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-noc-text mb-4">Add New User</h3>
            <form onSubmit={(e) => { e.preventDefault(); setShowAddModal(false); }} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Full Name *</label>
                  <input type="text" required className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-noc-text-muted mb-1">Username *</label>
                  <input type="text" required className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-noc-text-muted mb-1">Email *</label>
                <input type="email" required className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
              </div>
              <div>
                <label className="block text-xs font-medium text-noc-text-muted mb-1">Role *</label>
                <select className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary">
                  <option>Viewer</option>
                  <option>Operator</option>
                  <option>Network Engineer</option>
                  <option>Admin</option>
                  <option>Super Admin</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-noc-text-muted mb-1">Password *</label>
                <input type="password" required className="w-full px-3 py-2 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text focus:outline-none focus:border-noc-primary" />
              </div>
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-noc-border">
                <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 text-sm text-noc-text-muted hover:text-noc-text border border-noc-border rounded-lg transition-colors">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm text-white bg-noc-primary hover:bg-noc-primary/90 rounded-lg transition-colors">Create User</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
