import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { MicroagentManagementViewMicroagentHeader } from "./microagent-management-view-microagent-header";
import { MicroagentManagementViewMicroagentContent } from "./microagent-management-view-microagent-content";

export function MicroagentManagementViewMicroagent() {
  const { selectedMicroagentItem } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { selectedRepository } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { microagent } = selectedMicroagentItem ?? {};

  if (!microagent || !selectedRepository) {
    return null;
  }

  return (
    <div className="flex flex-col w-full h-full p-6 overflow-auto">
      <MicroagentManagementViewMicroagentHeader />
      <span className="text-white text-2xl font-medium pb-2">
        {microagent.name}
      </span>
      <span className="text-white text-lg font-medium pb-6">
        {microagent.path}
      </span>
      <div className="flex-1">
        <MicroagentManagementViewMicroagentContent />
      </div>
    </div>
  );
}
