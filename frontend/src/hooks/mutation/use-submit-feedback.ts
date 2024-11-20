import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Feedback, FeedbackResponse } from "#/api/open-hands.types";
import { getToken } from "#/services/auth";

export const useSubmitFeedback = () =>
  useMutation({
    mutationFn: async (variables: { feedback: Feedback }) => {
      const response = await fetch("/api/submit-feedback", {
        method: "POST",
        body: JSON.stringify(variables.feedback),
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to submit feedback");
      }

      return (await response.json()) as FeedbackResponse;
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });
