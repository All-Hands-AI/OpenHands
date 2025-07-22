import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { MicroagentManagementDefault } from "./microagent-management-default";
import { MicroagentManagementOpeningPr } from "./microagent-management-opening-pr";
import { MicroagentManagementReviewPr } from "./microagent-management-review-pr";
import { MicroagentManagementViewMicroagent } from "./microagent-management-view-microagent";

export function MicroagentManagementMain() {
  const { selectedMicroagentItem } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { microagent, conversation } = selectedMicroagentItem ?? {};

  if (microagent) {
    return <MicroagentManagementViewMicroagent />;
  }

  if (conversation) {
    const prNumber = conversation.pr_number || [];
    if (prNumber.length === 0) {
      return <MicroagentManagementOpeningPr />;
    }

    return <MicroagentManagementReviewPr />;
  }

  return <MicroagentManagementDefault />;
}
