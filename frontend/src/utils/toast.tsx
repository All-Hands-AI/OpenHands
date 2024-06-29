import toast from "react-hot-toast";

const idMap = new Map<string, string>();

const commonToastStyle = {
  background: "#333",
  color: "#fff",
  wordBreak: "break-word" as const,
  fontSize: "0.85rem",
  padding: "12px",
  maxWidth: "500px",
  width: "100%",
};

export default {
  error: (id: string, msg: string) => {
    if (idMap.has(id)) return; // prevent duplicate toast
    const toastId = toast(msg, {
      duration: 4000,
      style: {
        ...commonToastStyle,
        background: "#ef4444",
      },
      iconTheme: {
        primary: "#ef4444",
        secondary: "#fff",
      },
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
        style: commonToastStyle,
        iconTheme: {
          primary: "#333",
          secondary: "#fff",
        },
      });
    }
    idMap.delete(id);
  },
  settingsChanged: (msg: string) => {
    toast(msg, {
      position: "bottom-right",
      className: "bg-neutral-700",
      icon: "⚙️",
      style: commonToastStyle,
    });
  },
  info: (msg: string) => {
    toast(msg, {
      position: "top-center",
      className: "bg-neutral-700",
      style: commonToastStyle,
    });
  },
};
