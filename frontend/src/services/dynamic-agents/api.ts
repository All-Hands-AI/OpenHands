
import type { DynamicAgent, AgentTemplate, TechAnalysisResult } from '~/types/agents';

const API_BASE = '/api/v1';

export class DynamicAgentAPI {
  static async analyzeStack(technologies: string[]): Promise<TechAnalysisResult> {
    const response = await fetch(`${API_BASE}/agents/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ technologies })
    });
    
    if (!response.ok) {
      throw new Error('Failed to analyze tech stack');
    }
    
    return response.json();
  }

  static async createAgent(
    name: string,
    technologies: string[],
    analysis: TechAnalysisResult
  ): Promise<DynamicAgent> {
    const response = await fetch(`${API_BASE}/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, technologies, analysis })
    });
    
    if (!response.ok) {
      throw new Error('Failed to create agent');
    }
    
    return response.json();
  }

  static async listAgents(): Promise<DynamicAgent[]> {
    const response = await fetch(`${API_BASE}/agents`);
    
    if (!response.ok) {
      throw new Error('Failed to list agents');
    }
    
    return response.json();
  }

  static async getAgent(id: string): Promise<DynamicAgent> {
    const response = await fetch(`${API_BASE}/agents/${id}`);
    
    if (!response.ok) {
      throw new Error('Failed to get agent');
    }
    
    return response.json();
  }

  static async updateAgent(id: string, updates: Partial<DynamicAgent>): Promise<DynamicAgent> {
    const response = await fetch(`${API_BASE}/agents/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    
    if (!response.ok) {
      throw new Error('Failed to update agent');
    }
    
    return response.json();
  }

  static async deleteAgent(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/agents/${id}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete agent');
    }
  }

  static async listTemplates(): Promise<AgentTemplate[]> {
    const response = await fetch(`${API_BASE}/templates`);
    
    if (!response.ok) {
      throw new Error('Failed to list templates');
    }
    
    return response.json();
  }

  static async getTemplate(name: string): Promise<AgentTemplate> {
    const response = await fetch(`${API_BASE}/templates/${name}`);
    
    if (!response.ok) {
      throw new Error('Failed to get template');
    }
    
    return response.json();
  }
}
