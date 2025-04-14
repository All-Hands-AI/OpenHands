import React from "react";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { setInitialPrompt } from "#/state/initial-query-slice";

const INITIAL_PROMPT = "";

export function CodeNotInGitLink() {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const { mutate: createConversation } = useCreateConversation();

  const handleStartFromScratch = () => {
    // Set the initial prompt and create a new conversation
    dispatch(setInitialPrompt(INITIAL_PROMPT));
    createConversation({ q: INITIAL_PROMPT });
  };

  return (
    <div className="text-xs text-neutral-400">
      {t(I18nKey.GITHUB$CODE_NOT_IN_GITHUB)}{" "}
      <span
        onClick={handleStartFromScratch}
        className="underline cursor-pointer"
      >
        {t(I18nKey.GITHUB$START_FROM_SCRATCH)}
      </span>{" "}
      {t(I18nKey.GITHUB$VSCODE_LINK_DESCRIPTION)}
    </div>
  );
}
