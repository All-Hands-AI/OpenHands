import { appendOutput } from "#/state/command-slice";
import store from "#/store";
import { parseTerminalOutput } from "#/utils/parse-terminal-output";

interface TerminalStreamChunk {
  content: string;
  metadata: {
    command: string;
    is_complete: boolean;
    exit_code?: number;
    is_timeout?: boolean;
    timeout_type?: string;
    command_id?: string;
  };
}

export class TerminalStreamService {
  static readonly END_OF_OUTPUT_INDICATOR = "<end_of_output>";

  private eventSource: EventSource | null = null;

  private isConnected: boolean = false;

  private reconnectAttempts: number = 0;

  private maxReconnectAttempts: number = 5;

  private reconnectDelay: number = 1000; // Start with 1 second delay

  private currentCommandId: string | null = null;

  private accumulatedOutput: string = "";

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
          console.error("Error parsing terminal stream data:", error);
        }
      };

      this.eventSource.onerror = (error) => {
        console.error("Terminal stream error:", error);
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
      console.error("Failed to connect to terminal stream:", error);
    }
  }

  disconnect(): void {
    console.log("Disconnecting from terminal stream...");
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.isConnected = false;
    }
  }

  private handleStreamChunk(data: TerminalStreamChunk): void {
    const { content, metadata } = data;

    // If this is a new command, reset the accumulated output
    if (this.currentCommandId !== metadata.command_id) {
      this.currentCommandId = metadata.command_id || null;
      this.accumulatedOutput = "";
    }

    // Add the new content to the accumulated output
    this.accumulatedOutput += content;

    // If this is the final chunk, reset the command ID and skip the full output
    if (metadata.is_complete) {
      this.currentCommandId = null;
      store.dispatch(
        appendOutput({
          content: TerminalStreamService.END_OF_OUTPUT_INDICATOR,
          isPartial: false,
        }),
      );
      return;
    }
    // Process the output
    const processedOutput = parseTerminalOutput(
      content.replaceAll("\n", "\r\n"),
    );

    store.dispatch(
      appendOutput({
        content: processedOutput,
        isPartial: true,
      }),
    );
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
