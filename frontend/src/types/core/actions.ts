import { OpenHandsActionEvent } from "./base";
import { ActionSecurityRisk } from "#/state/security-analyzer-slice";

// Thoughts can be either a string (backward compatibility) or a dictionary
export type ThoughtsDict = {
  default: string;
  reasoning_content?: string;
};

export type Thoughts = string | ThoughtsDict;

// Utility function to extract the default thought from the Thoughts type
export function getDefaultThought(thoughts: Thoughts): string {
  if (typeof thoughts === "string") {
    return thoughts;
  }
  return thoughts.default || "";
}

// Utility function to extract the reasoning content from the Thoughts type
export function getReasoningContent(thoughts: Thoughts): string {
  if (typeof thoughts === "string") {
    return "";
  }
  return thoughts.reasoning_content || "";
}

export interface UserMessageAction extends OpenHandsActionEvent<"message"> {
  source: "user";
  args: {
    content: string;
    image_urls: string[];
    file_urls: string[];
  };
}

export interface SystemMessageAction extends OpenHandsActionEvent<"system"> {
  source: "agent" | "environment";
  args: {
    content: string;
    tools: Array<Record<string, unknown>> | null;
    openhands_version: string | null;
    agent_class: string | null;
  };
}

export interface CommandAction extends OpenHandsActionEvent<"run"> {
  source: "agent" | "user";
  args: {
    command: string;
    security_risk: ActionSecurityRisk;
    confirmation_state: "confirmed" | "rejected" | "awaiting_confirmation";
    thought: Thoughts;
    hidden?: boolean;
  };
}

export interface AssistantMessageAction
  extends OpenHandsActionEvent<"message"> {
  source: "agent";
  args: {
    thought: Thoughts;
    image_urls: string[] | null;
    file_urls: string[];
    wait_for_response: boolean;
  };
}

export interface IPythonAction extends OpenHandsActionEvent<"run_ipython"> {
  source: "agent";
  args: {
    code: string;
    security_risk: ActionSecurityRisk;
    confirmation_state: "confirmed" | "rejected" | "awaiting_confirmation";
    kernel_init_code: string;
    thought: Thoughts;
  };
}

export interface ThinkAction extends OpenHandsActionEvent<"think"> {
  source: "agent";
  args: {
    thought: Thoughts;
  };
}

export interface FinishAction extends OpenHandsActionEvent<"finish"> {
  source: "agent";
  args: {
    final_thought: string;
    outputs: Record<string, unknown>;
    thought: Thoughts;
  };
}

export interface DelegateAction extends OpenHandsActionEvent<"delegate"> {
  source: "agent";
  timeout: number;
  args: {
    agent: "BrowsingAgent";
    inputs: Record<string, string>;
    thought: Thoughts;
  };
}

export interface BrowseAction extends OpenHandsActionEvent<"browse"> {
  source: "agent";
  args: {
    url: string;
    thought: Thoughts;
  };
}

export interface BrowseInteractiveAction
  extends OpenHandsActionEvent<"browse_interactive"> {
  source: "agent";
  timeout: number;
  args: {
    browser_actions: string;
    thought: Thoughts | null;
    browsergym_send_msg_to_user: string;
  };
}

export interface FileReadAction extends OpenHandsActionEvent<"read"> {
  source: "agent";
  args: {
    path: string;
    thought: Thoughts;
    security_risk: ActionSecurityRisk | null;
    impl_source?: string;
    view_range?: number[] | null;
  };
}

export interface FileWriteAction extends OpenHandsActionEvent<"write"> {
  source: "agent";
  args: {
    path: string;
    content: string;
    thought: Thoughts;
  };
}

export interface FileEditAction extends OpenHandsActionEvent<"edit"> {
  source: "agent";
  args: {
    path: string;
    command?: string;
    file_text?: string | null;
    view_range?: number[] | null;
    old_str?: string | null;
    new_str?: string | null;
    insert_line?: number | null;
    content?: string;
    start?: number;
    end?: number;
    thought: Thoughts;
    security_risk: ActionSecurityRisk | null;
    impl_source?: string;
  };
}

export interface RejectAction extends OpenHandsActionEvent<"reject"> {
  source: "agent";
  args: {
    thought: Thoughts;
  };
}

export interface RecallAction extends OpenHandsActionEvent<"recall"> {
  source: "agent";
  args: {
    recall_type: "workspace_context" | "knowledge";
    query: string;
    thought: Thoughts;
  };
}

export interface MCPAction extends OpenHandsActionEvent<"call_tool_mcp"> {
  source: "agent";
  args: {
    name: string;
    arguments: Record<string, unknown>;
    thought?: Thoughts;
  };
}

export type OpenHandsAction =
  | UserMessageAction
  | AssistantMessageAction
  | SystemMessageAction
  | CommandAction
  | IPythonAction
  | ThinkAction
  | FinishAction
  | DelegateAction
  | BrowseAction
  | BrowseInteractiveAction
  | FileReadAction
  | FileEditAction
  | FileWriteAction
  | RejectAction
  | RecallAction
  | MCPAction;
