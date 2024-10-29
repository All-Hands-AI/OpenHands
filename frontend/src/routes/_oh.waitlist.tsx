import {
  ClientLoaderFunctionArgs,
  json,
  redirect,
  useLoaderData,
} from "@remix-run/react";
import Clipboard from "#/assets/clipboard.svg?react";
import { generateGitHubAuthUrl } from "#/utils/generate-github-auth-url";
import ModalButton from "#/components/buttons/ModalButton";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import { userIsAuthenticated } from "#/utils/user-is-authenticated";

export const clientLoader = async ({ request }: ClientLoaderFunctionArgs) => {
  const isSaas = window.__APP_MODE__ === "saas";
  const clientId = window.__GITHUB_CLIENT_ID__;

  let githubAuthUrl: string | null = null;
  if (isSaas && clientId) {
    const requestUrl = new URL(request.url);
    githubAuthUrl = generateGitHubAuthUrl(clientId, requestUrl);
  }

  const ghToken = localStorage.getItem("ghToken");
  const isInWaitlist = await userIsAuthenticated(ghToken);

  if (isInWaitlist) return redirect("/");

  return json({ ghToken, githubAuthUrl, isInWaitlist });
};

function Waitlist() {
  const { ghToken, githubAuthUrl, isInWaitlist } =
    useLoaderData<typeof clientLoader>();

  const isSignedInButNotInWaitlist = ghToken && !isInWaitlist;

  return (
    <div className="bg-neutral-800 h-full flex items-center justify-center rounded-xl">
      <div className="w-[384px] flex flex-col gap-6 bg-neutral-900 rounded-xl p-6">
        <Clipboard className="w-14 self-center" />

        <div className="flex flex-col gap-2">
          <h1 className="text-[20px] leading-6 -tracking-[0.01em] font-semibold">
            {isSignedInButNotInWaitlist
              ? "You're not in the waitlist yet!"
              : "Join the waitlist"}
          </h1>
          <p className="text-neutral-400 text-xs">
            Please click{" "}
            <a
              href="https://www.all-hands.dev/join-waitlist"
              target="_blank"
              rel="noreferrer noopener"
              className="text-blue-500"
            >
              here
            </a>{" "}
            to join the waitlist
            {!isSignedInButNotInWaitlist
              ? " or press the button below to sign in."
              : "."}
          </p>
        </div>

        {!ghToken && (
          <ModalButton
            text="Connect to GitHub"
            icon={<GitHubLogo width={20} height={20} />}
            className="bg-[#791B80] w-full"
            onClick={() => {
              if (githubAuthUrl) {
                window.location.href = githubAuthUrl;
              }
            }}
          />
        )}
      </div>
    </div>
  );
}

export default Waitlist;
