import { ClientActionFunctionArgs, json, redirect } from "@remix-run/react";

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const githubAuthUrl = formData.get("githubAuthUrl")?.toString();

  if (githubAuthUrl) redirect(githubAuthUrl);
  return json(null);
};
