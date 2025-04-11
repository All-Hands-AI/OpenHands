type SuggestedTaskType =
  | "MERGE_CONFLICTS"
  | "FAILING_CHECKS"
  | "UNRESOLVED_COMMENTS"
  | "OPEN_ISSUE"
  | "OPEN_PR";

export interface SuggestedTask {
  id: number;
  repo: string;
  title: string;
  type: SuggestedTaskType;
}

export interface SuggestedTaskGroup {
  title: string;
  tasks: SuggestedTask[];
}
