
import { DynamicAgent, AgentTemplate, TechAnalysisResult } from '~/types/agents';

export class AgentFactoryService {
  private static instance: AgentFactoryService;
  private agents: Map<string, DynamicAgent>;
  private templates: Map<string, AgentTemplate>;

  private constructor() {
    this.agents = new Map();
    this.templates = new Map();
  }

  static getInstance(): AgentFactoryService {
    if (!AgentFactoryService.instance) {
      AgentFactoryService.instance = new AgentFactoryService();
    }
    return AgentFactoryService.instance;
  }

  async createAgent(
    name: string,
    technologies: string[],
    analysis: TechAnalysisResult
  ): Promise<DynamicAgent> {
    const agent: DynamicAgent = {
      id: crypto.randomUUID(),
      name,
      type: this.determineAgentType(technologies),
      technologies,
      status: 'inactive',
      load: 0,
      metrics: {
        completeness: analysis.completeness,
        compatibility: analysis.compatibility
      }
    };

    this.agents.set(agent.id, agent);
    return agent;
  }

  private determineAgentType(technologies: string[]): string {
    // Implementation
    return 'general';
  }

  getAgent(id: string): DynamicAgent | undefined {
    return this.agents.get(id);
  }

  listAgents(): DynamicAgent[] {
    return Array.from(this.agents.values());
  }

  registerTemplate(template: AgentTemplate): void {
    this.templates.set(template.name, template);
  }

  getTemplate(name: string): AgentTemplate | undefined {
    return this.templates.get(name);
  }

  listTemplates(): AgentTemplate[] {
    return Array.from(this.templates.values());
  }
}
