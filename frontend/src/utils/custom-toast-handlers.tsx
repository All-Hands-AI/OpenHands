import toast, { Toast } from "react-hot-toast";
import CloseIcon from "#/icons/close.svg?react";
import { cn } from "./utils";

interface CustomToastProps {
  toast: Toast;
  variant: "success" | "error";
}

function CustomToast({
  toast: t,
  variant,
  children,
}: React.PropsWithChildren<CustomToastProps>) {
  return (
    <div
      className={cn(
        "w-[448px] border-l-4 pl-4 pr-3 py-3 rounded-lg flex gap-3 items-start",
        t.visible ? "animate-enter" : "animate-leave",
        variant === "error" && "bg-[#D0493D] border-[#A92418]",
        variant === "success" && "bg-[#44671F] border-[#5F8F2B]",
      )}
    >
      <p className="grow">{children}</p>
      <button type="button" onClick={() => toast.dismiss(t.id)}>
        <CloseIcon />
      </button>
    </div>
  );
}

export const displayErrorToast = (error: string) => {
  toast.custom((t) => (
    <CustomToast toast={t} variant="error">
      {error}
    </CustomToast>
  ));
};

export const displaySuccessToast = (message: string) => {
  toast.custom((t) => (
    <CustomToast toast={t} variant="success">
      {message}
    </CustomToast>
  ));
};
