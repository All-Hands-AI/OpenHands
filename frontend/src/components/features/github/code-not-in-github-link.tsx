import React from "react";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";

const INITIAL_PROMPT = "";

export function CodeNotInGitHubLink() {
  const { mutate: createConversation } = useCreateConversation();

  const handleStartFromScratch = () => {
    // Create a new conversation
    createConversation({ q: INITIAL_PROMPT });
  };

  return (
    <div className="text-xs text-neutral-400">
      Code not in GitHub?{" "}
      <span
        onClick={handleStartFromScratch}
        className="underline cursor-pointer"
      >
        Start from scratch
      </span>{" "}
      and use the VS Code link to upload and download your code.
    </div>
  );
}
