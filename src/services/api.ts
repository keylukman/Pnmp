/**
 * PNMP API Service
 * Centralized API client for backend communication
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

class ApiService {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('pnmp_token', token);
    } else {
      localStorage.removeItem('pnmp_token');
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('pnmp_token');
    }
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const isMultipart = options.body instanceof FormData;
    const headers: HeadersInit = {
      ...(isMultipart ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.setToken(null);
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Auth
  async login(username: string, password: string) {
    return this.request<{ access_token: string; token_type: string }>('/auth/login/json', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  // Users
  async getUsers() {
    return this.request<any[]>('/users/');
  }

  async getCurrentUser() {
    return this.request<any>('/users/me');
  }

  // Sites
  async getSites() {
    return this.request<any[]>('/sites/');
  }

  async createSite(data: { name: string; description?: string; address?: string }) {
    return this.request<any>('/sites/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateSite(id: number, data: Partial<{ name: string; description: string; address: string }>) {
    return this.request<any>(`/sites/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteSite(id: number) {
    return this.request<void>(`/sites/${id}`, { method: 'DELETE' });
  }

  // Devices
  async getDevices(params?: { site_id?: number; device_role?: string; status?: string; search?: string }) {
    const query = new URLSearchParams();
    if (params?.site_id) query.set('site_id', params.site_id.toString());
    if (params?.device_role) query.set('device_role', params.device_role);
    if (params?.status) query.set('status_filter', params.status);
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();
    return this.request<any[]>(`/devices/${qs ? '?' + qs : ''}`);
  }

  async getDevice(id: number) {
    return this.request<any>(`/devices/${id}`);
  }

  async createDevice(data: any) {
    return this.request<any>('/devices/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateDevice(id: number, data: any) {
    return this.request<any>(`/devices/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteDevice(id: number) {
    return this.request<void>(`/devices/${id}`, { method: 'DELETE' });
  }

  async testConnection(id: number) {
    return this.request<{ success: boolean; message: string; latency_ms?: number }>(`/devices/${id}/test-connection`, {
      method: 'POST',
    });
  }

  // ==================== Milestone 1: Inventory import / export ====================

  /** Preview an .xlsx workbook. READ-ONLY server-side: nothing is written to the DB. */
  async previewImport(file: File) {
    const form = new FormData();
    form.append('file', file);
    return this.request<ImportPreviewResponse>('/devices/import/preview', {
      method: 'POST',
      body: form,
    });
  }

  /** Transactional commit. approvedSites = exact workbook location values the operator approved. */
  async commitImport(file: File, approvedSites: string[] = []) {
    const form = new FormData();
    form.append('file', file);
    form.append('approved_sites', approvedSites.join(','));
    return this.request<ImportCommitResponse>('/devices/import', {
      method: 'POST',
      body: form,
    });
  }

  /** Download the ACTUAL device inventory as CSV (authenticated blob fetch — no fake data). */
  async exportDevicesCsv(): Promise<Blob> {
    const token = this.getToken();
    const response = await fetch(`${API_BASE_URL}/devices/export.csv`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (response.status === 401) {
      this.setToken(null);
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }
    if (!response.ok) throw new Error(`Export failed (HTTP ${response.status})`);
    return response.blob();
  }

  /** Liveness probe used to decide LIVE vs DISCONNECTED. Never throws. */
  async healthCheck(): Promise<boolean> {
    try {
      const res = await fetch('http://127.0.0.1:8000/health', { signal: AbortSignal.timeout(4000) });
      return res.ok;
    } catch {
      return false;
    }
  }

  // Alerts
  async getAlerts() {
    // TODO: Implement when backend alerts endpoint is ready
    return [];
  }

  // Events
  async getEvents() {
    // TODO: Implement when backend events endpoint is ready
    return [];
  }
}

// ---------- Typed contracts mirroring backend/app/api/v1/devices.py ----------

export interface ImportRowPreview {
  row_no: number;
  src_no: string | null;
  name: string | null;
  location: string | null;
  function: string | null;
  condition: string | null;
  vendor_raw: string | null;
  vendor: string | null;
  model: string | null;
  os_version: string | null;
  eol_eosl: string | null;
  ip_raw: string | null;
  management_ip: string | null;
  device_type: string | null;
  device_role: string | null;
  errors: string[];
  warnings: string[];
  duplicate_of_row: number | null;
  db_existing_device_id: number | null;
  site_id: number | null;
  site_status: string | null;
  status: 'importable' | 'invalid' | 'skip_duplicate' | 'skip_site_review';
}

export interface ImportSummary {
  filename?: string;
  sheet?: string;
  total_rows: number;
  valid: number;
  invalid: number;
  duplicate_in_file: number;
  existing_in_db: number;
  review_needed: number;
  truncated?: boolean;
  sites_matched?: number;
  sites_new_pending_approval?: number;
  sites_ambiguous?: number;
  inserted?: number;
  skipped?: number;
  skipped_site_review?: number;
  created_sites?: number;
  [k: string]: number | string | boolean | undefined;
}

export interface SiteMappingEntry {
  location: string;
  status: string; // matched | new_pending_approval | ambiguous | empty
  site_id: number | null;
  site_name: string | null;
  candidates: string[];
  row_numbers: number[];
}

export interface ImportPreviewResponse {
  success: boolean;
  mode: 'preview' | 'dry_run';
  summary: ImportSummary;
  rows: ImportRowPreview[];
  site_mapping: SiteMappingEntry[];
}

export interface ImportCommitResponse {
  success: boolean;
  mode: 'committed';
  summary: ImportSummary & { inserted: number; skipped: number; skipped_site_review: number; created_sites: number };
  message: string;
  imported_device_ids: number[];
}

export const apiService = new ApiService();
export default apiService;
