import toast from "react-hot-toast";
import { ErrorToast } from "#/components/error-toast";

export const displayErrorToast = (error: string) =>
  toast((t) => <ErrorToast id={t.id} error={error} />, {
    style: {
      background: "#C63143",
      color: "#fff",
      fontSize: "12px",
      fontWeight: "500",
      lineHeight: "20px",
      borderRadius: "4px",
      width: "336px",
    },
    duration: Infinity,
    position: "bottom-right",
  });
