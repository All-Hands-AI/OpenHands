import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { BrandButton } from "../../settings/brand-button";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";

export function CreateConversationButton() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const isCreatingConversationElsewhere = useIsCreatingConversation();

  // We check for isCreatingConversationElsewhere to prevent multiple conversations
  const isCreatingConversation = isCreatingConversationElsewhere;

  const handleCreateConversation = () => {
    const taskId = crypto.randomUUID();
    // Navigate with a special setup parameter
    navigate(`/conversations/${taskId}?setup=true`);
  };

  return (
    <BrandButton
      testId="launch-new-conversation-button"
      variant="primary"
      type="button"
      onClick={handleCreateConversation}
      isDisabled={isCreatingConversation}
      className="w-auto absolute bottom-5 left-5 right-5 font-semibold"
    >
      {!isCreatingConversation && t("COMMON$NEW_CONVERSATION")}
      {isCreatingConversation && t("HOME$LOADING")}
    </BrandButton>
  );
}
