import React from "react";
import TextareaAutosize from "react-textarea-autosize";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";
import { SubmitButton } from "#/components/shared/buttons/submit-button";
import { StopButton } from "#/components/shared/buttons/stop-button";

// Use a lightweight pubsub pattern to notify components
// when the chat input message is injected outside of the
// react component tree.
interface ChatInputCoordinator {
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  subscribe: (callback: () => void) => () => void;
  publish: () => void;
}

const ChatInputContext = React.createContext<ChatInputCoordinator | undefined>(
  undefined,
);

export function ChatInputProvider({ children }: { children: React.ReactNode }) {
  const coordinatorRef = React.useRef<ChatInputCoordinator | null>(null);

  // Initialize the coordinator only once.
  // After which it will be stable and never change
  if (coordinatorRef.current === null) {
    const listeners = new Set<() => void>();
    coordinatorRef.current = {
      textareaRef: React.createRef<HTMLTextAreaElement>(),
      subscribe: (callback) => {
        listeners.add(callback);

        return () => listeners.delete(callback);
      },
      publish: () => {
        listeners.forEach((callback) => callback());
      },
    };
  }

  // Provider is also stable due to using .current and can safely
  // be used anywhere in the application without extra renders
  return (
    <ChatInputContext.Provider value={coordinatorRef.current}>
      {children}
    </ChatInputContext.Provider>
  );
}

function useChatInputRef() {
  const { t } = useTranslation();
  const context = React.useContext(ChatInputContext);
  if (!context) {
    throw new Error(t(I18nKey.ERROR$USE_CHAT_INPUT_PROVIDER));
  }
  return context;
}

export function useInjectChatInputMessage() {
  const coordinator = useChatInputRef();

  return React.useCallback(
    (injectedMessage: string) => {
      const textarea = coordinator.textareaRef.current;

      if (textarea) {
        textarea.value = injectedMessage;
        textarea.focus();

        coordinator.publish();
      }
    },
    [coordinator],
  );
}

function useRenderOnMessageInject() {
  const coordinator = useChatInputRef();
  const [, forceRender] = React.useReducer((x) => x + 1, 0);

  React.useEffect(() => {
    const unsubscribe = coordinator.subscribe(forceRender);

    return unsubscribe;
  }, [coordinator]);
}

interface ChatInputProps {
  name?: string;
  button?: "submit" | "stop";
  disabled?: boolean;
  showButton?: boolean;
  defaultValue?: string;
  maxRows?: number;
  onSubmit: (message: string) => void;
  onStop?: () => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onImagePaste?: (files: File[]) => void;
  className?: React.HTMLAttributes<HTMLDivElement>["className"];
  buttonClassName?: React.HTMLAttributes<HTMLButtonElement>["className"];
}

export function ChatInput({
  name,
  button = "submit",
  disabled,
  showButton = true,
  defaultValue,
  maxRows = 16,
  onSubmit,
  onStop,
  onFocus,
  onBlur,
  onImagePaste,
  className,
  buttonClassName,
}: ChatInputProps) {
  const { t } = useTranslation();
  const [isDraggingOver, setIsDraggingOver] = React.useState(false);

  const { textareaRef } = useChatInputRef();
  useRenderOnMessageInject();

  const handlePaste = (event: React.ClipboardEvent<HTMLTextAreaElement>) => {
    // Only handle paste if we have an image paste handler and there are files
    if (onImagePaste && event.clipboardData.files.length > 0) {
      const files = Array.from(event.clipboardData.files).filter((file) =>
        file.type.startsWith("image/"),
      );
      // Only prevent default if we found image files to handle
      if (files.length > 0) {
        event.preventDefault();
        onImagePaste(files);
      }
    }
    // For text paste, let the default behavior handle it
  };

  const handleDragOver = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault();
    if (event.dataTransfer.types.includes("Files")) {
      setIsDraggingOver(true);
    }
  };

  const handleDragLeave = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault();
    setIsDraggingOver(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault();
    setIsDraggingOver(false);
    if (onImagePaste && event.dataTransfer.files.length > 0) {
      const files = Array.from(event.dataTransfer.files).filter((file) =>
        file.type.startsWith("image/"),
      );
      if (files.length > 0) {
        onImagePaste(files);
      }
    }
  };

  const handleSubmitMessage = () => {
    const message = textareaRef.current?.value || "";
    if (message.trim()) {
      onSubmit(message);
      if (textareaRef.current) {
        textareaRef.current.value = "";
      }
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !disabled &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      handleSubmitMessage();
    }
  };

  return (
    <div
      data-testid="chat-input"
      className="flex items-end justify-end grow gap-1 min-h-6 w-full"
    >
      <TextareaAutosize
        ref={textareaRef}
        name={name}
        placeholder={t(I18nKey.SUGGESTIONS$WHAT_TO_BUILD)}
        onKeyDown={handleKeyPress}
        onFocus={onFocus}
        onBlur={onBlur}
        onPaste={handlePaste}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        defaultValue={defaultValue}
        minRows={1}
        maxRows={maxRows}
        data-dragging-over={isDraggingOver}
        className={cn(
          "grow text-sm self-center placeholder:text-neutral-400 text-white resize-none outline-none ring-0",
          "transition-all duration-200 ease-in-out",
          isDraggingOver
            ? "bg-neutral-600/50 rounded-lg px-2"
            : "bg-transparent",
          className,
        )}
      />
      {showButton && (
        <div className={buttonClassName}>
          {button === "submit" && (
            <SubmitButton isDisabled={disabled} onClick={handleSubmitMessage} />
          )}
          {button === "stop" && (
            <StopButton isDisabled={disabled} onClick={onStop} />
          )}
        </div>
      )}
    </div>
  );
}
