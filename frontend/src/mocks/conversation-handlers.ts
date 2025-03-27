import { http, HttpResponse } from "msw";
import {
  Conversation,
  GetConversationsResponse,
} from "#/api/conversation-service/conversation-service.types";

const generateISODate = (days: number) =>
  new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

const conversations: Conversation[] = [
  {
    conversation_id: "1",
    title: "My New Project",
    selected_repository: null,
    last_updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    status: "RUNNING",
  },
  {
    conversation_id: "2",
    title: "Repo Testing",
    selected_repository: "octocat/hello-world",
    last_updated_at: generateISODate(2),
    created_at: generateISODate(2),
    status: "STOPPED",
  },
  {
    conversation_id: "3",
    title: "Another Project",
    selected_repository: "octocat/earth",
    last_updated_at: generateISODate(5),
    created_at: generateISODate(5),
    status: "STOPPED",
  },
];

const CONVERSATIONS = new Map<string, Conversation>(
  conversations.map((conversation) => [
    conversation.conversation_id,
    conversation,
  ]),
);

export const CONVERSATION_HANDLERS = [
  http.get("/api/conversations", async () => {
    const values = Array.from(CONVERSATIONS.values());
    const results: GetConversationsResponse = {
      results: values,
      next_page_id: null,
    };

    return HttpResponse.json(results, { status: 200 });
  }),

  http.delete("/api/conversations/:conversationId", async ({ params }) => {
    const { conversationId } = params;

    if (typeof conversationId === "string") {
      CONVERSATIONS.delete(conversationId);
      return HttpResponse.json(null, { status: 200 });
    }

    return HttpResponse.json(null, { status: 404 });
  }),

  http.patch(
    "/api/conversations/:conversationId",
    async ({ params, request }) => {
      const { conversationId } = params;

      if (typeof conversationId === "string") {
        const conversation = CONVERSATIONS.get(conversationId);

        if (conversation) {
          const body = await request.json();
          if (typeof body === "object" && body?.title) {
            CONVERSATIONS.set(conversationId, {
              ...conversation,
              title: body.title,
            });
            return HttpResponse.json(null, { status: 200 });
          }
        }
      }

      return HttpResponse.json(null, { status: 404 });
    },
  ),

  http.post("/api/conversations", () => {
    const conversation: Conversation = {
      conversation_id: (Math.random() * 100).toString(),
      title: "New Conversation",
      selected_repository: null,
      last_updated_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      status: "RUNNING",
    };

    CONVERSATIONS.set(conversation.conversation_id, conversation);
    return HttpResponse.json(conversation, { status: 201 });
  }),

  http.get("/api/conversations/:conversationId", async ({ params }) => {
    const { conversationId } = params;

    if (typeof conversationId === "string") {
      const project = CONVERSATIONS.get(conversationId);
      if (project) return HttpResponse.json(project, { status: 200 });
    }

    return HttpResponse.json(null, { status: 404 });
  }),
];
