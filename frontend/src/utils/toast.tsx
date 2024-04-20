import toast from "react-hot-toast";

const idMap = new Map<string, string>();

export default {
  stickyError: (id: string, msg: string) => {
    if (idMap.has(id)) return; // prevent duplicate toast
    const toastId = toast.loading(msg, {
      // icon: "👏",
      // style: {
      //   borderRadius: "10px",
      //   background: "#333",
      //   color: "#fff",
      // },
      style: {
        background: "#ef4444",
        color: "#fff",
        lineBreak: "anywhere",
      },
      iconTheme: {
        primary: "#ef4444",
        secondary: "#fff",
      },
    });
    idMap.set(id, toastId);
  },
  stickySuccess: (id: string, msg: string) => {
    const toastId = idMap.get(id);
    if (toastId === undefined) return;
    if (toastId) {
      toast.success(msg, {
        id: toastId,
        style: {
          background: "#333",
          color: "#fff",
          lineBreak: "anywhere",
        },
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
      style: {
        background: "#333",
        color: "#fff",
        lineBreak: "anywhere",
      },
    });
  },

  info: (msg: string) => {
    toast(msg, {
      position: "top-center",
      className: "bg-neutral-700",

      style: {
        background: "#333",
        color: "#fff",
        lineBreak: "anywhere",
      },
    });
  },
};
