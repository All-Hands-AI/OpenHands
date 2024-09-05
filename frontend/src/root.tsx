import {
  json,
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLoaderData,
} from "@remix-run/react";
import "./tailwind.css";
import "./index.css";
import React from "react";
import { useDisclosure } from "@nextui-org/react";
import { ActionFunctionArgs, LoaderFunctionArgs } from "@remix-run/node";
import CogTooth from "./assets/cog-tooth";
import ConnectToGitHubByTokenModal from "./components/modals/ConnectToGitHubByTokenModal";
import { SettingsForm } from "./routes/settings-form";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";
import { getAgents, getModels } from "./api/open-hands";
import { commitSession, getSession } from "./sessions";
import { isGitHubErrorReponse, retrieveGitHubUser } from "./api/github";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"));
  const tosAccepted = session.get("tosAccepted");
  const ghToken = session.get("ghToken");

  let user: GitHubUser | null = null;
  if (ghToken) {
    const data = await retrieveGitHubUser(ghToken);
    if (!isGitHubErrorReponse(data)) user = data;
    // TODO: display error message in the UI
    else console.warn(data.status, data.message);
  }

  return json({
    user,
    models: await getModels(),
    agents: await getAgents(),
    tosAccepted,
  });
};

export const action = async ({ request }: ActionFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"));
  const formData = await request.formData();

  const tos = formData.get("tos")?.toString();
  if (tos === "on") {
    session.set("tosAccepted", true);
  }

  const token = formData.get("token")?.toString();
  if (token) {
    session.set("ghToken", token);
  }

  return json(null, {
    headers: {
      "Set-Cookie": await commitSession(session),
    },
  });
};

export default function App() {
  const { user, models, agents, tosAccepted } = useLoaderData<typeof loader>();

  const {
    isOpen: settingsModalIsOpen,
    onOpen: onSettingsModalOpen,
    onOpenChange: onSettingsModalOpenChange,
  } = useDisclosure();

  return (
    <div className="bg-root-primary p-3 h-screen flex gap-3">
      <aside className="px-1 flex flex-col gap-[15px]">
        <Link data-testid="link-to-main" to="/">
          <AllHandsLogo width={34} height={23} />
        </Link>
        <nav className="py-[18px] flex flex-col items-center gap-[18px]">
          <img
            src={user?.avatar_url}
            alt="User avatar"
            className="w-8 h-8 rounded-full"
          />
          <button
            type="button"
            className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
            onClick={onSettingsModalOpen}
            aria-label="Settings"
          >
            <CogTooth />
          </button>
        </nav>
      </aside>
      <div className="w-full relative">
        <Outlet />
        {!tosAccepted && (
          <ModalBackdrop>
            <ConnectToGitHubByTokenModal />
          </ModalBackdrop>
        )}
        {settingsModalIsOpen && (
          <ModalBackdrop>
            <div className="bg-root-primary w-[384px] p-6 rounded-xl flex flex-col gap-2">
              <span className="text-xl leading-6 font-semibold -tracking-[0.01em">
                AI Provider Configuration
              </span>
              <p className="text-xs text-[#A3A3A3]">
                To continue, connect an OpenAI, Anthropic, or other LLM account
              </p>
              <SettingsForm
                settings={{}}
                models={models}
                agents={agents}
                onClose={onSettingsModalOpenChange}
              />
            </div>
          </ModalBackdrop>
        )}
      </div>
    </div>
  );
}
