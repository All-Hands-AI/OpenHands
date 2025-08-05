import { redirect } from "react-router";
import { Route } from "./+types/settings";
import { queryClient } from "#/query-client-config";
import { GetConfigResponse } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { MicroagentManagementContent } from "#/components/features/microagent-management/microagent-management-content";
import { ConversationSubscriptionsProvider } from "#/context/conversation-subscriptions-provider";
import { EventHandler } from "#/wrapper/event-handler";

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
    <ConversationSubscriptionsProvider>
      <EventHandler>
        <MicroagentManagementContent />
      </EventHandler>
    </ConversationSubscriptionsProvider>
  );
}

export default MicroagentManagement;
