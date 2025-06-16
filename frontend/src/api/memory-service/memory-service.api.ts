import { openHands } from "../open-hands-axios";

interface GetPromptResponse {
  status: string;
  prompt: string;
}

export class MemoryService {
  static async getPrompt(
    conversationId: string,
    eventId: number,
  ): Promise<string> {
    const { data } = await openHands.get<GetPromptResponse>(
      `/api/conversations/${conversationId}/remember_prompt`,
      {
        params: { event_id: eventId },
      },
    );
    return data.prompt;
  }
}
