
import { useEffect, useCallback } from 'react';
import { useDynamicAgentStore } from '../state/dynamic-agents';
import type { DynamicAgent } from '~/types/agents';

export function useDynamicAgents() {
  const {
    agents,
    loading,
    error,
    loadAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    analyzeStack
  } = useDynamicAgentStore();

  useEffect(() => {
    loadAgents();
    
    // Set up polling for agent updates
    const interval = setInterval(loadAgents, 5000);
    return () => clearInterval(interval);
  }, [loadAgents]);

  const handleCreateAgent = useCallback(async (
    name: string,
    technologies: string[]
  ) => {
    try {
      await createAgent(name, technologies);
      return true;
    } catch (error) {
      console.error('Failed to create agent:', error);
      return false;
    }
  }, [createAgent]);

  const handleUpdateAgent = useCallback(async (
    id: string,
    updates: Partial<DynamicAgent>
  ) => {
    try {
      await updateAgent(id, updates);
      return true;
    } catch (error) {
      console.error('Failed to update agent:', error);
      return false;
    }
  }, [updateAgent]);

  const handleDeleteAgent = useCallback(async (id: string) => {
    try {
      await deleteAgent(id);
      return true;
    } catch (error) {
      console.error('Failed to delete agent:', error);
      return false;
    }
  }, [deleteAgent]);

  return {
    agents,
    loading,
    error,
    createAgent: handleCreateAgent,
    updateAgent: handleUpdateAgent,
    deleteAgent: handleDeleteAgent,
    analyzeStack
  };
}
