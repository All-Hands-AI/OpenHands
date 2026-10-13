import { create } from "zustand";
import { devtools } from "zustand/middleware";

export interface SecretRequest {
  conversationId: string;
  toolCallId: string;
  name: string;
  reason: string | null;
}

interface SecretRequestState {
  /** Pending requests, oldest first; the modal shows one at a time. */
  requests: SecretRequest[];
}

interface SecretRequestActions {
  enqueue: (request: SecretRequest) => void;
  dismiss: (toolCallId: string) => void;
}

export const useSecretRequestStore = create<
  SecretRequestState & SecretRequestActions
>()(
  devtools(
    (set) => ({
      requests: [],
      enqueue: (request) =>
        set((s) => ({ requests: [...s.requests, request] })),
      dismiss: (toolCallId) =>
        set((s) => ({
          requests: s.requests.filter((r) => r.toolCallId !== toolCallId),
        })),
    }),
    { name: "SecretRequestStore" },
  ),
);
