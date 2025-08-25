import { queryClient } from "#/query-client-config";
import { GetConfigResponse } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { MicroagentManagementContent } from "#/components/features/microagent-management/microagent-management-content";
import { ConversationSubscriptionsProvider } from "#/context/conversation-subscriptions-provider";
import { EventHandler } from "#/wrapper/event-handler";

export const clientLoader = async () => {
  let config = queryClient.getQueryData<GetConfigResponse>(["config"]);
  if (!config) {
    config = await OpenHands.getConfig();
    queryClient.setQueryData<GetConfigResponse>(["config"], config);
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
