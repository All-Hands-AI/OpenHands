import ChatMessage from "./ChatMessage";
import AgentState from "#/types/AgentState";

const isMessage = (message: Message | ErrorMessage): message is Message =>
  "sender" in message;

interface ChatProps {
  messages: (Message | ErrorMessage)[];
  curAgentState?: AgentState;
}

function Chat({ messages, curAgentState }: ChatProps) {
  return (
    <div className="flex flex-col gap-3 px-3 pt-3 mb-6">
      {messages.map((message, index) =>
        isMessage(message) ? (
          <ChatMessage
            key={index}
            message={message}
            isLastMessage={messages && index === messages.length - 1}
            awaitingUserConfirmation={
              curAgentState === AgentState.AWAITING_USER_CONFIRMATION
            }
          />
        ) : (
          <div key={index} className="flex gap-2 items-center justify-start">
            <div className="bg-danger w-2 h-full rounded" />
            <div className="text-sm leading-4 flex flex-col gap-2">
              <p className="text-danger font-bold">{message.error}</p>
              <p className="text-neutral-300">{message.message}</p>
            </div>
          </div>
        ),
      )}
    </div>
  );
}

export default Chat;
