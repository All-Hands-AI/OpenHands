
import { getAuthToken } from '~/utils/auth';
import type { 
  DynamicAgent, 
  AgentTemplate, 
  TechAnalysisResult 
} from '~/types/agents';

const API_BASE = '/api/v1';

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class DynamicAgentAPI {
  private static async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = getAuthToken();
    if (!token) {
      throw new APIError('Authentication required', 401, 'AUTH_REQUIRED');
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
      }
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(
        error.message || 'API request failed',
        response.status,
        error.code
      );
    }
    
    return response.json();
  }

  static async analyzeStack(
    technologies: string[]
  ): Promise<TechAnalysisResult> {
    return this.request('/agents/analyze', {
      method: 'POST',
      body: JSON.stringify({ technologies })
    });
  }

  static async createAgent(
    name: string,
    technologies: string[],
    analysis: TechAnalysisResult
  ): Promise<DynamicAgent> {
    return this.request('/agents', {
      method: 'POST',
      body: JSON.stringify({ name, technologies, analysis })
    });
  }

  static async listAgents(): Promise<DynamicAgent[]> {
    return this.request('/agents');
  }

  static async getAgent(id: string): Promise<DynamicAgent> {
    return this.request(`/agents/${id}`);
  }

  static async updateAgent(
    id: string,
    updates: Partial<DynamicAgent>
  ): Promise<DynamicAgent> {
    return this.request(`/agents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    });
  }

  static async deleteAgent(id: string): Promise<void> {
    await this.request(`/agents/${id}`, {
      method: 'DELETE'
    });
  }

  static async listTemplates(): Promise<AgentTemplate[]> {
    return this.request('/templates');
  }

  static async getTemplate(name: string): Promise<AgentTemplate> {
    return this.request(`/templates/${name}`);
  }
}
