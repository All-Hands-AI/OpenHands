import { Textarea } from "@nextui-org/react";
import React, { ChangeEvent, KeyboardEvent, useState } from "react";
// import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { twMerge } from "tailwind-merge";
import i18next from "i18next";
import useInputComposition from "../hooks/useInputComposition";
import { sendChatMessage } from "../services/chatService";
import { RootState } from "../store";

function Input() {
  // const { t } = useTranslation();
  const { initialized } = useSelector((state: RootState) => state.task);
  const [inputMessage, setInputMessage] = useState("");

  const handleSendMessage = () => {
    if (inputMessage.trim() !== "") {
      sendChatMessage(inputMessage);
      setInputMessage("");
    }
  };

  const { onCompositionEnd, onCompositionStart, isComposing } =
    useInputComposition();

  const handleChangeInputMessage = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.value !== "\n") {
      setInputMessage(e.target.value);
    }
  };

  const handleSendMessageOnEnter = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      // Prevent "Enter" from sending during IME input (e.g., Chinese, Japanese)
      if (isComposing) {
        return;
      }
      e.preventDefault();
      e.stopPropagation();
      handleSendMessage();
    }
  };

  return (
    <div className="w-full relative text-base">
      <Textarea
        className="py-4 px-4"
        classNames={{
          inputWrapper: "bg-neutral-700",
          input: "pr-16 py-2",
        }}
        value={inputMessage}
        maxRows={10}
        minRows={1}
        variant="bordered"
        onChange={handleChangeInputMessage}
        onKeyDown={handleSendMessageOnEnter}
        onCompositionStart={onCompositionStart}
        onCompositionEnd={onCompositionEnd}
        placeholder={i18next.t("CHAT_INTERFACE$INPUT_PLACEHOLDER")}
      />
      <button
        type="button"
        className={twMerge(
          "bg-transparent border-none rounded py-2.5 px-5 hover:opacity-80 cursor-pointer select-none absolute right-5 bottom-6",
          !initialized && "cursor-not-allowed opacity-80",
        )}
        onClick={handleSendMessage}
        disabled={!initialized}
        aria-label="Send message"
      >
        {i18next.t("CHAT_INTERFACE$INPUT_SEND_MESSAGE_BUTTON_CONTENT")}
      </button>
    </div>
  );
}

export default Input;
