import { openHands } from "../open-hands-axios";
import {
  Conversation,
  GetConversationsResponse,
  UpdateConversationBody,
} from "./conversation-service.types";
import { getConversationUrl } from "./conversation-service.utils";

export class ConversationService {
  static async createConversation(
    selectedRepository?: string,
    initialUserMsg?: string,
    imageUrls?: string[],
    replayJson?: string,
  ): Promise<Conversation> {
    const body = {
      selected_repository: selectedRepository,
      selected_branch: undefined,
      initial_user_msg: initialUserMsg,
      image_urls: imageUrls,
      replay_json: replayJson,
    };

    const { data } = await openHands.post<Conversation>(
      getConversationUrl(),
      body,
    );

    return data;
  }

  static async getConversation(conversationId: string) {
    const { data } = await openHands.get<Conversation | null>(
      getConversationUrl(conversationId),
    );

    return data;
  }

  static async getConversations(): Promise<Conversation[]> {
    const { data } = await openHands.get<GetConversationsResponse>(
      getConversationUrl(),
      { params: { limit: 9 } },
    );

    return data.results;
  }

  static async updateConversation(
    conversationId: string,
    conversation: UpdateConversationBody,
  ): Promise<void> {
    await openHands.patch(getConversationUrl(conversationId), conversation);
  }

  static async deleteConversation(conversationId: string): Promise<void> {
    await openHands.delete(`/api/conversations/${conversationId}`);
  }
}
