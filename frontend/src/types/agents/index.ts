
export interface TechInfo {
  name: string;
  type: TechType;
  category: TechCategory;
  popularity: number;
  lastUpdated: string;
  description?: string;
  url?: string;
  version?: string;
}

export type TechType = 
  | 'language'
  | 'framework'
  | 'library'
  | 'database'
  | 'tool'
  | 'platform'
  | 'service';

export type TechCategory = 
  | 'frontend'
  | 'backend'
  | 'database'
  | 'devops'
  | 'testing'
  | 'security'
  | 'analytics';

export interface TechAnalysisResult {
  completeness: number;
  compatibility: number;
  missingComponents: TechCategory[];
  recommendations: string[];
  confidence: number;
}

export interface AgentMetrics {
  requestsHandled?: number;
  avgResponseTime?: number;
  errorRate?: number;
  memoryUsage?: number;
  cpuUsage?: number;
}

export interface DynamicAgent {
  id: string;
  name: string;
  type: string;
  technologies: string[];
  status: AgentStatus;
  currentTask?: string;
  load: number;
  lastActive: string;
  metrics?: AgentMetrics;
}

export type AgentStatus = 'active' | 'inactive' | 'error' | 'paused';

export interface AgentTemplate {
  name: string;
  type: string;
  technologies: string[];
  capabilities: string[];
  description: string;
  requirements: {
    minMemory?: string;
    recommendedCpu?: string;
    dependencies?: string[];
  };
}
