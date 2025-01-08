
import { useState, useEffect } from 'react';
import { DynamicAgent } from '~/types/agents';
import { AgentFactoryService } from '~/services/agent-factory';

export function AgentList() {
  const [agents, setAgents] = useState<DynamicAgent[]>([]);
  const factory = AgentFactoryService.getInstance();

  useEffect(() => {
    const loadAgents = () => {
      const agentList = factory.listAgents();
      setAgents(agentList);
    };

    loadAgents();
    const interval = setInterval(loadAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Dynamic Agents</h2>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  );
}

function AgentCard({ agent }: { agent: DynamicAgent }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{agent.name}</h3>
        <span className={`px-2 py-1 rounded text-sm ${
          agent.status === 'active' ? 'bg-green-100 text-green-800' :
          agent.status === 'error' ? 'bg-red-100 text-red-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {agent.status}
        </span>
      </div>
      
      <div className="mt-2 space-y-2">
        <p className="text-sm text-gray-600">Type: {agent.type}</p>
        <div className="flex flex-wrap gap-1">
          {agent.technologies.map(tech => (
            <span key={tech} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
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
              className="h-full bg-blue-500 rounded"
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
}
