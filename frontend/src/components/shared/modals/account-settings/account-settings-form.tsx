import React from "react";
import { useTranslation } from "react-i18next";
import { useMutation } from "@tanstack/react-query";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "../confirmation-modals/base-modal";
import { ModalBody } from "../modal-body";
import { AvailableLanguages } from "#/i18n";
import { I18nKey } from "#/i18n/declaration";
import { useAuth } from "#/context/auth-context";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { ModalButton } from "../../buttons/modal-button";
import { CustomInput } from "../../custom-input";
import { FormFieldset } from "../../form-fieldset";
import { useConfig } from "#/hooks/query/use-config";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { UserBalance } from "#/components/features/payment/user-balance";
import { useCurrentSettings } from "#/context/settings-context";
import OpenHands from "#/api/open-hands";
import { useBalance } from "#/hooks/query/use-balance";
import { StripeCheckoutForm } from "#/components/features/payment/stripe-checkout-form";
import { cn } from "#/utils/utils";

interface AccountSettingsFormProps {
  onClose: () => void;
  selectedLanguage: string;
  analyticsConsent: string | null;
}

export function AccountSettingsForm({
  onClose,
  selectedLanguage,
  analyticsConsent,
}: AccountSettingsFormProps) {
  const { t } = useTranslation();
  const user = useGitHubUser();
  const { gitHubToken, setGitHubToken, logout } = useAuth();
  const { data: config } = useConfig();
  const { saveUserSettings } = useCurrentSettings();
  const { data: balance } = useBalance(user.data?.login ?? "");
  const {
    data: clientSecret,
    mutate: getClientSecret,
    isPending: isGettingClientSecret,
  } = useMutation({
    mutationFn: OpenHands.createCheckoutSession,
  });

  const shouldRenderStripeForm = !!clientSecret;

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);

    const ghToken = formData.get("ghToken")?.toString();
    const language = formData.get("language")?.toString();
    const analytics = formData.get("analytics")?.toString() === "on";

    if (ghToken) setGitHubToken(ghToken);

    // The form returns the language label, so we need to find the corresponding
    // language key to save it in the settings
    if (language) {
      const languageKey = AvailableLanguages.find(
        ({ label }) => label === language,
      )?.value;

      if (languageKey) await saveUserSettings({ LANGUAGE: languageKey });
    }

    handleCaptureConsent(analytics);
    const ANALYTICS = analytics.toString();
    localStorage.setItem("analytics-consent", ANALYTICS);

    onClose();
  };

  return (
    <ModalBody
      testID="account-settings-form"
      className={cn(shouldRenderStripeForm && "p-1 block bg-white")}
    >
      {shouldRenderStripeForm && (
        <StripeCheckoutForm clientSecret={clientSecret} />
      )}

      {!shouldRenderStripeForm && (
        <form className="flex flex-col w-full gap-6" onSubmit={handleSubmit}>
          <div className="w-full flex flex-col gap-2">
            <BaseModalTitle title={t(I18nKey.ACCOUNT_SETTINGS$TITLE)} />

            {config?.APP_MODE === "saas" && config?.APP_SLUG && (
              <a
                href={`https://github.com/apps/${config.APP_SLUG}/installations/new`}
                target="_blank"
                rel="noreferrer noopener"
                className="underline"
              >
                {t(I18nKey.GITHUB$CONFIGURE_REPOS)}
              </a>
            )}
            {balance && (
              <UserBalance
                balance={balance}
                isLoading={isGettingClientSecret}
                onTopUp={() => getClientSecret()}
              />
            )}

            <FormFieldset
              id="language"
              label={t(I18nKey.LANGUAGE$LABEL)}
              defaultSelectedKey={selectedLanguage}
              isClearable={false}
              items={AvailableLanguages.map(({ label, value: key }) => ({
                key,
                value: label,
              }))}
            />

            {config?.APP_MODE !== "saas" && (
              <>
                <CustomInput
                  name="ghToken"
                  label={t(I18nKey.GITHUB$TOKEN_LABEL)}
                  type="password"
                  defaultValue={gitHubToken ?? ""}
                />
                <BaseModalDescription>
                  {t(I18nKey.GITHUB$GET_TOKEN)}{" "}
                  <a
                    href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-[#791B80] underline"
                  >
                    {t(I18nKey.COMMON$HERE)}
                  </a>
                </BaseModalDescription>
              </>
            )}
            {user.isError && (
              <p className="text-danger text-xs">
                {t(I18nKey.GITHUB$TOKEN_INVALID)}
              </p>
            )}
            {gitHubToken && !user.isError && (
              <ModalButton
                variant="text-like"
                text={t(I18nKey.BUTTON$DISCONNECT)}
                onClick={() => {
                  logout();
                  onClose();
                }}
                className="text-danger self-start"
              />
            )}
          </div>

          <label className="flex gap-2 items-center self-start">
            <input
              name="analytics"
              type="checkbox"
              defaultChecked={analyticsConsent === "true"}
            />
            {t(I18nKey.ANALYTICS$ENABLE)}
          </label>

          <div className="flex flex-col gap-2 w-full">
            <ModalButton
              testId="save-settings"
              type="submit"
              intent="account"
              text={t(I18nKey.BUTTON$SAVE)}
              className="bg-[#4465DB]"
            />
            <ModalButton
              text={t(I18nKey.BUTTON$CLOSE)}
              onClick={onClose}
              className="bg-[#737373]"
            />
          </div>
        </form>
      )}
    </ModalBody>
  );
}
