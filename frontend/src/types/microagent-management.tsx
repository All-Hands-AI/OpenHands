export type TabType = "personal" | "repositories" | "organizations";

export interface RepositoryMicroagent {
  name: string;
  type: "repo" | "knowledge";
  content: string;
  triggers: string[];
  inputs: string[];
  tools: string[];
  created_at: string;
  git_provider: string;
}

export interface MicroagentFormData {
  query: string;
  triggers: string[];
}
