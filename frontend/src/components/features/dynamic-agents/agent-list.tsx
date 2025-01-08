import { useCallback, useMemo } from 'react';
import { useDynamicAgents } from '~/hooks/use-dynamic-agents';
import { LoadingSpinner } from '~/components/shared/loading-spinner';
import { ErrorToast } from '~/components/shared/error-toast';
import type { DynamicAgent } from '~/types/agents';

interface AgentCardProps {
  agent: DynamicAgent;
}

function getStatusClass(status: DynamicAgent['status']) {
  switch (status) {
    case 'active': return 'bg-green-100 text-green-800';
    case 'inactive': return 'bg-gray-100 text-gray-800';
    case 'error': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

function AgentCard({ agent }: AgentCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">{agent.name}</h3>
        <span className={getStatusClass(agent.status)}>{agent.status}</span>
      </div>
      <div className="mt-2">
        <p className="text-sm text-gray-600">Type: {agent.type}</p>
        <p className="text-sm text-gray-600">Load: {(agent.load * 100).toFixed(1)}%</p>
        {agent.currentTask && (
          <p className="text-sm text-gray-600">
            Current Task: {agent.currentTask}
          </p>
        )}
      </div>
    </div>
  );
}

export function AgentList() {
  const { agents, loading, error } = useDynamicAgents();
  
  const renderAgent = useCallback((agent: DynamicAgent) => (
    <AgentCard
      key={agent.id}
      agent={agent}
    />
  ), []);

  const sortedAgents = useMemo(() => 
    [...agents].sort((a, b) => b.load - a.load),
    [agents]
  );
  
  if (loading) return <LoadingSpinner size="small" />;
  if (error) return <ErrorToast id="agent-list-error" error={error.toString()} />;
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Dynamic Agents</h2>
        <button
          type="button"
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          onClick={() => {
            // TODO: Implement refresh functionality
          }}
        >
          Refresh
        </button>
      </div>
      <div className="space-y-4">
        {sortedAgents.map(renderAgent)}
      </div>
    </div>
  );
}