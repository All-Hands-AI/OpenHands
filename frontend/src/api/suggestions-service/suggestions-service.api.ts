import { RepositoryTaskGroup } from "#/components/features/home/tasks/task.types";
import { openHands } from "../open-hands-axios";

export class SuggestionsService {
  static async getSuggestedTasks(): Promise<RepositoryTaskGroup[]> {
    const { data } = await openHands.get<RepositoryTaskGroup[]>("/api/tasks");
    return data;
  }
}
