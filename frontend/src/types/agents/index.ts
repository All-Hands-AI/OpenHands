export interface TechCategory {
  name: string;
  type: 'library' | 'framework' | 'language' | 'tool';
}

export interface TechAnalysisResult {
  completeness: number;
  compatibility: number;
  confidence: number;
  missingComponents: TechCategory[];
  recommendations: string[];
}

export interface AgentMetrics {
  // TODO: Add metrics
}

export interface TechInfo {
  name: string;
  version?: string;
  description?: string;
}

export interface AgentRequirements {
  minMemory?: string;
  recommendedCpu?: string;
}

export interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  technologies: TechInfo[];
  capabilities: string[];
  requirements?: AgentRequirements;
}

export interface DynamicAgent {
  id: string;
  name: string;
  type: string;
  technologies: string[];
  status: 'active' | 'inactive' | 'error';
  load: number;
  metrics?: AgentMetrics;
  lastActive: string;
  currentTask?: string;
}