import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { MicroagentManagementDefault } from "./microagent-management-default";
import { MicroagentManagementOpeningPr } from "./microagent-management-opening-pr";
import { MicroagentManagementReviewPr } from "./microagent-management-review-pr";
import { MicroagentManagementViewMicroagent } from "./microagent-management-view-microagent";
import {
  isConversationCompleted,
  isConversationError,
  isConversationOpeningPR,
  isConversationStarting,
  isConversationStopped,
} from "#/utils/utils";
import { MicroagentManagementError } from "./microagent-management-error";
import { MicroagentManagementConversationStopped } from "./microagent-management-conversation-stopped";

export function MicroagentManagementMain() {
  const { selectedMicroagentItem } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { microagent, conversation } = selectedMicroagentItem ?? {};

  if (microagent) {
    return <MicroagentManagementViewMicroagent />;
  }

  if (conversation) {
    const hasPr = !!(
      conversation.pr_number && conversation.pr_number.length > 0
    );
    if (isConversationCompleted(hasPr)) {
      return <MicroagentManagementReviewPr />;
    }

    if (
      isConversationStarting(
        conversation.status,
        conversation.runtime_status,
      ) ||
      isConversationOpeningPR(conversation.status, conversation.runtime_status)
    ) {
      return <MicroagentManagementOpeningPr />;
    }

    if (isConversationError(conversation.runtime_status)) {
      return <MicroagentManagementError />;
    }

    if (
      isConversationStopped(conversation.status, conversation.runtime_status)
    ) {
      return <MicroagentManagementConversationStopped />;
    }

    return <MicroagentManagementDefault />;
  }

  return <MicroagentManagementDefault />;
}
