
import { useState } from 'react';
import { useTechAnalyzer } from './tech-analyzer';
import { AgentFactoryService } from '~/services/agent-factory';
import type { TechAnalysisResult } from '~/types/agents';

export function AgentCreator() {
  const [name, setName] = useState('');
  const [technologies, setTechnologies] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const { analyzeStack, analyzing } = useTechAnalyzer();
  const factory = AgentFactoryService.getInstance();

  const handleCreate = async () => {
    if (!name || technologies.length === 0) return;
    
    setCreating(true);
    try {
      const analysis = await analyzeStack(technologies);
      const agent = await factory.createAgent(name, technologies, analysis);
      setName('');
      setTechnologies([]);
      // Trigger success notification
    } catch (error) {
      // Handle error
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Create Dynamic Agent</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Agent Name
          </label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Technologies
          </label>
          <div className="mt-1 flex flex-wrap gap-2">
            {technologies.map(tech => (
              <span
                key={tech}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {tech}
                <button
                  type="button"
                  onClick={() => setTechnologies(technologies.filter(t => t !== tech))}
                  className="ml-1 text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <input
            type="text"
            placeholder="Add technology..."
            onKeyDown={e => {
              if (e.key === 'Enter' && e.currentTarget.value) {
                setTechnologies([...technologies, e.currentTarget.value]);
                e.currentTarget.value = '';
              }
            }}
            className="mt-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <button
          onClick={handleCreate}
          disabled={creating || analyzing || !name || technologies.length === 0}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400"
        >
          {creating ? 'Creating...' : 'Create Agent'}
        </button>
      </div>
    </div>
  );
}
