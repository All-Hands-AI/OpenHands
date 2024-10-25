import ModalButton from "./buttons/ModalButton";

interface FeedbackFormProps {
  onSubmit: (permissions: "private" | "public", email: string) => void;
  onClose: () => void;
  isSubmitting?: boolean;
}

export function FeedbackForm({
  onSubmit,
  onClose,
  isSubmitting,
}: FeedbackFormProps) {
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    const formData = new FormData(event.currentTarget);

    const email = formData.get("email")?.toString();
    const permissions = formData.get("permissions")?.toString() as
      | "private"
      | "public"
      | undefined;

    if (email) onSubmit(permissions || "private", email);
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
