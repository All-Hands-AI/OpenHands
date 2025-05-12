import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";
import { SubmitButton } from "#/components/shared/buttons/submit-button";
import { StopButton } from "#/components/shared/buttons/stop-button";
import { TipTapEditor } from "./tiptap-editor";

interface ChatInputProps {
  name?: string;
  button?: "submit" | "stop";
  disabled?: boolean;
  showButton?: boolean;
  value?: string;
  maxRows?: number;
  onSubmit: (message: string) => void;
  onStop?: () => void;
  onChange?: (message: string) => void;
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
  value = "",
  maxRows = 16,
  onSubmit,
  onStop,
  onChange,
  onFocus,
  onBlur,
  onImagePaste,
  className,
  buttonClassName,
}: ChatInputProps) {
  const { t } = useTranslation();
  const [inputValue, setInputValue] = React.useState(value);

  const handleChange = (newValue: string) => {
    setInputValue(newValue);
    onChange?.(newValue);
  };

  const handleSubmitMessage = () => {
    if (inputValue.trim()) {
      onSubmit(inputValue);
      setInputValue("");
      onChange?.("");
    }
  };

  return (
    <div
      data-testid="chat-input"
      className="flex items-end justify-end grow gap-1 min-h-6 w-full relative"
    >
      <TipTapEditor
        value={inputValue}
        onChange={handleChange}
        onSubmit={handleSubmitMessage}
        onFocus={onFocus}
        onBlur={onBlur}
        placeholder={t(I18nKey.SUGGESTIONS$WHAT_TO_BUILD)}
        disabled={disabled}
        className={className}
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
