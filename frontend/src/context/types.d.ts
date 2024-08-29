type AgentState =
  | "init"
  | "loading"
  | "running"
  | "awaiting_user_input"
  | "finished"
  | "paused"
  | "stopped"
  | "rejected"
  | "error"
  // user states (confirmation)
  | "awaiting_user_confirmation"
  | "user_confirmed"
  | "user_rejected";

interface Config {
  action: "initialize";
  args: {
    AGENT: string;
    CONFIRMATION_MODE: boolean;
    LANGUAGE: string;
    LLM_API_KEY: string;
    LLM_MODEL: string;
  };
}

interface AgentStateChange {
  id: number;
  message: string;
  source: "agent";
  timestamp: string;
  observation: "agent_state_changed";
  content: string;
  extras: {
    agent_state: AgentState;
  };
}

interface UserMessage {
  // if message is received from ws, it contains source and id fields
  id?: number;
  source?: "user";
  action: "message";
  args: {
    content: string;
    images_urls: string[];
  };
}

interface AssistantMessage {
  id: number;
  action: "message";
  message: string;
  source: "agent";
  timestamp: string; // ISO 8601
  args: {
    content: string;
    images_urls: string[] | null;
    wait_for_response: boolean;
  };
}

interface CommandAction {
  id: number;
  action: "run";
  message: string;
  source: "agent";
  timestamp: string;
  args: {
    command: string;
    is_confirmed: "confirmed" | "rejected" | "awaiting_confirmation";
    thought: string;
  };
}

interface CommandObservation {
  id: number;
  cause: number;
  observation: "run";
  message: string;
  content: string;
  source: "agent";
  timestamp: string;
  extras: {
    command: string;
    command_id: number;
    exit_code: number;
  };
}

interface IPythonAction {
  id: number;
  action: "run_ipython";
  message: string;
  source: "agent";
  timestamp: string;
  args: {
    code: string;
    is_confirmed: "confirmed" | "rejected" | "awaiting_confirmation";
    kernel_init_code: string;
    thought: string;
  };
}

interface IPythonObservation {
  id: number;
  cause: number;
  observation: "run_ipython";
  message: string;
  content: string;
  source: "agent";
  timestamp: string;
  extras: {
    code: string;
  };
}

interface FinishAction {
  id: number;
  message: string;
  source: "agent";
  timestamp: string;
  action: "finish";
  args: {
    outputs: Record<string, unknown>;
    thought: string;
  };
}

interface ErrorObservation {
  id: number;
  message: string;
  source: "agent";
  timestamp: string;
  observation: "error";
  content: string;
  extras: Record<string, unknown>;
}

interface DelegateAction {
  id: number;
  timestamp: string;
  source: "agent";
  message: string;
  action: "delegate";
  args: {
    agent: "BrowsingAgent";
    inputs: Record<string, string>;
    thought: string;
  };
  timeout: number;
}

interface DelegateObservation {
  id: number;
  timestamp: string;
  source: "agent";
  message: string;
  cause: number;
  observation: "delegate";
  content: string;
  extras: {
    outputs: Record<string, unknown>;
  };
}

interface BrowseAction {
  id: number;
  timestamp: string;
  source: "agent";
  message: string;
  action: "browse";
  args: {
    url: string;
    thought: string;
  };
}

interface BrowseInteractiveAction {
  id: number;
  timestamp: string;
  source: "agent";
  message: string;
  action: "browse_interactive";
  args: {
    browser_actions: string;
    thought: string | null;
    browsergym_send_msg_to_user: string;
  };
  timeout: number;
}

interface BrowseObservation {
  id: number;
  timestamp: string;
  source: "agent";
  message: string;
  cause: number;
  observation: "browse";
  content: string;
  extras: {
    url: string;
    screenshot: string;
    error: boolean;
    open_page_urls: string[];
    active_page_index: number;
    dom_object: Record<string, unknown>;
    axtree_object: Record<string, unknown>;
    extra_element_properties: Record<string, unknown>;
    last_browser_action: string;
    last_browser_action_error: unknown;
    focused_element_bid: string;
  };
}

interface RejectAction {
  id: number;
  timestamp: string;
  source: "agent";
  message: string;
  action: "reject";
  args: {
    thought: string;
  };
}

interface AddTaskAction {
  id: number;
  timestamp: string;
  source: "agent";
  message: string;
  action: "add_task";
  args: {
    parent: string;
    goal: string;
    subtasks: unknown[];
    thought: string;
  };
}

interface ModifyTaskAction {
  id: number;
  timestamp: string;
  source: "agent";
  message: string;
  action: "modify_task";
  args: {
    task_id: string;
    state: string;
    thought: string;
  };
}

type TrajectoryItem =
  | AgentStateChange
  | UserMessage
  | AssistantMessage
  | CommandAction
  | CommandObservation
  | IPythonAction
  | IPythonObservation
  | FinishAction
  | Config
  | ErrorObservation
  | DelegateAction
  | DelegateObservation
  | BrowseAction
  | BrowseInteractiveAction
  | BrowseObservation
  | RejectAction
  | AddTaskAction
  | ModifyTaskAction;
