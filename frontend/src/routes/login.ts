import { ClientActionFunctionArgs, json } from "@remix-run/react";

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const githubToken = formData.get("ghToken")?.toString();

  if (githubToken) localStorage.setItem("ghToken", githubToken);
  return json({ success: true });
};
