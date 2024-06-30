import toast from "react-hot-toast";

const idMap = new Map<string, string>();

const commonToastClasses = "text-sm py-3 px-4 max-w-[600px] w-full break-words";

export default {
  error: (id: string, msg: string) => {
    if (idMap.has(id)) return; // prevent duplicate toast
    const toastId = toast(msg, {
      duration: 4000,
      className: `${commonToastClasses} bg-error text-white`,
    });
    idMap.set(id, toastId);
  },
  success: (id: string, msg: string) => {
    const toastId = idMap.get(id);
    if (toastId === undefined) return;
    if (toastId) {
      toast.success(msg, {
        id: toastId,
        duration: 4000,
        className: `${commonToastClasses} bg-success text-white`,
      });
    }
    idMap.delete(id);
  },
  settingsChanged: (msg: string) => {
    toast(msg, {
      position: "bottom-right",
      icon: "⚙️",
      className: `${commonToastClasses} bg-neutral text-foreground max-w-[800px]`,
    });
  },
  info: (msg: string) => {
    toast(msg, {
      position: "top-center",
      className: `${commonToastClasses} bg-info text-white`,
    });
  },
};
