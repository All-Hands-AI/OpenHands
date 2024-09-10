import React from "react";
import { Form, Link, useNavigation, useSubmit } from "@remix-run/react";
import Send from "#/assets/send.svg?react";
import Clip from "#/assets/clip.svg?react";
import { useSocket } from "#/context/socket";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";
import ConfirmResetWorkspaceModal from "#/components/modals/confirmation-modals/ConfirmResetWorkspaceModal";
import { cn } from "#/utils/utils";

export function TaskForm() {
  const { isConnected } = useSocket();
  const navigation = useNavigation();
  const formRef = React.useRef<HTMLFormElement>(null);
  const submit = useSubmit();

  const [hasText, setHasText] = React.useState(false);
  const [resetWorkspaceModalOpen, setResetWorkspaceModalOpen] =
    React.useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setHasText(!!e.target.value);
  };

  return (
    <div className="flex flex-col gap-2">
      {isConnected && (
        <Link
          to="/app"
          className="text-xs -tracking-tighter text-green-400 hover:underline self-end"
        >
          Go back to ongoing conversation
        </Link>
      )}
      <Form
        ref={formRef}
        method="post"
        className="relative"
        onSubmit={(event) => {
          if (isConnected) {
            event.preventDefault();
            setResetWorkspaceModalOpen(true);
          }
        }}
      >
        <input
          name="q"
          type="text"
          placeholder="What do you want to build?"
          onChange={handleChange}
          className={cn(
            "bg-[#404040] placeholder:text-[#A3A3A3] border border-[#525252] w-[600px] rounded-lg px-[16px] py-[18px] text-[17px] leading-5",
            "focus:bg-[#525252]",
          )}
        />
        {hasText && (
          <button
            type="submit"
            aria-label="Submit"
            className="absolute right-4 top-1/2 transform -translate-y-1/2"
            disabled={navigation.state === "loading"}
          >
            <Send width={24} height={24} />
          </button>
        )}
      </Form>
      <button
        type="button"
        className="flex self-start items-center text-[#A3A3A3] text-xs leading-[18px] -tracking-[0.08px]"
      >
        <Clip width={16} height={16} />
        Attach a file
      </button>

      {resetWorkspaceModalOpen && (
        <ModalBackdrop>
          <ConfirmResetWorkspaceModal
            onConfirm={() => {
              setResetWorkspaceModalOpen(false);
              const formData = new FormData(formRef.current ?? undefined);
              formData.set("reset", "true");
              submit(formData, { method: "POST" });
            }}
            onCancel={() => setResetWorkspaceModalOpen(false)}
          />
        </ModalBackdrop>
      )}
    </div>
  );
}
