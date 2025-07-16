import { redirect } from "react-router";
import { MicroagentManagementSidebar } from "#/components/features/microagent-management/microagent-management-sidebar";
import { Route } from "./+types/settings";
import { queryClient } from "#/query-client-config";
import { GetConfigResponse } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";

export const clientLoader = async ({ request }: Route.ClientLoaderArgs) => {
  const url = new URL(request.url);
  const { pathname } = url;

  let config = queryClient.getQueryData<GetConfigResponse>(["config"]);
  if (!config) {
    config = await OpenHands.getConfig();
    queryClient.setQueryData<GetConfigResponse>(["config"], config);
  }

  const shouldHideMicroagentManagement =
    config?.FEATURE_FLAGS.HIDE_MICROAGENT_MANAGEMENT;

  if (shouldHideMicroagentManagement && pathname === "/microagent-management") {
    return redirect("/");
  }

  return null;
};

function MicroagentManagement() {
  return (
    <div className="w-full h-full flex rounded-lg border border-[#525252] bg-[#24272E]">
      <MicroagentManagementSidebar />
      <div className="flex-1" />
    </div>
  );
}

export default MicroagentManagement;
