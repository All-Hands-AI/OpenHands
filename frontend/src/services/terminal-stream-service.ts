import { appendOutput } from "#/state/command-slice";
import store from "#/store";
import { processTerminalOutput } from "#/utils/terminal-output-processor";

interface TerminalStreamChunk {
  content: string;
  command: string;
  isComplete: boolean;
  commandId?: number;
  isTimeout?: boolean;
}

export class TerminalStreamService {
  static readonly END_OF_OUTPUT_INDICATOR = "<end_of_output>";

  private eventSource: EventSource | null = null;

  private isConnected: boolean = false;

  // Configuration for reconnection
  private reconnectAttempts: number = 0;

  private maxReconnectAttempts: number = 5;

  private reconnectDelay: number = 1000; // Start with 1 second delay

  // Track current command for first chunk detection
  private currentCommandId: number | null = null;

  constructor(private baseUrl: string) {}

  connect(): void {
    if (this.eventSource) {
      this.disconnect();
    }

    try {
      const url = `${this.baseUrl}/terminal-stream`;
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as TerminalStreamChunk;
          this.handleStreamChunk(data);
        } catch (error) {
          // console.error("Error parsing terminal stream data:", error);
        }
      };

      this.eventSource.onerror = () => {
        // console.error("Terminal stream error:", error);
        this.isConnected = false;
        this.eventSource?.close();
        this.eventSource = null;

        // Attempt to reconnect with exponential backoff
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts += 1;
            this.reconnectDelay *= 2; // Exponential backoff
            this.connect();
          }, this.reconnectDelay);
        }
      };
    } catch (error) {
      // console.error("Failed to connect to terminal stream:", error);
    }
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.isConnected = false;
    }
  }

  private handleStreamChunk(data: TerminalStreamChunk): void {
    const { content, command, isComplete, commandId, isTimeout } = data;

    // Check if this is a new command
    const isNewCommand = this.currentCommandId !== commandId;
    const isFirstChunk = isNewCommand;

    if (isNewCommand) {
      this.currentCommandId = commandId || null;
    }

    // Process the output with unified processing
    const processedOutput = processTerminalOutput(content, {
      isFirstChunk,
      removeCommandPrefix: isFirstChunk ? command : undefined,
    });

    // Handle completion
    if (isComplete) {
      this.currentCommandId = null;
      store.dispatch(
        appendOutput({
          content: isFirstChunk
            ? processedOutput
            : TerminalStreamService.END_OF_OUTPUT_INDICATOR,
          isPartial: false,
        }),
      );
      return;
    }

    // Handle timeout
    if (isTimeout) {
      store.dispatch(
        appendOutput({
          content: processedOutput,
          isPartial: false, // Timeout is considered final
        }),
      );
      return;
    }

    // Handle partial output
    if (processedOutput) {
      store.dispatch(
        appendOutput({
          content: processedOutput,
          isPartial: true,
        }),
      );
    }
  }

  isStreamConnected(): boolean {
    return this.isConnected;
  }
}

// Singleton instance
let terminalStreamService: TerminalStreamService | null = null;

export function getTerminalStreamService(
  baseUrl?: string,
): TerminalStreamService {
  if (!terminalStreamService && baseUrl) {
    terminalStreamService = new TerminalStreamService(baseUrl);
  }

  if (!terminalStreamService) {
    throw new Error("Terminal stream service not initialized");
  }

  return terminalStreamService;
}
