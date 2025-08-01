import { SuggestedTask } from "#/components/features/home/tasks/task.types";
import { openHands } from "../open-hands-axios";

/**
 * Utility function to check if the response data is an empty JSON object "{}"
 * @param data The response data to check
 * @returns true if the data is an empty object, false otherwise
 */
function isEmptyJsonResponse(data: unknown): boolean {
  return (
    typeof data === "object" &&
    data !== null &&
    !Array.isArray(data) &&
    Object.keys(data).length === 0
  );
}

export class SuggestionsService {
  static async getSuggestedTasks(): Promise<SuggestedTask[]> {
    const { data } = await openHands.get("/api/user/suggested-tasks");

    // Handle empty JSON response "{}" by returning empty array
    if (isEmptyJsonResponse(data)) {
      return [];
    }

    return data;
  }
}
