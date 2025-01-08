
import { useState, useEffect } from 'react';
import { AgentTemplate } from '~/types/agents';
import { AgentFactoryService } from '~/services/agent-factory';

export function TemplateList() {
  const [templates, setTemplates] = useState<AgentTemplate[]>([]);
  const factory = AgentFactoryService.getInstance();

  useEffect(() => {
    setTemplates(factory.listTemplates());
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Agent Templates</h2>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
        {templates.map(template => (
          <TemplateCard key={template.name} template={template} />
        ))}
      </div>
    </div>
  );
}

function TemplateCard({ template }: { template: AgentTemplate }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium">{template.name}</h3>
      <p className="text-sm text-gray-600 mt-1">{template.description}</p>
      
      <div className="mt-4 space-y-2">
        <div>
          <h4 className="text-sm font-medium text-gray-700">Technologies</h4>
          <div className="flex flex-wrap gap-1 mt-1">
            {template.technologies.map(tech => (
              <span key={tech} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                {tech}
              </span>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium text-gray-700">Capabilities</h4>
          <div className="flex flex-wrap gap-1 mt-1">
            {template.capabilities.map(cap => (
              <span key={cap} className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                {cap}
              </span>
            ))}
          </div>
        </div>

        {template.requirements && (
          <div>
            <h4 className="text-sm font-medium text-gray-700">Requirements</h4>
            <ul className="text-sm text-gray-600 list-disc list-inside mt-1">
              {template.requirements.minMemory && (
                <li>Min Memory: {template.requirements.minMemory}</li>
              )}
              {template.requirements.recommendedCpu && (
                <li>CPU: {template.requirements.recommendedCpu}</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
