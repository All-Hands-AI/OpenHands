import {
  AppConversationStartRequest,
  AppConversationStartTask,
} from "../open-hands.types";

class AppConversationServiceCallback {
  /**
   * Start an app conversation with streaming updates using callback pattern
   * This approach avoids the no-await-in-loop ESLint warning
   * @param request The conversation start request
   * @param onProgress Callback function called for each progress update
   * @param onComplete Callback function called when streaming is complete
   * @param onError Callback function called when an error occurs
   * @returns Promise that resolves when the stream starts (not when it completes)
   */
  static async streamStartAppConversation(
    request: AppConversationStartRequest,
    onProgress: (task: AppConversationStartTask) => void,
    onComplete: (allTasks: AppConversationStartTask[]) => void,
    onError: (error: Error) => void,
  ): Promise<void> {
    const baseURL = `${window.location.protocol}//${
      import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host
    }`;
    const url = `${baseURL}/api/v1/app-conversations/stream-start`;

    try {
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
      const allTasks: AppConversationStartTask[] = [];

      const processStream = async (): Promise<void> => {
        try {
          const { done, value } = await reader.read();

          if (done) {
            // Process any remaining data in buffer
            if (buffer.trim()) {
              const trimmedBuffer = buffer.trim();
              if (trimmedBuffer !== "[" && trimmedBuffer !== "]") {
                const cleanBuffer = trimmedBuffer.replace(/,$/, "");
                if (cleanBuffer) {
                  try {
                    const task: AppConversationStartTask =
                      JSON.parse(cleanBuffer);
                    allTasks.push(task);
                    onProgress(task);
                  } catch (error) {
                    // eslint-disable-next-line no-console
                    console.warn(
                      "Failed to parse final JSON:",
                      cleanBuffer,
                      error,
                    );
                  }
                }
              }
            }
            onComplete(allTasks);
            return;
          }

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
                  allTasks.push(task);
                  onProgress(task);
                } catch (error) {
                  // eslint-disable-next-line no-console
                  console.warn("Failed to parse JSON line:", cleanLine, error);
                }
              }
            }
          }

          // Continue processing the stream
          processStream();
        } catch (error) {
          reader.releaseLock();
          onError(error instanceof Error ? error : new Error(String(error)));
        }
      };

      // Start processing the stream
      processStream();
    } catch (error) {
      onError(error instanceof Error ? error : new Error(String(error)));
    }
  }
}

export default AppConversationServiceCallback;
