export interface ActionMessage {
  id: number;

  // Either 'agent' or 'user'
  source: "agent" | "user";

  // The action to be taken
  action: string;

  // The type of action
  type: string;

  // The arguments for the action
  args: Record<string, unknown>;

  // A friendly message that can be put in the chat log
  message: string;

  // The timestamp of the message
  timestamp: string;

  // LLM metrics information
  llm_metrics?: {
    accumulated_cost: number;
  };

  // Tool call metadata
  tool_call_metadata?: {
    model_response?: {
      usage: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
      };
    };
  };
}

export interface ObservationMessage {
  // The type of observation
  observation: string;

  // The observation type for the switch statement
  type: string;

  id: number;
  cause: number;

  // The observed data
  content: string;

  extras: {
    metadata: Record<string, unknown>;
    error_id?: string;
    observation_type?: string;
    agent_state?: unknown;
    command?: string;
    hidden?: boolean;
    name?: string;
    args?: unknown;
    impl_source?: string;
    path?: string;
    diff?: string;
    content?: string;
    url?: string;
    title?: string;
    screenshot?: string;
    error?: boolean;
    open_page_urls?: string[];
    active_page_index?: number;
    dom_object?: Record<string, unknown>;
    axtree_object?: Record<string, unknown>;
    extra_element_properties?: Record<string, unknown>;
    last_browser_action?: string;
    last_browser_action_error?: unknown;
    focused_element_bid?: string;
    query?: string;
    results?: unknown[];
    [key: string]: unknown;
  };

  // A friendly message that can be put in the chat log
  message: string;

  // The timestamp of the message
  timestamp: string;
}

export interface StatusMessage {
  status_update?: boolean;
  type: "success" | "error" | "info" | "warning";
  id: string;
  message: string;
}
