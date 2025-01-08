import { create } from 'zustand';
import type { DynamicAgent, TechAnalysisResult } from '~/types/agents';
import { DynamicAgentAPI } from '~/services/dynamic-agents/api';

interface DynamicAgentState {
  agents: DynamicAgent[];
  templates: DynamicAgent[];
  loading: boolean;
  error: Error | null;
  createAgent: (name: string, technologies: string[]) => Promise<boolean>;
  updateAgent: (id: string, updates: Partial<DynamicAgent>) => Promise<boolean>;
  deleteAgent: (id: string) => Promise<void>;
  analyzeStack: (technologies: string[]) => Promise<TechAnalysisResult>;
}

export const useDynamicAgentStore = create<DynamicAgentState>((set) => ({
  agents: [],
  templates: [],
  loading: false,
  error: null,

  async createAgent(name: string, technologies: string[]): Promise<boolean> {
    try {
      set((state) => ({ ...state, loading: true, error: null }));
      const agent = await DynamicAgentAPI.createAgent(name, technologies);
      set((state) => ({ ...state, loading: false, agents: [...state.agents, agent] }));
      return true;
    } catch (error) {
      set((state) => ({ ...state, loading: false, error: error as Error }));
      return false;
    }
  },

  async updateAgent(id: string, updates: Partial<DynamicAgent>): Promise<boolean> {
    try {
      set((state) => ({ ...state, loading: true, error: null }));
      const updatedAgent = await DynamicAgentAPI.updateAgent(id, updates);
      set((state) => ({
        ...state,
        loading: false,
        agents: state.agents.map((agent) =>
          agent.id === id ? { ...agent, ...updatedAgent } : agent
        ),
      }));
      return true;
    } catch (error) {
      set((state) => ({ ...state, loading: false, error: error as Error }));
      return false;
    }
  },

  async deleteAgent(id: string): Promise<void> {
    try {
      set((state) => ({ ...state, loading: true, error: null }));
      await DynamicAgentAPI.deleteAgent(id);
      set((state) => ({
        ...state,
        loading: false,
        agents: state.agents.filter((agent) => agent.id !== id),
      }));
    } catch (error) {
      set((state) => ({ ...state, loading: false, error: error as Error }));
      throw error;
    }
  },

  async analyzeStack(technologies: string[]): Promise<TechAnalysisResult> {
    try {
      set((state) => ({ ...state, loading: true, error: null }));
      const result = await DynamicAgentAPI.analyzeStack(technologies);
      set((state) => ({ ...state, loading: false }));
      return result;
    } catch (error) {
      set((state) => ({ ...state, loading: false, error: error as Error }));
      throw error;
    }
  },
}));