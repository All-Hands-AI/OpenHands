
import { create } from 'zustand';
import type { DynamicAgent, AgentTemplate, TechAnalysisResult } from '~/types/agents';
import { DynamicAgentAPI } from './api';

interface DynamicAgentState {
  agents: DynamicAgent[];
  templates: AgentTemplate[];
  loading: boolean;
  error: Error | null;
  
  // Actions
  loadAgents: () => Promise<void>;
  loadTemplates: () => Promise<void>;
  createAgent: (name: string, technologies: string[]) => Promise<void>;
  updateAgent: (id: string, updates: Partial<DynamicAgent>) => Promise<void>;
  deleteAgent: (id: string) => Promise<void>;
  analyzeStack: (technologies: string[]) => Promise<TechAnalysisResult>;
}

export const useDynamicAgentStore = create<DynamicAgentState>((set, get) => ({
  agents: [],
  templates: [],
  loading: false,
  error: null,

  loadAgents: async () => {
    set({ loading: true, error: null });
    try {
      const agents = await DynamicAgentAPI.listAgents();
      set({ agents, loading: false });
    } catch (error) {
      set({ error: error as Error, loading: false });
    }
  },

  loadTemplates: async () => {
    set({ loading: true, error: null });
    try {
      const templates = await DynamicAgentAPI.listTemplates();
      set({ templates, loading: false });
    } catch (error) {
      set({ error: error as Error, loading: false });
    }
  },

  createAgent: async (name: string, technologies: string[]) => {
    set({ loading: true, error: null });
    try {
      const analysis = await DynamicAgentAPI.analyzeStack(technologies);
      const agent = await DynamicAgentAPI.createAgent(name, technologies, analysis);
      set(state => ({
        agents: [...state.agents, agent],
        loading: false
      }));
    } catch (error) {
      set({ error: error as Error, loading: false });
    }
  },

  updateAgent: async (id: string, updates: Partial<DynamicAgent>) => {
    set({ loading: true, error: null });
    try {
      const updatedAgent = await DynamicAgentAPI.updateAgent(id, updates);
      set(state => ({
        agents: state.agents.map(agent =>
          agent.id === id ? updatedAgent : agent
        ),
        loading: false
      }));
    } catch (error) {
      set({ error: error as Error, loading: false });
    }
  },

  deleteAgent: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await DynamicAgentAPI.deleteAgent(id);
      set(state => ({
        agents: state.agents.filter(agent => agent.id !== id),
        loading: false
      }));
    } catch (error) {
      set({ error: error as Error, loading: false });
    }
  },

  analyzeStack: async (technologies: string[]) => {
    set({ loading: true, error: null });
    try {
      const analysis = await DynamicAgentAPI.analyzeStack(technologies);
      set({ loading: false });
      return analysis;
    } catch (error) {
      set({ error: error as Error, loading: false });
      throw error;
    }
  }
}));
