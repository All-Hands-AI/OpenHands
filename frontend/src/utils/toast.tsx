import toast from "react-hot-toast";

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
    // Calculate duration based on message length (minimum 5 seconds for settings messages)
    const calculateDuration = (message: string): number => {
      const wordsPerMinute = 200;
      const charactersPerMinute = wordsPerMinute * 5;
      const charactersPerSecond = charactersPerMinute / 60;
      const readingTimeMs = (message.length / charactersPerSecond) * 1000;
      const durationWithBuffer = readingTimeMs * 1.5;
      return Math.min(Math.max(durationWithBuffer, 5000), 10000);
    };

    toast(msg, {
      position: "bottom-right",
      className: "bg-tertiary",
      duration: calculateDuration(msg),
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
