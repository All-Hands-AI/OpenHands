import { toasterMessages, Typography } from "@openhands/ui";
import { Spinner } from "@heroui/react";
import { useTranslation } from "react-i18next";
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
    <div className="flex items-start gap-2 pl-4">
      <Spinner size="sm" />
      <div>
        <Typography.H6> {t("MICROAGENT$ADDING_CONTEXT")}</Typography.H6>
        <Typography.Text>
          <a
            href={`/conversations/${conversationId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            {t("MICROAGENT$VIEW_CONVERSATION")}
          </a>
        </Typography.Text>
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
        <Typography.H6>{t("MICROAGENT$SUCCESS_PR_READY")}</Typography.H6>
        <Typography.Text>
          <a
            href={`/conversations/${conversationId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            {t("MICROAGENT$VIEW_CONVERSATION")}
          </a>
        </Typography.Text>
      </div>
      <button type="button" onClick={onClose}>
        <CloseIcon />
      </button>
    </div>
  );
}

export const renderConversationCreatedToast = (conversationId: string) =>
  toasterMessages.custom(
    (props) => (
      <ConversationCreatedToast
        conversationId={conversationId}
        onClose={props.onDismiss}
      />
    ),
    { duration: 5_000, position: "top-right" },
  );

export const renderConversationFinishedToast = (conversationId: string) =>
  toasterMessages.custom(
    (props) => (
      <ConversationFinishedToast
        conversationId={conversationId}
        onClose={props.onDismiss}
      />
    ),
    { duration: 5_000, position: "top-right" },
  );

export const renderConversationErroredToast = (errorMessage: string) =>
  toasterMessages.error(errorMessage, {
    duration: 5_000,
    position: "top-right",
  });
