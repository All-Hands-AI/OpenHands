import { SuggestedTask } from "#/components/features/home/tasks/task.types";
import { openHands } from "../open-hands-axios";

export class SuggestionsService {
  static async getSuggestedTasks(): Promise<SuggestedTask[]> {
    const { data } = await openHands.get("/api/tasks");
    return data;
  }
}
