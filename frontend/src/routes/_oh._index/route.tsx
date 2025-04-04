import { BrandButton } from "#/components/features/settings/brand-button";
import { HeroHeading } from "#/components/shared/hero-heading";
import { TaskForm } from "#/components/shared/task-form";
// import { useConfig } from "#/hooks/query/use-config";
// import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useSettings } from "#/hooks/query/use-settings";
import { I18nKey } from "#/i18n/declaration";
import { useGetJwt } from "#/zutand-stores/persist-config/selector";
import { useConnectModal } from "@rainbow-me/rainbowkit";
import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useAccount } from "wagmi";

function Home() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { data: settings } = useSettings();
  const { isConnected } = useAccount();
  const jwt = useGetJwt();
  const formRef = React.useRef<HTMLFormElement>(null);

  // const { data: config } = useConfig();
  // const { data: user } = useGitHubUser();
  const { openConnectModal } = useConnectModal();

  // const gitHubAuthUrl = useGitHubAuthUrl({
  //   appMode: config?.APP_MODE || null,
  //   gitHubClientId: config?.GITHUB_CLIENT_ID || null,
  // });

  const isUserLoggedIn = !!jwt && !!isConnected;

  return (
    <div
      data-testid="home-screen"
      className="bg-[#080808] h-full rounded-xl flex flex-col items-center justify-center relative overflow-y-auto px-2"
    >
      <HeroHeading />
      <div className="flex flex-col gap-1 w-full mt-8 md:w-[600px] items-center">
        <div className="flex flex-col gap-2 w-full">
          {isUserLoggedIn ? (
            <TaskForm ref={formRef} />
          ) : (
            <div className="flex flex-col gap-2 w-full">
              <div className="text-tertiary-light text-center">
                Welcome to Thesis! We're currently in private beta.
                <br /> To get started, Please enter connect your wallet.
              </div>

              <BrandButton
                testId="connect-your-wallet"
                type="button"
                variant="secondary"
                className="w-full text-tertiary font-bold hover:brightness-110 bg-tertiary-light border-content mt-2 uppercase"
                onClick={openConnectModal}
              >
                {t(I18nKey.BUTTON$CONNECT_WALLET)}
              </BrandButton>
            </div>
          )}
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
