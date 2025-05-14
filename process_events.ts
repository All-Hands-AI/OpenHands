import { Event, Action, Observation, Message, TextContent, ImageContent, AgentConfig } from './types';
import { logger } from './logger';
import { truncateContent } from './utils';
import { PromptManager } from './prompt';
import {
  AgentDelegateAction,
  AgentThinkAction,
  AgentFinishAction,
  IPythonRunCellAction,
  FileEditAction,
  FileReadAction,
  BrowseInteractiveAction,
  BrowseURLAction,
  McpAction,
  A2AListRemoteAgentsAction,
  A2ASendTaskAction,
  CmdRunAction,
  MessageAction
} from './types';

export class ConversationMemory {
  private agentConfig: AgentConfig;
  private promptManager: PromptManager;

  constructor(config: AgentConfig, promptManager: PromptManager) {
    this.agentConfig = config;
    this.promptManager = promptManager;
  }

  /**
   * Process state history into a list of messages for the LLM.
   * Ensures that tool call actions are processed correctly in function calling mode.
   *
   * @param condensedHistory - The condensed history of events to convert
   * @param initialMessages - The initial messages to include in the conversation
   * @param maxMessageChars - The maximum number of characters in the content of an event
   * @param visionIsActive - Whether vision is active in the LLM
   * @returns A list of processed messages for the LLM
   */
  processEvents(
    condensedHistory: Event[],
    initialMessages: Message[],
    maxMessageChars?: number,
    visionIsActive: boolean = false
  ): Message[] {
    const events = condensedHistory;

    // Log visual browsing status
    logger.debug(`Visual browsing: ${this.agentConfig.enableSomVisualBrowsing}`);

    // Process special events first (system prompts, etc.)
    let messages = [...initialMessages];

    // Process regular events
    const pendingToolCallActionMessages: Record<string, Message> = {};
    const toolCallIdToMessage: Record<string, Message> = {};

    for (let i = 0; i < events.length; i++) {
      const event = events[i];
      let messagesToAdd: Message[] = [];

      // Create a regular message from an event
      if (event instanceof Action) {
        messagesToAdd = this._processAction(
          event,
          pendingToolCallActionMessages,
          visionIsActive
        );
      } else if (event instanceof Observation) {
        messagesToAdd = this._processObservation(
          event,
          toolCallIdToMessage,
          maxMessageChars,
          visionIsActive,
          this.agentConfig.enableSomVisualBrowsing,
          i,
          events
        );
      } else {
        throw new Error(`Unknown event type: ${typeof event}`);
      }

      // Check pending tool call action messages and see if they are complete
      const responseIdsToRemove: string[] = [];

      for (const [responseId, pendingMessage] of Object.entries(pendingToolCallActionMessages)) {
        if (!pendingMessage.toolCalls) {
          throw new Error(
            `Tool calls should NOT be undefined when function calling is enabled & the message is considered pending tool call. Pending message: ${JSON.stringify(pendingMessage)}`
          );
        }

        if (pendingMessage.toolCalls.every(toolCall => toolCall.id in toolCallIdToMessage)) {
          // If complete:
          // 1. Add the message that initiated the tool calls
          messagesToAdd.push(pendingMessage);

          // 2. Add the tool calls results
          for (const toolCall of pendingMessage.toolCalls) {
            messagesToAdd.push(toolCallIdToMessage[toolCall.id]);
            delete toolCallIdToMessage[toolCall.id];
          }

          responseIdsToRemove.push(responseId);
        }
      }

      // Cleanup the processed pending tool messages
      for (const responseId of responseIdsToRemove) {
        delete pendingToolCallActionMessages[responseId];
      }

      messages = [...messages, ...messagesToAdd];
    }

    // Filter out unmatched tool calls
    messages = Array.from(this._filterUnmatchedToolCalls(messages));

    return messages;
  }

