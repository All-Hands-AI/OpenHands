import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { BrandButton } from "../settings/brand-button";
import AllHandsLogo from "#/assets/branding/all-hands-logo-spark.svg?react";

export function HomeHeader() {
  const navigate = useNavigate();
  const {
    mutate: createConversation,
    isPending,
    isSuccess,
  } = useCreateConversation();
  const isCreatingConversationElsewhere = useIsCreatingConversation();
  const { t } = useTranslation();

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  return (
    <header className="flex flex-col gap-5">
      <AllHandsLogo />

      <div className="flex items-center justify-between">
        <h1 className="heading">{t("HOME$LETS_START_BUILDING")}</h1>
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
          {!isCreatingConversation && t("HOME$LAUNCH_FROM_SCRATCH")}
          {isCreatingConversation && t("HOME$LOADING")}
        </BrandButton>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm max-w-[424px]">
          {t("HOME$OPENHANDS_DESCRIPTION")}
        </p>
        <p className="text-sm">
          {t("HOME$NOT_SURE_HOW_TO_START")}{" "}
          <a
            href="https://docs.all-hands.dev/usage/getting-started"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2"
          >
            {t("HOME$READ_THIS")}
          </a>
        </p>
      </div>
    </header>
  );
}
