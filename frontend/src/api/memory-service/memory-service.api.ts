import { openHands } from "../open-hands-axios";

export class MemoryService {
  static async getPrompt(conversationId: string): Promise<string> {
    const { data } = await openHands.get<string>(
      `/api/memory/prompt/${conversationId}`,
    );
    return data;
  }
}
