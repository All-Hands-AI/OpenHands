import toast from "react-hot-toast";

export const displayErrorToast = (error: string) => {
  toast.error(error, {
    position: "top-right",
    style: {
      background: "#454545",
      border: "1px solid #717888",
      color: "#fff",
      borderRadius: "4px",
    },
  });
};

export const displaySuccessToast = (message: string) => {
  toast.success(message, {
    position: "top-right",
    style: {
      background: "#454545",
      border: "1px solid #717888",
      color: "#fff",
      borderRadius: "4px",
    },
  });
};
