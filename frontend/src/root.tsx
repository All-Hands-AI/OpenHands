import {
  ClientActionFunctionArgs,
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  ShouldRevalidateFunctionArgs,
  defer,
  json,
  useLoaderData,
  useNavigation,
} from "@remix-run/react";
import "./tailwind.css";
import "./index.css";
import React from "react";
import { useDisclosure } from "@nextui-org/react";
import CogTooth from "./assets/cog-tooth";
import ConnectToGitHubByTokenModal from "./components/modals/ConnectToGitHubByTokenModal";
import { SettingsForm } from "./routes/settings-form";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";
import { isGitHubErrorReponse, retrieveGitHubUser } from "./api/github";
import { getAgents, getModels } from "./api/open-hands";
import LoadingProjectModal from "./components/modals/LoadingProject";

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

export const clientLoader = async () => {
  const tosAccepted = localStorage.getItem("tosAccepted") === "true";
  const ghToken = localStorage.getItem("ghToken");

  const models = getModels();
  const agents = getAgents();

  let user: GitHubUser | null = null;
  if (ghToken) {
    const data = await retrieveGitHubUser(ghToken);
    if (!isGitHubErrorReponse(data)) user = data;
  }

  return defer({
    user,
    models,
    agents,
    tosAccepted,
  });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const ghToken = formData.get("token")?.toString();
  const tosAccepted = formData.get("tos")?.toString();

  if (tosAccepted) {
    localStorage.setItem("tosAccepted", "true");
  }

  if (ghToken) {
    localStorage.setItem("ghToken", ghToken);
  }

  return json(null);
};

export const shouldRevalidate = ({ formData }: ShouldRevalidateFunctionArgs) =>
  !!formData?.get("tos");

export default function App() {
  const navigation = useNavigation();
  const { user, models, agents, tosAccepted } =
    useLoaderData<typeof clientLoader>();

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
        {navigation.state === "loading" && (
          <ModalBackdrop>
            <LoadingProjectModal />
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
                // @ts-expect-error - TODO: fix this
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

export function HydrateFallback() {
  return <p>Loading...</p>;
}
