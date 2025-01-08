import { useState } from 'react';
import { AgentFactoryService } from '~/services/agent-factory';
import { useTechAnalyzer } from './tech-analyzer';
import type { TechAnalysisResult } from '~/types/agents';

export function AgentCreator() {
  const [name, setName] = useState('');
  const [technologies, setTechnologies] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<TechAnalysisResult | null>(null);
  const { analyze, loading, error } = useTechAnalyzer();

  const handleAnalyze = async () => {
    try {
      const result = await analyze(technologies);
      setAnalysis(result);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleCreate = async () => {
    try {
      const service = AgentFactoryService.getInstance();
      await service.createAgent(name, technologies);
      setName('');
      setTechnologies([]);
      setAnalysis(null);
    } catch (err) {
      // TODO: Handle error
      console.error(err);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Agent Name
        </label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div>
        <label htmlFor="technologies" className="block text-sm font-medium text-gray-700">
          Technologies (comma-separated)
        </label>
        <input
          type="text"
          id="technologies"
          value={technologies.join(', ')}
          onChange={(e) => setTechnologies(e.target.value.split(',').map(t => t.trim()))}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="flex space-x-4">
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>

        <button
          type="button"
          onClick={handleCreate}
          disabled={!analysis || loading}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
        >
          Create Agent
        </button>
      </div>

      {error && (
        <div className="text-red-600">
          {error.message}
        </div>
      )}

      {analysis && (
        <div className="mt-4 p-4 bg-gray-50 rounded">
          <h3 className="text-lg font-medium">Analysis Results</h3>
          <dl className="mt-2 space-y-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Completeness</dt>
              <dd className="text-sm text-gray-900">{(analysis.completeness * 100).toFixed(1)}%</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Compatibility</dt>
              <dd className="text-sm text-gray-900">{(analysis.compatibility * 100).toFixed(1)}%</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Confidence</dt>
              <dd className="text-sm text-gray-900">{(analysis.confidence * 100).toFixed(1)}%</dd>
            </div>
            {analysis.missingComponents.length > 0 && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Missing Components</dt>
                <dd className="text-sm text-gray-900">
                  {analysis.missingComponents.map(comp => comp.name).join(', ')}
                </dd>
              </div>
            )}
            {analysis.recommendations.length > 0 && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Recommendations</dt>
                <dd className="text-sm text-gray-900">
                  <ul className="list-disc list-inside">
                    {analysis.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}