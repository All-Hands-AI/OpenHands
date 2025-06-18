import toast from "react-hot-toast";
import { Spinner } from "@heroui/react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  return (
    <div className="flex items-start gap-2">
      <Spinner size="sm" />
      <div>
        {t("MICROAGENT$ADDING_CONTEXT")}
        <br />
        <a
          href={`/conversations/${conversationId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          {t("MICROAGENT$VIEW_CONVERSATION")}
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
  const { t } = useTranslation();
  return (
    <div className="flex items-start gap-2">
      <SuccessIndicator status="success" />
      <div>
        {t("MICROAGENT$SUCCESS_PR_READY")}
        <br />
        <a
          href={`/conversations/${conversationId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          {t("MICROAGENT$VIEW_CONVERSATION")}
        </a>
      </div>
      <button type="button" onClick={onClose}>
        <CloseIcon />
      </button>
    </div>
  );
}

interface ConversationErroredToastProps {
  errorMessage: string;
  onClose: () => void;
}

function ConversationErroredToast({
  errorMessage,
  onClose,
}: ConversationErroredToastProps) {
  return (
    <div className="flex items-start gap-2">
      <SuccessIndicator status="error" />
      <div>{errorMessage}</div>
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
      id: `status-${conversationId}`,
      duration: 5000,
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
      id: `status-${conversationId}`,
      duration: 5000,
    },
  );

export const renderConversationErroredToast = (
  conversationId: string,
  errorMessage: string,
) =>
  toast(
    (t) => (
      <ConversationErroredToast
        errorMessage={errorMessage}
        onClose={() => toast.dismiss(t.id)}
      />
    ),
    {
      ...TOAST_OPTIONS,
      id: `status-${conversationId}`,
      duration: 5000,
    },
  );
