import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Feedback } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

type SubmitFeedbackArgs = {
  feedback: Feedback;
};

export const useSubmitFeedback = () => {
  const { token } = useAuth();

  return useMutation({
    mutationFn: ({ feedback }: SubmitFeedbackArgs) =>
      OpenHands.submitFeedback(token || "", feedback),
    onError: (error) => {
      toast.error(error.message);
    },
  });
};