  /**
   * Converts an action into a message format that can be sent to the LLM.
   *
   * This method handles different types of actions and formats them appropriately:
   * 1. For tool-based actions (AgentDelegate, CmdRun, IPythonRunCell, FileEdit) and agent-sourced AgentFinish:
   *    - In function calling mode: Stores the LLM's response in pendingToolCallActionMessages
   *    - In non-function calling mode: Creates a message with the action string
   * 2. For MessageActions: Creates a message with the text content and optional image content
   */
  private _processAction(
    action: Action,
    pendingToolCallActionMessages: Record<string, Message>,
    visionIsActive: boolean = false
  ): Message[] {
    // Handle tool-based actions
    if (
      action instanceof AgentDelegateAction ||
      action instanceof AgentThinkAction ||
      action instanceof IPythonRunCellAction ||
      action instanceof FileEditAction ||
      action instanceof FileReadAction ||
      action instanceof BrowseInteractiveAction ||
      action instanceof BrowseURLAction ||
      action instanceof McpAction ||
      action instanceof A2AListRemoteAgentsAction ||
      action instanceof A2ASendTaskAction ||
      (action instanceof CmdRunAction && action.source === 'agent')
    ) {
      const toolMetadata = action.toolCallMetadata;
      if (!toolMetadata) {
        throw new Error(
          'Tool call metadata should NOT be undefined when function calling is enabled. Action: ' +
          JSON.stringify(action)
        );
      }

      const llmResponse = toolMetadata.modelResponse;
      const assistantMsg = llmResponse.choices[0].message;

      logger.debug(
        `Tool calls type: ${typeof assistantMsg.toolCalls}, value: ${JSON.stringify(assistantMsg.toolCalls)}`
      );

      // Add the LLM message (assistant) that initiated the tool calls
      pendingToolCallActionMessages[llmResponse.id] = {
        role: assistantMsg.role || 'assistant',
        content: assistantMsg.content ? [{ type: 'text', text: assistantMsg.content }] : [],
        toolCalls: assistantMsg.toolCalls,
      };

      return [];
    }
    else if (action instanceof AgentFinishAction) {
      const role = action.source === 'user' ? 'user' : 'assistant';

      // when agent finishes, it has toolMetadata
      // which has already been executed, and it doesn't have a response
      // when the user finishes (/exit), we don't have toolMetadata
      const toolMetadata = action.toolCallMetadata;
      if (toolMetadata) {
        // take the response message from the tool call
        const assistantMsg = toolMetadata.modelResponse.choices[0].message;
        const content = assistantMsg.content || '';

        // save content if any, to thought
        if (action.thought) {
          if (action.thought !== content) {
            action.thought += '\n' + content;
          }
        } else {
          action.thought = content;
        }

        // remove the tool call metadata
        action.toolCallMetadata = null;
      }

      if (!['user', 'system', 'assistant', 'tool'].includes(role)) {
        throw new Error(`Invalid role: ${role}`);
      }

      return [
        {
          role,
          content: [{ type: 'text', text: action.thought }],
        },
      ];
    }
    else if (action instanceof MessageAction) {
      const role = action.source === 'user' ? 'user' : 'assistant';
      const content: Array<TextContent | ImageContent> = [
        { type: 'text', text: action.content || '' }
      ];

      if (visionIsActive && action.imageUrls && action.imageUrls.length > 0) {
        content.push({ type: 'image', imageUrls: action.imageUrls });
      }

      if (!['user', 'system', 'assistant', 'tool'].includes(role)) {
        throw new Error(`Invalid role: ${role}`);
      }

      return [
        {
          role,
          content,
        },
      ];
    }
    else if (action instanceof CmdRunAction && action.source === 'user') {
      const content = [
        { type: 'text', text: `User executed the command:\n${action.command}` }
      ];

      return [
        {
          role: 'user',
          content,
        },
      ];
    }

    return [];
  }

  // Additional methods should be implemented here:
  // - _processObservation
  // etc.

  /**
   * Filter out tool calls that don't have matching tool responses and vice versa.
   */
  private *_filterUnmatchedToolCalls(messages: Message[]): Generator<Message> {
    const toolCallIds = new Set(
      messages
        .filter(msg => msg.role === 'assistant' && msg.toolCalls)
        .flatMap(msg => msg.toolCalls || [])
        .filter(toolCall => toolCall.id)
        .map(toolCall => toolCall.id)
    );

    const toolResponseIds = new Set(
      messages
        .filter(msg => msg.role === 'tool' && msg.toolCallId)
        .map(msg => msg.toolCallId)
    );

    for (const message of messages) {
      // Remove tool messages with no matching assistant tool call
      if (message.role === 'tool' && message.toolCallId) {
        if (toolCallIds.has(message.toolCallId)) {
          yield message;
        }
      }
      // Remove assistant tool calls with no matching tool response
      else if (message.role === 'assistant' && message.toolCalls && message.toolCalls.length > 0) {
        const allToolCallsMatch = message.toolCalls.every(
          toolCall => toolResponseIds.has(toolCall.id)
        );

        if (allToolCallsMatch) {
          yield message;
        } else {
          const matchedToolCalls = message.toolCalls.filter(
            toolCall => toolResponseIds.has(toolCall.id)
          );

          if (matchedToolCalls.length > 0) {
            // Keep an updated message if there are tools calls left
            yield {
              ...message,
              toolCalls: matchedToolCalls
            };
          }
        }
      } else {
        // Any other case is kept
        yield message;
      }
    }
  }
}
