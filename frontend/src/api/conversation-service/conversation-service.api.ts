import { AxiosInstance } from "axios";
import { openHands } from "../open-hands-axios";
import {
  Conversation,
  GetConversationsResponse,
  UpdateConversationBody,
} from "./conversation-service.types";
import { getConversationUrl } from "./conversation-service.utils";

class ConversationService {
  constructor(private axiosInstance: AxiosInstance = openHands) {}

  async createConversation(
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

    const { data } = await this.axiosInstance.post<Conversation>(
      getConversationUrl(),
      body,
    );

    return data;
  }

  async getConversation(conversationId: string) {
    const { data } = await this.axiosInstance.get<Conversation>(
      getConversationUrl(conversationId),
    );

    return data;
  }

  async getConversations(): Promise<Conversation[]> {
    const { data } = await this.axiosInstance.get<GetConversationsResponse>(
      getConversationUrl(),
      { params: { limit: 9 } },
    );

    return data.results;
  }

  async updateConversation(
    conversationId: string,
    conversation: UpdateConversationBody,
  ): Promise<void> {
    await this.axiosInstance.patch(
      getConversationUrl(conversationId),
      conversation,
    );
  }

  async deleteConversation(conversationId: string): Promise<void> {
    await this.axiosInstance.delete(`/api/conversations/${conversationId}`);
  }
}

export const conversationService = new ConversationService();
