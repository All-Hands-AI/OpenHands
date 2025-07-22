import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { MicroagentManagementSidebar } from "./microagent-management-sidebar";
import { MicroagentManagementMain } from "./microagent-management-main";
import { MicroagentManagementAddMicroagentModal } from "./microagent-management-add-microagent-modal";
import { RootState } from "#/store";
import {
  setAddMicroagentModalVisible,
  addMicroagentStatus,
  updateMicroagentStatus,
} from "#/state/microagent-management-slice";
import { useCreateConversationAndSubscribeMultiple } from "#/hooks/use-create-conversation-and-subscribe-multiple";
import { MicroagentFormData } from "#/types/microagent-management";
import { MicroagentStatus } from "#/types/microagent-status";
import { AgentState } from "#/types/agent-state";
import { getFirstPRUrl } from "#/utils/parse-pr-url";
import {
  getDefaultBranch,
  getPR,
  getProviderName,
  getPRShort,
} from "#/utils/utils";
import {
  isOpenHandsEvent,
  isAgentStateChangeObservation,
  isFinishAction,
} from "#/types/core/guards";
import { GitRepository } from "#/types/git";
import { queryClient } from "#/query-client-config";

export function MicroagentManagementContent() {
  const { addMicroagentModalVisible, selectedRepository } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const dispatch = useDispatch();
  const { createConversationAndSubscribe, isPending } =
    useCreateConversationAndSubscribeMultiple();

  // Responsive width state
  const [width, setWidth] = React.useState(
    typeof window !== "undefined" ? window.innerWidth : 1200,
  );

  React.useEffect(() => {
    function handleResize() {
      setWidth(window.innerWidth);
    }
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

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

  // Reusable function to update microagent status and invalidate conversations list
  const updateMicroagentStatusAndInvalidate = React.useCallback(
    (
      conversationId: string,
      status: MicroagentStatus,
      repositoryName: string,
      prUrl?: string,
    ) => {
      dispatch(
        updateMicroagentStatus({
          conversationId,
          status,
          ...(prUrl && { prUrl }),
        }),
      );

      // Invalidate conversations list when microagent status changes
      invalidateConversationsList(repositoryName);
    },
    [dispatch, invalidateConversationsList],
  );

  const handleMicroagentEvent = React.useCallback(
    (socketEvent: unknown, microagentConversationId: string) => {
      // Handle error events
      const isErrorEvent = (
        evt: unknown,
      ): evt is { error: true; message: string } =>
        typeof evt === "object" &&
        evt !== null &&
        "error" in evt &&
        evt.error === true;

      const isAgentStatusError = (evt: unknown): boolean =>
        isOpenHandsEvent(evt) &&
        isAgentStateChangeObservation(evt) &&
        evt.extras.agent_state === AgentState.ERROR;

      // Get repository name from selectedRepository for invalidation
      const repositoryName =
        selectedRepository && typeof selectedRepository === "object"
          ? (selectedRepository as GitRepository).full_name
          : "";

      if (isErrorEvent(socketEvent) || isAgentStatusError(socketEvent)) {
        updateMicroagentStatusAndInvalidate(
          microagentConversationId,
          MicroagentStatus.ERROR,
          repositoryName,
        );
      } else if (
        isOpenHandsEvent(socketEvent) &&
        isAgentStateChangeObservation(socketEvent)
      ) {
        if (socketEvent.extras.agent_state === AgentState.FINISHED) {
          updateMicroagentStatusAndInvalidate(
            microagentConversationId,
            MicroagentStatus.COMPLETED,
            repositoryName,
          );
        }
      } else if (isOpenHandsEvent(socketEvent) && isFinishAction(socketEvent)) {
        // Check if the finish action contains a PR URL
        const prUrl = getFirstPRUrl(socketEvent.args.final_thought || "");
        if (prUrl) {
          updateMicroagentStatusAndInvalidate(
            microagentConversationId,
            MicroagentStatus.COMPLETED,
            repositoryName,
            prUrl,
          );
        }
      }
    },
    [updateMicroagentStatusAndInvalidate, selectedRepository],
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
    const conversationInstructions = `Create a microagent for the repository ${repositoryName} by following the steps below:

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
        branch: getDefaultBranch(gitProvider),
        gitProvider,
      },
      createMicroagent,
      onSuccessCallback: (conversationId: string) => {
        hideAddMicroagentModal();

        // Add the new microagent to the status tracking
        dispatch(
          addMicroagentStatus({
            eventId: Date.now(), // Use timestamp as event ID for microagent creation
            conversationId,
            status: MicroagentStatus.CREATING,
          }),
        );

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
      onEventCallback: (event: unknown, conversationId: string) => {
        // Handle conversation events for real-time status updates
        handleMicroagentEvent(event, conversationId);
      },
    });
  };

  if (width < 1024) {
    return (
      <div className="w-full h-full flex flex-col gap-6">
        <div className="w-full rounded-lg border border-[#525252] bg-[#24272E] max-h-[494px] min-h-[494px]">
          <MicroagentManagementSidebar isSmallerScreen />
        </div>
        <div className="w-full rounded-lg border border-[#525252] bg-[#24272E] flex-1 min-h-[494px]">
          <MicroagentManagementMain />
        </div>
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

  return (
    <div className="w-full h-full flex rounded-lg border border-[#525252] bg-[#24272E] overflow-hidden">
      <MicroagentManagementSidebar />
      <div className="flex-1">
        <MicroagentManagementMain />
      </div>
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
