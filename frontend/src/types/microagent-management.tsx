import { Conversation } from "#/api/open-hands.types";

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
  path: string;
}

export interface IMicroagentItem {
  microagent?: RepositoryMicroagent;
  conversation?: Conversation;
}

export interface MicroagentFormData {
  query: string;
  triggers: string[];
  selectedBranch: string;
  microagentPath: string;
}

export interface LearnThisRepoFormData {
  query: string;
  selectedBranch: string;
}
