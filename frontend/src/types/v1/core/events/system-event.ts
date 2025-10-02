import { TextContent } from "../base/common";
import { BaseEvent, ChatCompletionToolParam } from "../base/event";

// System prompt event interface
export interface SystemPromptEvent extends BaseEvent {
  /**
   * The source is always "agent" for system prompt events
   */
  source: "agent";

  /**
   * The system prompt text
   */
  system_prompt: TextContent;

  /**
   * List of tools in OpenAI tool format
   */
  tools: ChatCompletionToolParam[];
}
