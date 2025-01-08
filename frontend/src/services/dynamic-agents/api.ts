import { getAuthToken } from '~/utils/auth';
import type { DynamicAgent } from '~/types/agents';

export class DynamicAgentAPI {
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1/agents') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = getAuthToken();
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  static async listAgents(): Promise<DynamicAgent[]> {
    const api = new DynamicAgentAPI();
    return api.request<DynamicAgent[]>('/');
  }

  static async createAgent(name: string, technologies: string[]): Promise<DynamicAgent> {
    const api = new DynamicAgentAPI();
    return api.request<DynamicAgent>('/', {
      method: 'POST',
      body: JSON.stringify({ name, technologies }),
    });
  }

  static async updateAgent(id: string, updates: Partial<DynamicAgent>): Promise<DynamicAgent> {
    const api = new DynamicAgentAPI();
    return api.request<DynamicAgent>(`/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  static async deleteAgent(id: string): Promise<void> {
    const api = new DynamicAgentAPI();
    await api.request(`/${id}`, { method: 'DELETE' });
  }
}