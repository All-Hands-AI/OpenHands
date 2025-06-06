import React from "react";
import TextareaAutosize from "react-textarea-autosize";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";
import { SubmitButton } from "#/components/shared/buttons/submit-button";
import { StopButton } from "#/components/shared/buttons/stop-button";
import { useForceRender } from "#/hooks/use-force-render";

const ChatInputContext = React.createContext<
  | [
      string | undefined,
      React.Dispatch<React.SetStateAction<string | undefined>>,
    ]
  | undefined
>(undefined);

function useChatInput() {
  const { t } = useTranslation();
  const context = React.useContext(ChatInputContext);
  if (!context) {
    throw new Error(t(I18nKey.ERROR$USE_CHAT_INPUT_PROVIDER));
  }
  return context;
}

export function useInjectChatInputMessage() {
  const [, setInjectedMessage] = useChatInput();

  return setInjectedMessage;
}

export function ChatInputProvider({ children }: { children: React.ReactNode }) {
  const value = React.useState<string | undefined>(undefined);

  return (
    <ChatInputContext.Provider value={value}>
      {children}
    </ChatInputContext.Provider>
  );
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
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const [isDraggingOver, setIsDraggingOver] = React.useState(false);

  const forceRender = useForceRender();
  const [injectedMessage] = useChatInput();

  React.useEffect(() => {
    if (textareaRef.current && injectedMessage !== undefined) {
      const currentRef = textareaRef.current;
      currentRef.value = injectedMessage;
      currentRef.focus();

      // Unfortunately, TextareaAutosize uses React.useLayoutEffect internally,
      // so we need to force a React render here instead of merely triggering a DOM input update.
      forceRender();
    }
  }, [injectedMessage]);

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
