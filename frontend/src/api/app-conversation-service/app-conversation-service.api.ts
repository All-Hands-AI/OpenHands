import {
  AppConversationStartRequest,
  AppConversationStartTask,
} from "../open-hands.types";

class AppConversationService {
  /**
   * Start an app conversation with streaming updates
   * @param request The conversation start request
   * @returns AsyncGenerator that yields AppConversationStartTask updates
   */
  static async *streamStartAppConversation(
    request: AppConversationStartRequest,
  ): AsyncGenerator<AppConversationStartTask, void, unknown> {
    const baseURL = `${window.location.protocol}//${
      import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host
    }`;
    const url = `${baseURL}/api/v1/app-conversations/stream-start`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error("Response body is null");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        // eslint-disable-next-line no-await-in-loop -- Sequential reading from stream required
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // The API returns a JSON array that gets built incrementally
        // We need to parse individual JSON objects as they come in
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep the last incomplete line in buffer

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine && trimmedLine !== "[" && trimmedLine !== "]") {
            // Remove trailing comma if present
            const cleanLine = trimmedLine.replace(/,$/, "");
            if (cleanLine) {
              try {
                const task: AppConversationStartTask = JSON.parse(cleanLine);
                yield task;
              } catch (error) {
                console.warn("Failed to parse JSON line:", cleanLine, error);
              }
            }
          }
        }
      }

      // Process any remaining data in buffer
      if (buffer.trim()) {
        const trimmedBuffer = buffer.trim();
        if (trimmedBuffer !== "[" && trimmedBuffer !== "]") {
          const cleanBuffer = trimmedBuffer.replace(/,$/, "");
          if (cleanBuffer) {
            try {
              const task: AppConversationStartTask = JSON.parse(cleanBuffer);
              yield task;
            } catch (error) {
              console.warn("Failed to parse final JSON:", cleanBuffer, error);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}

export default AppConversationService;
