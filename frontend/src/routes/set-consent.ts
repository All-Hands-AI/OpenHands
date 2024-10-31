import { ClientActionFunctionArgs, json } from "@remix-run/react";

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const userConsents = formData.get("analytics") === "on";
  localStorage.setItem("analytics-consent", userConsents.toString());

  return json(null);
};
