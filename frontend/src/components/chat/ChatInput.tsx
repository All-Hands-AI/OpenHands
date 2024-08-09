import { Textarea } from "@nextui-org/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { VscArrowUp, VscFileMedia } from "react-icons/vsc";
import { twMerge } from "tailwind-merge";
import { I18nKey } from "#/i18n/declaration";

interface ChatInputProps {
  disabled?: boolean;
  onSendMessage: (message: string, image_urls: string[]) => void;
}

function ChatInput({ disabled = false, onSendMessage }: ChatInputProps) {
  const { t } = useTranslation();

  const [message, setMessage] = React.useState("");
  const [files, setFiles] = React.useState<File[]>([]);
  // This is true when the user is typing in an IME (e.g., Chinese, Japanese)
  const [isComposing, setIsComposing] = React.useState(false);

  const convertImageToBase64 = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        resolve(reader.result as string);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

  const handleSendChatMessage = async () => {
    if (message.trim()) {
      let base64images: string[] = [];
      if (files.length > 0) {
        base64images = await Promise.all(
          files.map((file) => convertImageToBase64(file)),
        );
      }
      onSendMessage(message, base64images);
      setMessage("");
      setFiles([]);
    }
  };

  const onKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !isComposing) {
      event.preventDefault(); // prevent a new line
      if (!disabled) {
        handleSendChatMessage();
      }
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFiles((prev) => [...prev, ...Array.from(event.target.files!)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prevFiles) => prevFiles.filter((_, i) => i !== index));
  };

  const handlePaste = (event: React.ClipboardEvent<HTMLInputElement>) => {
    const clipboardItems = Array.from(event.clipboardData.items);
    const pastedFiles: File[] = [];
    clipboardItems.forEach((item) => {
      if (item.type.startsWith("image/")) {
        const file = item.getAsFile();
        if (file) {
          pastedFiles.push(file);
        }
      }
    });
    if (pastedFiles.length > 0) {
      setFiles((prevFiles) => [...prevFiles, ...pastedFiles]);
      event.preventDefault();
    }
  };

  return (
    <div className="w-full relative text-base flex pt-3">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={onKeyPress}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        placeholder={t(I18nKey.CHAT_INTERFACE$INPUT_PLACEHOLDER)}
        onPaste={handlePaste}
        className="pb-3 px-3"
        classNames={{
          inputWrapper: "bg-neutral-700 border border-neutral-600 rounded-lg",
          input: "pr-16 text-neutral-400",
        }}
        maxRows={10}
        minRows={1}
        variant="bordered"
      />
      <label
        htmlFor="file-input"
        className={twMerge(
          "bg-transparent border rounded-lg p-1 border-white hover:opacity-80 cursor-pointer select-none absolute right-16 bottom-[19px] transition active:bg-white active:text-black",
          disabled
            ? "cursor-not-allowed border-neutral-400 text-neutral-400"
            : "hover:bg-neutral-500",
        )}
        aria-label={t(I18nKey.CHAT_INTERFACE$TOOLTIP_UPLOAD_IMAGE)}
      >
        <VscFileMedia />
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
          id="file-input"
          multiple
        />
      </label>
      <button
        type="button"
        onClick={handleSendChatMessage}
        disabled={disabled}
        className={twMerge(
          "bg-transparent border rounded-lg p-1 border-white hover:opacity-80 cursor-pointer select-none absolute right-5 bottom-[19px] transition active:bg-white active:text-black",
          disabled
            ? "cursor-not-allowed border-neutral-400 text-neutral-400"
            : "hover:bg-neutral-500",
        )}
        aria-label={t(I18nKey.CHAT_INTERFACE$TOOLTIP_SEND_MESSAGE)}
      >
        <VscArrowUp />
      </button>
      {files.length > 0 && (
        <div className="absolute bottom-16 right-5 flex space-x-2 p-4 border-1 border-neutral-500 bg-neutral-800 rounded-lg">
          {files.map((file, index) => (
            <div key={index} className="relative">
              <img
                src={URL.createObjectURL(file)}
                alt="upload preview"
                className="w-24 h-24 object-contain rounded bg-white"
              />
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="absolute top-0 right-0 bg-black border border-grey-200 text-white rounded-full w-5 h-5 flex pb-1 items-center justify-center"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ChatInput;
