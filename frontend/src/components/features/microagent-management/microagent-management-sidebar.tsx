import { MicroagentManagementSidebarHeader } from "./microagent-management-sidebar-header";
import { MicroagentManagementSidebarTabs } from "./microagent-management-sidebar-tabs";

export function MicroagentManagementSidebar() {
  return (
    <div className="w-[418px] h-full border-r border-[#525252] bg-[#24272E] rounded-tl-lg rounded-bl-lg py-10 px-6">
      <MicroagentManagementSidebarHeader />
      <MicroagentManagementSidebarTabs />
    </div>
  );
}
