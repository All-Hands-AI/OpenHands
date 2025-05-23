import { openHands } from "../open-hands-axios";

export class MemoryService {
  static async getPrompt(
    conversationId: string,
    eventId: number,
  ): Promise<string> {
    const { data } = await openHands.get<string>(
      `/api/conversations/${conversationId}/remember_prompt`,
      {
        params: { event_id: eventId },
      },
    );
    return data;
  }
}
