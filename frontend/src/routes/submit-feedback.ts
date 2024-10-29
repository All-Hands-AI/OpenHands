import { ClientActionFunctionArgs, json } from "@remix-run/react";
import { Feedback } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";

const VIEWER_PAGE = "https://www.all-hands.dev/share";

const isFeedback = (feedback: unknown): feedback is Feedback => {
  if (typeof feedback !== "object" || feedback === null) {
    return false;
  }

  return (
    "version" in feedback &&
    "email" in feedback &&
    "token" in feedback &&
    "feedback" in feedback &&
    "permissions" in feedback &&
    "trajectory" in feedback
  );
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const feedback = formData.get("feedback")?.toString();
  const token = localStorage.getItem("token");

  if (token && feedback) {
    const parsed = JSON.parse(feedback);
    if (isFeedback(parsed)) {
      try {
        const response = await OpenHands.sendFeedback(token, parsed);
        if (response.statusCode === 200) {
          const { message, feedback_id: feedbackId, password } = response.body;
          const link = `${VIEWER_PAGE}?share_id=${feedbackId}`;
          return json({
            success: true,
            data: { message, link, password },
          });
        }
      } catch (error) {
        return json({ success: false, data: null });
      }
    }
  }

  return json({ success: false, data: null });
};
