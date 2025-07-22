import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { MicroagentManagementSidebar } from "./microagent-management-sidebar";
import { MicroagentManagementMain } from "./microagent-management-main";
import { MicroagentManagementAddMicroagentModal } from "./microagent-management-add-microagent-modal";
import { RootState } from "#/store";
import { setAddMicroagentModalVisible } from "#/state/microagent-management-slice";
import { useCreateConversationAndSubscribeMultiple } from "#/hooks/use-create-conversation-and-subscribe-multiple";
import { MicroagentFormData } from "#/types/microagent-management";
import { AgentState } from "#/types/agent-state";
import { getPR, getProviderName, getPRShort } from "#/utils/utils";
import {
  isOpenHandsEvent,
  isAgentStateChangeObservation,
  isFinishAction,
} from "#/types/core/guards";
import { GitRepository } from "#/types/git";
import { queryClient } from "#/query-client-config";
import { Provider } from "#/types/settings";

// Handle error events
const isErrorEvent = (evt: unknown): evt is { error: true; message: string } =>
  typeof evt === "object" &&
  evt !== null &&
  "error" in evt &&
  evt.error === true;

const isAgentStatusError = (evt: unknown): boolean =>
  isOpenHandsEvent(evt) &&
  isAgentStateChangeObservation(evt) &&
  evt.extras.agent_state === AgentState.ERROR;

const shouldInvalidateConversationsList = (currentSocketEvent: unknown) => {
  const hasError =
    isErrorEvent(currentSocketEvent) || isAgentStatusError(currentSocketEvent);
  const hasStateChanged =
    isOpenHandsEvent(currentSocketEvent) &&
    isAgentStateChangeObservation(currentSocketEvent);
  const hasFinished =
    isOpenHandsEvent(currentSocketEvent) && isFinishAction(currentSocketEvent);

  return hasError || hasStateChanged || hasFinished;
};

const getConversationInstructions = (
  repositoryName: string,
  formData: MicroagentFormData,
  pr: string,
  prShort: string,
  gitProvider: Provider,
) => `Create a microagent for the repository ${repositoryName} by following the steps below:

- Step 1: Create a markdown file inside the .openhands/microagents folder with the name of the microagent (The microagent must be created in the .openhands/microagents folder and should be able to perform the described task when triggered).

- Step 2: Update the markdown file with the content below:

${
  formData.triggers &&
  formData.triggers.length > 0 &&
  `
---
triggers:
${formData.triggers.map((trigger: string) => `  - ${trigger}`).join("\n")}
---
`
}

${formData.query}

- Step 3: Create a new branch for the repository ${repositoryName}, must avoid duplicated branches.

- Step 4: Please push the changes to your branch on ${getProviderName(gitProvider)} and create a ${pr}. Please create a meaningful branch name that describes the changes. If a ${pr} template exists in the repository, please follow it when creating the ${prShort} description.
`;

export function MicroagentManagementContent() {
  const { addMicroagentModalVisible, selectedRepository } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const dispatch = useDispatch();
  const { createConversationAndSubscribe, isPending } =
    useCreateConversationAndSubscribeMultiple();

  const hideAddMicroagentModal = () => {
    dispatch(setAddMicroagentModalVisible(false));
  };

  // Reusable function to invalidate conversations list for a repository
  const invalidateConversationsList = React.useCallback(
    (repositoryName: string) => {
      queryClient.invalidateQueries({
        queryKey: [
          "conversations",
          "search",
          repositoryName,
          "microagent_management",
        ],
      });
    },
    [],
  );

  const handleMicroagentEvent = React.useCallback(
    (socketEvent: unknown) => {
      // Get repository name from selectedRepository for invalidation
      const repositoryName =
        selectedRepository && typeof selectedRepository === "object"
          ? (selectedRepository as GitRepository).full_name
          : "";

      if (shouldInvalidateConversationsList(socketEvent)) {
        invalidateConversationsList(repositoryName);
      }
    },
    [invalidateConversationsList, selectedRepository],
  );

  const handleCreateMicroagent = (formData: MicroagentFormData) => {
    if (!selectedRepository || typeof selectedRepository !== "object") {
      return;
    }

    // Use the GitRepository properties
    const repository = selectedRepository as GitRepository;
    const repositoryName = repository.full_name;
    const gitProvider = repository.git_provider;

    const isGitLab = gitProvider === "gitlab";

    const pr = getPR(isGitLab);
    const prShort = getPRShort(isGitLab);

    // Create conversation instructions for microagent generation
    const conversationInstructions = getConversationInstructions(
      repositoryName,
      formData,
      pr,
      prShort,
      gitProvider,
    );

    // Create the CreateMicroagent object
    const createMicroagent = {
      repo: repositoryName,
      git_provider: gitProvider,
      title: formData.query,
    };

    createConversationAndSubscribe({
      query: conversationInstructions,
      conversationInstructions,
      repository: {
        name: repositoryName,
        branch: formData.selectedBranch,
        gitProvider,
      },
      createMicroagent,
      onSuccessCallback: () => {
        hideAddMicroagentModal();

        // Invalidate conversations list to fetch the latest conversations for this repository
        invalidateConversationsList(repositoryName);

        // Also invalidate microagents list to fetch the latest microagents
        // Extract owner and repo from full_name (format: "owner/repo")
        const [owner, repo] = repositoryName.split("/");
        queryClient.invalidateQueries({
          queryKey: ["repository-microagents", owner, repo],
        });

        hideAddMicroagentModal();
      },
      onEventCallback: (event: unknown) => {
        // Handle conversation events for real-time status updates
        handleMicroagentEvent(event);
      },
    });
  };

  return (
    <div className="w-full h-full flex rounded-lg border border-[#525252] bg-[#24272E]">
      <MicroagentManagementSidebar />
      <MicroagentManagementMain />
      {addMicroagentModalVisible && (
        <MicroagentManagementAddMicroagentModal
          onConfirm={handleCreateMicroagent}
          onCancel={hideAddMicroagentModal}
          isLoading={isPending}
        />
      )}
    </div>
  );
}
