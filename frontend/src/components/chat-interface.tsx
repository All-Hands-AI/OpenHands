import { useDispatch } from "react-redux";
import { useSocket } from "#/context/socket";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { ChatMessage } from "./chat-message";
import { FeedbackActions } from "./feedback-actions";
import { ImageCarousel } from "./image-carousel";
import { createChatMessage } from "#/services/chatService";
import { InteractiveChatBox } from "./interactive-chat-box";
import { addUserMessage } from "#/state/chatSlice";

const isErrorMessage = (
  message: Message | ErrorMessage,
): message is ErrorMessage => "error" in message;

interface ChatInterfaceProps {
  messages: (Message | ErrorMessage)[];
}

export function ChatInterface({ messages }: ChatInterfaceProps) {
  const { send } = useSocket();
  const dispatch = useDispatch();

  const handleSendMessage = async (content: string, files: File[]) => {
    const promises = files.map((file) => convertImageToBase64(file));
    const imageUrls = await Promise.all(promises);

    const timestamp = new Date().toISOString();
    dispatch(addUserMessage({ content, imageUrls, timestamp }));
    send(createChatMessage(content, imageUrls, timestamp));
  };

  return (
    <div className="h-full flex flex-col justify-between">
      <div className="flex flex-col grow overflow-y-auto overflow-x-hidden px-4 pt-4">
        {messages.map((message, index) =>
          isErrorMessage(message) ? (
            <div key={index} data-testid="error-message">
              <span>{message.error}</span>
              <p>{message.message}</p>
            </div>
          ) : (
            <ChatMessage
              key={index}
              type={message.sender}
              message={message.content}
            >
              {message.imageUrls.length > 0 && (
                <ImageCarousel images={message.imageUrls} />
              )}
            </ChatMessage>
          ),
        )}
      </div>

      <div className="flex flex-col gap-[6px] px-4 pb-4">
        <div className="flex justify-between">
          {messages.length > 3 && <FeedbackActions />}
          {messages.length > 2 && (
            <button type="button" data-testid="continue-action-button">
              Continue
            </button>
          )}
        </div>
        <InteractiveChatBox onSubmit={handleSendMessage} />
      </div>
    </div>
  );
}
