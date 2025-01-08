
import React, { useCallback, useMemo } from 'react';
import { useDynamicAgents } from '~/hooks/use-dynamic-agents';
import { LoadingSpinner } from '~/components/shared/loading-spinner';
import { ErrorToast } from '~/components/shared/error-toast';
import type { DynamicAgent } from '~/types/agents';

export function AgentList() {
  const { agents, loading, error, refreshAgents } = useDynamicAgents();
  
  const handleRefresh = useCallback(() => {
    refreshAgents();
  }, [refreshAgents]);
  
  const sortedAgents = useMemo(() => 
    [...agents].sort((a, b) => b.load - a.load),
    [agents]
  );
  
  const renderAgent = useCallback((agent: DynamicAgent) => (
    <AgentCard 
      key={agent.id} 
      agent={agent}
    />
  ), []);
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorToast error={error} />;
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Dynamic Agents</h2>
        <button
          onClick={handleRefresh}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Refresh
        </button>
      </div>
      
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {sortedAgents.map(renderAgent)}
      </div>
    </div>
  );
}

const AgentCard = React.memo(({ agent }: { agent: DynamicAgent }) => {
  const statusColor = useMemo(() => {
    switch (agent.status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }, [agent.status]);
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{agent.name}</h3>
        <span className={`px-2 py-1 rounded text-sm ${statusColor}`}>
          {agent.status}
        </span>
      </div>
      
      <div className="mt-2 space-y-2">
        <p className="text-sm text-gray-600">Type: {agent.type}</p>
        <div className="flex flex-wrap gap-1">
          {agent.technologies.map(tech => (
            <span 
              key={tech} 
              className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
            >
              {tech}
            </span>
          ))}
        </div>
        {agent.currentTask && (
          <p className="text-sm text-gray-600">
            Current Task: {agent.currentTask}
          </p>
        )}
        <div className="mt-2">
          <div className="h-2 bg-gray-200 rounded">
            <div
              className="h-full bg-blue-500 rounded transition-all duration-300"
              style={{ width: `${agent.load * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Load: {(agent.load * 100).toFixed(1)}%
          </p>
        </div>
      </div>
    </div>
  );
});

AgentCard.displayName = 'AgentCard';
