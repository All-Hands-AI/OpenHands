import { useSelector } from "react-redux";
import { useWindowSize } from "@uidotdev/usehooks";
import { AnimatePresence, motion } from "framer-motion";
import { ChatInterface } from "../chat/chat-interface";
import { ConversationTabContent } from "./conversation-tabs/conversation-tab-content";
import { cn } from "#/utils/utils";
import { RootState } from "#/store";

export function ConversationMain() {
  const { width } = useWindowSize();
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );
  const isMobile = width && width <= 1024;

  if (isMobile) {
    return (
      <div className="flex flex-col gap-3 w-full overflow-x-hidden">
        <div
          className={cn(
            "overflow-hidden w-full bg-base min-h-[494px]",
            !isRightPanelShown && "h-full",
          )}
        >
          <ChatInterface />
        </div>
        <AnimatePresence mode="wait">
          {isRightPanelShown && (
            <motion.div
              key="mobile-right-panel"
              initial={{ y: "100%", opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: "100%", opacity: 0 }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                duration: 0.3,
              }}
              className="h-full w-full min-h-[494px] flex flex-col gap-3"
            >
              <ConversationTabContent />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "grid h-full w-full min-h-0 min-w-0 overflow-x-hidden transition-all duration-300 ease-in-out",
        isRightPanelShown ? "grid-cols-[1fr_1fr]" : "grid-cols-[1fr_0fr]",
      )}
    >
      {/* Left Panel - Chat Interface */}
      <div className="overflow-hidden bg-base h-full">
        <div className="flex justify-center w-full h-full">
          <div
            className={cn(
              "w-full h-full",
              !isRightPanelShown && "max-w-[768px]",
            )}
          >
            <ChatInterface />
          </div>
        </div>
      </div>

      {/* Right Panel - Conversation Tabs */}
      <div className="overflow-hidden h-full">
        <AnimatePresence>
          {isRightPanelShown && (
            <motion.div
              key="right-panel"
              initial={{ x: "100%", opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: "100%", opacity: 0 }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                duration: 0.3,
              }}
              className="w-full h-full flex flex-col overflow-hidden"
            >
              <div className="flex flex-col flex-1 gap-3">
                <ConversationTabContent />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
