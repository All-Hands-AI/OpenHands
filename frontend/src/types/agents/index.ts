
export interface TechInfo {
  name: string;
  type: string;
  category: string;
  popularity?: number;
  lastUpdated?: string;
  description?: string;
  url?: string;
  version?: string;
}

export interface TechAnalysisResult {
  completeness: number;
  compatibility: number;
  missingComponents: string[];
  recommendations: string[];
}

export interface AgentTemplate {
  name: string;
  type: string;
  technologies: string[];
  capabilities: string[];
  description: string;
  requirements?: {
    minMemory?: string;
    recommendedCpu?: string;
    dependencies?: string[];
  };
}

export interface DynamicAgent {
  id: string;
  name: string;
  type: string;
  technologies: string[];
  status: 'active' | 'inactive' | 'error';
  currentTask?: string;
  load: number;
  lastActive?: string;
  metrics?: Record<string, number | string>;
}
