import toast from "react-hot-toast";
import { calculateToastDuration } from "./toast-duration";

const idMap = new Map<string, string>();

export default {
  error: (id: string, msg: string) => {
    if (idMap.has(id)) return; // prevent duplicate toast
    const toastId = toast(msg, {
      duration: 4000,
      style: {
        background: "#ef4444",
        color: "#fff",
      },
      iconTheme: {
        primary: "#ef4444",
        secondary: "#fff",
      },
    });
    idMap.set(id, toastId);
  },
  success: (id: string, msg: string, duration: number = 4000) => {
    if (idMap.has(id)) return; // prevent duplicate toast
    const toastId = toast.success(msg, {
      duration,
      style: {
        background: "#333",
        color: "#fff",
      },
      iconTheme: {
        primary: "#333",
        secondary: "#fff",
      },
    });
    idMap.set(id, toastId);
  },
  settingsChanged: (msg: string) => {
    toast(msg, {
      position: "bottom-right",
      className: "bg-tertiary",
      duration: calculateToastDuration(msg, 5000),
      icon: "⚙️",
      style: {
        background: "#333",
        color: "#fff",
      },
    });
  },

  info: (msg: string) => {
    toast(msg, {
      position: "top-center",
      className: "bg-tertiary",

      style: {
        background: "#333",
        color: "#fff",
        lineBreak: "anywhere",
      },
    });
  },
};
