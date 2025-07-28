import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../settings/brand-button";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import PlusIcon from "#/icons/u-plus.svg?react";

export function NewConversation() {
  const { t } = useTranslation();

  const navigate = useNavigate();
  const {
    mutate: createConversation,
    isPending,
    isSuccess,
  } = useCreateConversation();
  const isCreatingConversationElsewhere = useIsCreatingConversation();

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  return (
    <section className="w-full flex flex-col bg-[#363940] rounded-[15px] p-[20px] gap-[10px]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-[10px]">
          <PlusIcon width={17} height={14} />
          <span className="leading-5 font-bold text-base text-white">
            {t(I18nKey.COMMON$NEW_CONVERSATION)}
          </span>
        </div>
      </div>
      <div>
        <span className="leading-[22px] text-sm font-normal text-white">
          {t(I18nKey.HOME$NEW_PROJECT_DESCRIPTION)}
        </span>
      </div>
      <BrandButton
        testId="header-launch-button"
        variant="primary"
        type="button"
        onClick={() =>
          createConversation(
            {},
            {
              onSuccess: (data) =>
                navigate(`/conversations/${data.conversation_id}`),
            },
          )
        }
        isDisabled={isCreatingConversation}
      >
        {!isCreatingConversation && t("COMMON$NEW_CONVERSATION")}
        {isCreatingConversation && t("HOME$LOADING")}
      </BrandButton>
    </section>
  );
}
