import { useCasesMocks } from "#/mocks/use-cases.mock";
import { handleAssistantMessage } from "#/services/actions";
import { sleep } from "#/utils/utils";
import { useEffect, useState } from "react";

const useStreamUseCaseForUser = (conversationId: string | number) => {
  const [isLoadingMessage, setIsLoadingMessage] = useState(true);

  useEffect(() => {
    if (!conversationId) {
      return;
    }

    try {
      const listEventOfConversation =
        useCasesMocks[conversationId] || ([] as any);

      (async () => {
        for (const ev of listEventOfConversation) {
          if (
            true
            // !pushedEvents.find((x) => JSON.stringify(x) === JSON.stringify(ev))
          ) {
            setIsLoadingMessage(true);
            handleAssistantMessage(ev);

            await sleep(500);
            setIsLoadingMessage(false);
            await sleep(500);
          }
        }
      })();
    } catch (error) {
      console.log(
        "listEventOfConversation handleAssistantMessage error",
        error,
      );
    } finally {
      setIsLoadingMessage(false);
    }
  }, [conversationId]);

  return {
    isLoadingMessage,
  };
};

export default useStreamUseCaseForUser;
