export type ProjectStatus = "RUNNING" | "STOPPED";

export interface Conversation {
  conversation_id: string;
  title: string;
  selected_repository: string | null;
  last_updated_at: string;
  created_at: string;
  status: ProjectStatus;
}

export interface GetConversationsResponse {
  results: Conversation[];
  next_page_id: string | null;
}

export type UpdateConversationBody = Partial<
  Omit<Conversation, "conversation_id">
>;
