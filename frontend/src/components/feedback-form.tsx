import React from "react";
import hotToast from "react-hot-toast";
import ModalButton from "./buttons/ModalButton";
import { Feedback } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";

const FEEDBACK_VERSION = "1.0";
const VIEWER_PAGE = "https://www.all-hands.dev/share";

interface FeedbackFormProps {
  onClose: () => void;
  polarity: "positive" | "negative";
}

export function FeedbackForm({ onClose, polarity }: FeedbackFormProps) {
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const copiedToClipboardToast = () => {
    hotToast("Password copied to clipboard", {
      icon: "📋",
      position: "bottom-right",
    });
  };

  const onPressToast = (password: string) => {
    navigator.clipboard.writeText(password);
    copiedToClipboardToast();
  };

  const shareFeedbackToast = (
    message: string,
    link: string,
    password: string,
  ) => {
    hotToast(
      <div className="flex flex-col gap-1">
        <span>{message}</span>
        <a
          data-testid="toast-share-url"
          className="text-blue-500 underline"
          onClick={() => onPressToast(password)}
          href={link}
          target="_blank"
          rel="noreferrer"
        >
          Go to shared feedback
        </a>
        <span onClick={() => onPressToast(password)} className="cursor-pointer">
          Password: {password} <span className="text-gray-500">(copy)</span>
        </span>
      </div>,
      { duration: 10000 },
    );
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    const formData = new FormData(event.currentTarget);
    setIsSubmitting(true);

    const email = formData.get("email")?.toString() || "";
    const permissions = (formData.get("permissions")?.toString() ||
      "private") as "private" | "public";

    const feedback: Feedback = {
      version: FEEDBACK_VERSION,
      email,
      polarity,
      permissions,
      trajectory: [],
      token: "",
    };

    const response = await OpenHands.submitFeedback(feedback);
    const { message, feedback_id, password } = response.body; // eslint-disable-line
    const link = `${VIEWER_PAGE}?share_id=${feedback_id}`;
    shareFeedbackToast(message, link, password);
    setIsSubmitting(false);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6 w-full">
      <label className="flex flex-col gap-2">
        <span className="text-xs text-neutral-400">Email</span>
        <input
          required
          name="email"
          type="email"
          placeholder="Please enter your email"
          className="bg-[#27272A] px-3 py-[10px] rounded"
        />
      </label>

      <div className="flex gap-4 text-neutral-400">
        <label className="flex gap-2 cursor-pointer">
          <input
            name="permissions"
            value="private"
            type="radio"
            defaultChecked
          />
          Private
        </label>
        <label className="flex gap-2 cursor-pointer">
          <input name="permissions" value="public" type="radio" />
          Public
        </label>
      </div>

      <div className="flex gap-2">
        <ModalButton
          disabled={isSubmitting}
          type="submit"
          text="Submit"
          className="bg-[#4465DB] grow"
        />
        <ModalButton
          disabled={isSubmitting}
          text="Cancel"
          onClick={onClose}
          className="bg-[#737373] grow"
        />
      </div>
    </form>
  );
}
