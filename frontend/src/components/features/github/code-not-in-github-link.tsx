import React from "react";
import { useDispatch } from "react-redux";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { setInitialPrompt } from "#/state/initial-query-slice";
import { useTranslation } from "react-i18next";

const INITIAL_PROMPT = "";

export function CodeNotInGitHubLink() {
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
      {t("GITHUB$CODE_NOT_IN_GITHUB")}{" "}
      <span
        onClick={handleStartFromScratch}
        className="underline cursor-pointer"
      >
        {t("GITHUB$START_FROM_SCRATCH")}
      </span>{" "}
      and use the VS Code link to upload and download your code.
    </div>
  );
}
