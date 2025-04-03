import { BrandButton } from "#/components/features/settings/brand-button";
import { HeroHeading } from "#/components/shared/hero-heading";
import { TaskForm } from "#/components/shared/task-form";
// import { useConfig } from "#/hooks/query/use-config";
// import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { I18nKey } from "#/i18n/declaration";
import { useConnectModal } from "@rainbow-me/rainbowkit";
import { t } from "i18next";
import React, { useEffect } from "react";
import { useNavigate } from "react-router";
import { useDispatch } from "react-redux";
import { useAccount } from "wagmi";
import { useSettings } from "#/hooks/query/use-settings";
import { useUserConversations } from "#/hooks/query/use-user-conversations";
import { useTranslation } from "react-i18next";

function Home() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { data: settings } = useSettings();
  const { data: conversations } = useUserConversations();
  const { isConnected } = useAccount();
  const formRef = React.useRef<HTMLFormElement>(null);

  // const { data: config } = useConfig();
  // const { data: user } = useGitHubUser();
  const { openConnectModal } = useConnectModal();

  // const gitHubAuthUrl = useGitHubAuthUrl({
  //   appMode: config?.APP_MODE || null,
  //   gitHubClientId: config?.GITHUB_CLIENT_ID || null,
  // });

  useEffect(() => {
    if (conversations?.length) {
      navigate(`/oh/${conversations[0].conversation_id}`);
    }
  }, [conversations?.length]);

  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full rounded-xl flex flex-col items-center justify-center relative overflow-y-auto px-2"
    >
      <HeroHeading />
      <div className="flex flex-col gap-1 w-full mt-8 md:w-[600px] items-center">
        <div className="flex flex-col gap-2 w-full">
          {isConnected ? <TaskForm ref={formRef} /> :
            <div className="flex flex-col gap-2 w-full">
              <div>Welcome to Thesis! We're currently in private beta.
                To get started, Please enter connect your wallet.
              </div>
              <BrandButton
                testId="connect-your-wallet"
                type="button"
                variant="secondary"
                className="w-full text-content border-content"
                onClick={openConnectModal}
              >
                {t(I18nKey.BUTTON$CONNECT_WALLET)}
              </BrandButton>
            </div>}
        </div>

        {/* <div className="flex gap-4 w-full flex-col md:flex-row mt-8">
          <GitHubRepositoriesSuggestionBox
            handleSubmit={() => formRef.current?.requestSubmit()}
            gitHubAuthUrl={gitHubAuthUrl}
            user={user || null}
          />
          {ENABLE_TRAJECTORY_REPLAY() && (
            <ReplaySuggestionBox
              onChange={async (event) => {
                if (event.target.files) {
                  const json = event.target.files[0];
                  dispatch(setReplayJson(await convertFileToText(json)));
                  posthog.capture("json_file_uploaded");
                  formRef.current?.requestSubmit();
                } else {
                  // TODO: handle error
                }
              }}
            />
          )}
        </div>
        <div className="w-full flex justify-start mt-2 ml-2">
          <CodeNotInGitHubLink />
        </div> */}
      </div>
    </div>
  );
}

export default Home;
