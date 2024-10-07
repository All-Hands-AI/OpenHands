import toast, { Toast } from "react-hot-toast";

interface ErrorToastProps {
  id: Toast["id"];
  error: string;
}

export function ErrorToast({ id, error }: ErrorToastProps) {
  return (
    <div className="flex items-center justify-between w-full h-full">
      <span>{error}</span>
      <button
        type="button"
        onClick={() => toast.dismiss(id)}
        className="bg-neutral-500 px-1 rounded h-full"
      >
        Close
      </button>
    </div>
  );
}
