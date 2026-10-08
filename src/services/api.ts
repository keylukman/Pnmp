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
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
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

export const apiService = new ApiService();
export default apiService;
