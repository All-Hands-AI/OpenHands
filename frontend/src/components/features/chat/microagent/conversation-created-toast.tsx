import toast from "react-hot-toast";
import { Spinner } from "@heroui/react";
import { TOAST_OPTIONS } from "#/utils/custom-toast-handlers";
import CloseIcon from "#/icons/close.svg?react";
import { SuccessIndicator } from "../success-indicator";

interface ConversationCreatedToastProps {
  conversationId: string;
  onClose: () => void;
}

function ConversationCreatedToast({
  conversationId,
  onClose,
}: ConversationCreatedToastProps) {
  return (
    <div className="flex items-start gap-2">
      <Spinner size="sm" />
      <div>
        OpenHands is adding this new context to your respository. We&nbsp;ll let
        you know when the pull request is ready.
        <br />
        <a
          href={`/conversations/${conversationId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          View Conversation
        </a>
      </div>
      <button type="button" onClick={onClose}>
        <CloseIcon />
      </button>
    </div>
  );
}

interface ConversationFinishedToastProps {
  conversationId: string;
  onClose: () => void;
}

function ConversationFinishedToast({
  conversationId,
  onClose,
}: ConversationFinishedToastProps) {
  return (
    <div className="flex items-start gap-2">
      <SuccessIndicator status="success" />
      <div>
        Success! Your microagent pull request is ready.
        <br />
        <a
          href={`/conversations/${conversationId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          View Conversation
        </a>
      </div>
      <button type="button" onClick={onClose}>
        <CloseIcon />
      </button>
    </div>
  );
}

export const renderConversationCreatedToast = (conversationId: string) =>
  toast(
    (t) => (
      <ConversationCreatedToast
        conversationId={conversationId}
        onClose={() => toast.dismiss(t.id)}
      />
    ),
    {
      ...TOAST_OPTIONS,
      id: "status",
      duration: Infinity,
    },
  );

export const renderConversationFinishedToast = (conversationId: string) =>
  toast(
    (t) => (
      <ConversationFinishedToast
        conversationId={conversationId}
        onClose={() => toast.dismiss(t.id)}
      />
    ),
    {
      ...TOAST_OPTIONS,
      id: "status",
      duration: Infinity,
    },
  );
