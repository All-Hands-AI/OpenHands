import { ClientActionFunctionArgs, json } from "@remix-run/react";
import { createGitHubRepository } from "#/api/github";

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const token = formData.get("ghToken")?.toString();
  const repositoryName = formData.get("repositoryName")?.toString();
  const repositoryDescription = formData
    .get("repositoryDescription")
    ?.toString();

  if (token && repositoryName) {
    const response = await createGitHubRepository(
      token,
      repositoryName,
      repositoryDescription,
    );

    return json(response);
  }

  return json(null);
};
