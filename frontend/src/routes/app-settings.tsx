import React from "react";
import { useTranslation } from "react-i18next";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useSettings } from "#/hooks/query/use-settings";
import { AvailableLanguages } from "#/i18n";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { I18nKey } from "#/i18n/declaration";
import { LanguageInput } from "#/components/features/settings/app-settings/language-input";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { AppSettingsInputsSkeleton } from "#/components/features/settings/app-settings/app-settings-inputs-skeleton";
import { useConfig } from "#/hooks/query/use-config";
import { parseMaxBudgetPerTask } from "#/utils/settings-utils";

function AppSettingsScreen() {
  const { t } = useTranslation();

  const { mutate: saveSettings, isPending } = useSaveSettings();
  const { data: settings, isLoading } = useSettings();
  const { data: config } = useConfig();

  const [languageInputHasChanged, setLanguageInputHasChanged] =
    React.useState(false);
  const [analyticsSwitchHasChanged, setAnalyticsSwitchHasChanged] =
    React.useState(false);
  const [
    soundNotificationsSwitchHasChanged,
    setSoundNotificationsSwitchHasChanged,
  ] = React.useState(false);
  const [
    proactiveConversationsSwitchHasChanged,
    setProactiveConversationsSwitchHasChanged,
  ] = React.useState(false);
  const [maxBudgetPerTaskHasChanged, setMaxBudgetPerTaskHasChanged] =
    React.useState(false);

  const formAction = (formData: FormData) => {
    const languageLabel = formData.get("language-input")?.toString();
    const languageValue = AvailableLanguages.find(
      ({ label }) => label === languageLabel,
    )?.value;
    const language = languageValue || DEFAULT_SETTINGS.LANGUAGE;

    const enableAnalytics =
      formData.get("enable-analytics-switch")?.toString() === "on";
    const enableSoundNotifications =
      formData.get("enable-sound-notifications-switch")?.toString() === "on";

    const enableProactiveConversations =
      formData.get("enable-proactive-conversations-switch")?.toString() ===
      "on";

    const maxBudgetPerTaskValue = formData
      .get("max-budget-per-task-input")
      ?.toString();
    const maxBudgetPerTask = parseMaxBudgetPerTask(maxBudgetPerTaskValue || "");

    saveSettings(
      {
        LANGUAGE: language,
        user_consents_to_analytics: enableAnalytics,
        ENABLE_SOUND_NOTIFICATIONS: enableSoundNotifications,
        ENABLE_PROACTIVE_CONVERSATION_STARTERS: enableProactiveConversations,
        MAX_BUDGET_PER_TASK: maxBudgetPerTask,
      },
      {
        onSuccess: () => {
          handleCaptureConsent(enableAnalytics);
          displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
        },
        onError: (error) => {
          const errorMessage = retrieveAxiosErrorMessage(error);
          displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
        },
        onSettled: () => {
          setLanguageInputHasChanged(false);
          setAnalyticsSwitchHasChanged(false);
          setSoundNotificationsSwitchHasChanged(false);
          setProactiveConversationsSwitchHasChanged(false);
          setMaxBudgetPerTaskHasChanged(false);
        },
      },
    );
  };

  const checkIfLanguageInputHasChanged = (value: string) => {
    const selectedLanguage = AvailableLanguages.find(
      ({ label: langValue }) => langValue === value,
    )?.label;
    const currentLanguage = AvailableLanguages.find(
      ({ value: langValue }) => langValue === settings?.LANGUAGE,
    )?.label;

    setLanguageInputHasChanged(selectedLanguage !== currentLanguage);
  };

  const checkIfAnalyticsSwitchHasChanged = (checked: boolean) => {
    const currentAnalytics = !!settings?.USER_CONSENTS_TO_ANALYTICS;
    setAnalyticsSwitchHasChanged(checked !== currentAnalytics);
  };

  const checkIfSoundNotificationsSwitchHasChanged = (checked: boolean) => {
    const currentSoundNotifications = !!settings?.ENABLE_SOUND_NOTIFICATIONS;
    setSoundNotificationsSwitchHasChanged(
      checked !== currentSoundNotifications,
    );
  };

  const checkIfProactiveConversationsSwitchHasChanged = (checked: boolean) => {
    const currentProactiveConversations =
      !!settings?.ENABLE_PROACTIVE_CONVERSATION_STARTERS;
    setProactiveConversationsSwitchHasChanged(
      checked !== currentProactiveConversations,
    );
  };

  const checkIfMaxBudgetPerTaskHasChanged = (value: string) => {
    const newValue = parseMaxBudgetPerTask(value);
    const currentValue = settings?.MAX_BUDGET_PER_TASK;
    setMaxBudgetPerTaskHasChanged(newValue !== currentValue);
  };

  const formIsClean =
    !languageInputHasChanged &&
    !analyticsSwitchHasChanged &&
    !soundNotificationsSwitchHasChanged &&
    !proactiveConversationsSwitchHasChanged &&
    !maxBudgetPerTaskHasChanged;

  const shouldBeLoading = !settings || isLoading || isPending;

  return (
    <form
      data-testid="app-settings-screen"
      action={formAction}
      className="flex flex-col h-full justify-between"
    >
      {shouldBeLoading && <AppSettingsInputsSkeleton />}
      {!shouldBeLoading && (
        <div className="p-9 flex flex-col gap-6">
          <LanguageInput
            name="language-input"
            defaultKey={settings.LANGUAGE}
            onChange={checkIfLanguageInputHasChanged}
          />

          <SettingsSwitch
            testId="enable-analytics-switch"
            name="enable-analytics-switch"
            defaultIsToggled={!!settings.USER_CONSENTS_TO_ANALYTICS}
            onToggle={checkIfAnalyticsSwitchHasChanged}
          >
            {t(I18nKey.ANALYTICS$SEND_ANONYMOUS_DATA)}
          </SettingsSwitch>

          <SettingsSwitch
            testId="enable-sound-notifications-switch"
            name="enable-sound-notifications-switch"
            defaultIsToggled={!!settings.ENABLE_SOUND_NOTIFICATIONS}
            onToggle={checkIfSoundNotificationsSwitchHasChanged}
          >
            {t(I18nKey.SETTINGS$SOUND_NOTIFICATIONS)}
          </SettingsSwitch>

          {config?.APP_MODE === "saas" && (
            <SettingsSwitch
              testId="enable-proactive-conversations-switch"
              name="enable-proactive-conversations-switch"
              defaultIsToggled={
                !!settings.ENABLE_PROACTIVE_CONVERSATION_STARTERS
              }
              onToggle={checkIfProactiveConversationsSwitchHasChanged}
            >
              {t(I18nKey.SETTINGS$PROACTIVE_CONVERSATION_STARTERS)}
            </SettingsSwitch>
          )}

          <SettingsInput
            testId="max-budget-per-task-input"
            name="max-budget-per-task-input"
            type="number"
            label={t(I18nKey.SETTINGS$MAX_BUDGET_PER_CONVERSATION)}
            defaultValue={settings.MAX_BUDGET_PER_TASK?.toString() || ""}
            onChange={checkIfMaxBudgetPerTaskHasChanged}
            placeholder="Maximum budget per conversation in USD"
            min={1}
            step={1}
            className="w-[680px]" // Match the width of the language field
          />
        </div>
      )}

      <div className="flex gap-6 p-6 justify-end border-t border-t-tertiary">
        <BrandButton
          testId="submit-button"
          variant="primary"
          type="submit"
          isDisabled={isPending || formIsClean}
        >
          {!isPending && t("SETTINGS$SAVE_CHANGES")}
          {isPending && t("SETTINGS$SAVING")}
        </BrandButton>
      </div>
    </form>
  );
}

export default AppSettingsScreen;
