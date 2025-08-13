import { Container } from "#/components/features/conversation/conversation-tabs/container";
import { TabContent } from "#/components/features/conversation/conversation-tabs/tab-content";

import { cn } from "#/utils/utils";

export function ConversationTabs() {
  return (
    <Container className={cn("h-full w-full")} labels={[]}>
      {/* Use both Outlet and TabContent */}
      <div className="h-full w-full">
        <TabContent />
      </div>
    </Container>
  );
}
