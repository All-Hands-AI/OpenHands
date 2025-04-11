import { StopButton } from "#/components/shared/buttons/stop-button"
import { SubmitButton } from "#/components/shared/buttons/submit-button"
import { I18nKey } from "#/i18n/declaration"
import { cn } from "#/utils/utils"
import {
  useConversationActions,
  useGetConversationState,
} from "#/zutand-stores/coin/selector"
import React, { useEffect } from "react"
import { useTranslation } from "react-i18next"
import TextareaAutosize from "react-textarea-autosize"

interface ChatInputProps {
  name?: string
  button?: "submit" | "stop"
  disabled?: boolean
  showButton?: boolean
  value?: string
  maxRows?: number
  onSubmit: (message: string) => void
  onStop?: () => void
  onChange?: (message: string) => void
  onFocus?: () => void
  onBlur?: () => void
  onImagePaste?: (files: File[]) => void
  className?: React.HTMLAttributes<HTMLDivElement>["className"]
  buttonClassName?: React.HTMLAttributes<HTMLButtonElement>["className"]
}

export function ChatInput({
  name,
  button = "submit",
  disabled,
  showButton = true,
  value,
  maxRows = 4,
  onSubmit,
  onStop,
  onChange,
  onFocus,
  onBlur,
  onImagePaste,
  className,
  buttonClassName,
}: ChatInputProps) {
  const { t } = useTranslation()
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  const [isDraggingOver, setIsDraggingOver] = React.useState(false)

  const initMsg = useGetConversationState("initMsg")
  const { handleSetInitMsg } = useConversationActions()

  useEffect(() => {
    if (initMsg) {
      onChange(initMsg)
      handleSetInitMsg("")
    }
  }, [initMsg])

  const handlePaste = (event: React.ClipboardEvent<HTMLTextAreaElement>) => {
    // Only handle paste if we have an image paste handler and there are files
    if (onImagePaste && event.clipboardData.files.length > 0) {
      const files = Array.from(event.clipboardData.files).filter((file) =>
        file.type.startsWith("image/"),
      )
      // Only prevent default if we found image files to handle
      if (files.length > 0) {
        event.preventDefault()
        onImagePaste(files)
      }
    }
    // For text paste, let the default behavior handle it
  }

  const handleDragOver = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault()
    if (event.dataTransfer.types.includes("Files")) {
      setIsDraggingOver(true)
    }
  }

  const handleDragLeave = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault()
    setIsDraggingOver(false)
  }

  const handleDrop = (event: React.DragEvent<HTMLTextAreaElement>) => {
    event.preventDefault()
    setIsDraggingOver(false)
    if (onImagePaste && event.dataTransfer.files.length > 0) {
      const files = Array.from(event.dataTransfer.files).filter((file) =>
        file.type.startsWith("image/"),
      )
      if (files.length > 0) {
        onImagePaste(files)
      }
    }
  }

  const handleSubmitMessage = () => {
    const message = value || textareaRef.current?.value || ""
    if (message.trim()) {
      onSubmit(message)
      onChange?.("")
      if (textareaRef.current) {
        textareaRef.current.value = ""
      }
    }
  }

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !disabled &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault()
      handleSubmitMessage()
    }
  }

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange?.(event.target.value)
  }

  return (
    <div
      data-testid="chat-input"
      className="flex min-h-14 w-full grow items-end justify-end gap-1"
    >
      <TextareaAutosize
        disabled={disabled}
        ref={textareaRef}
        name={name}
        placeholder={t(I18nKey.SUGGESTIONS$WHAT_TO_BUILD)}
        onKeyDown={handleKeyPress}
        onChange={handleChange}
        onFocus={onFocus}
        onBlur={onBlur}
        onPaste={handlePaste}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        value={value}
        minRows={1}
        maxRows={maxRows}
        data-dragging-over={isDraggingOver}
        className={cn(
          "grow resize-none self-center rounded-xl text-sm text-white outline-none ring-0 placeholder:text-neutral-400",
          "transition-all duration-200 ease-in-out",
          isDraggingOver
            ? "rounded-xl bg-neutral-600/50 px-2"
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
  )
}
