import {
  ClientLoaderFunctionArgs,
  json,
  redirect,
  useLoaderData,
} from "@remix-run/react";
import OpenHands from "#/api/open-hands";

export const clientLoader = async ({ request }: ClientLoaderFunctionArgs) => {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");

  if (code) {
    // request to the server to exchange the code for a token
    const { access_token: accessToken } =
      await OpenHands.getGitHubAccessToken(code);
    // set the token in local storage
    localStorage.setItem("ghToken", accessToken);
    return redirect("/");
  }

  return json({ error: "No code provided" }, { status: 400 });
};

function OAuthGitHubCallback() {
  const { error } = useLoaderData<typeof clientLoader>();
  if (error) {
    return (
      <div>
        <h1>Error</h1>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Redirecting...</h1>
    </div>
  );
}

export default OAuthGitHubCallback;
