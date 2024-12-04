import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Feedback } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";

type SubmitFeedbackArgs = {
  feedback: Feedback;
};

export const useSubmitFeedback = () =>
  useMutation({
    mutationFn: ({ feedback }: SubmitFeedbackArgs) =>
      OpenHands.submitFeedback(feedback),
    onError: (error) => {
      toast.error(error.message);
    },
  });
