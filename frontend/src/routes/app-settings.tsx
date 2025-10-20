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
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";
import QuestionCircleIcon from "#/icons/question-circle.svg?react";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { SettingsDropdownInput } from "#/components/features/settings/settings-dropdown-input";

function AppSettingsScreen() {
  const { t } = useTranslation();

  const { mutate: saveSettings, isPending } = useSaveSettings();
  const { data: settings, isLoading } = useSettings();
  const { data: config } = useConfig();
  const { data: resources } = useAIConfigOptions();

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
  const [
    solvabilityAnalysisSwitchHasChanged,
    setSolvabilityAnalysisSwitchHasChanged,
  ] = React.useState(false);
  const [maxBudgetPerTaskHasChanged, setMaxBudgetPerTaskHasChanged] =
    React.useState(false);
  const [gitUserNameHasChanged, setGitUserNameHasChanged] =
    React.useState(false);
  const [gitUserEmailHasChanged, setGitUserEmailHasChanged] =
    React.useState(false);
  const [
    confirmationModeSwitchHasChanged,
    setConfirmationModeSwitchHasChanged,
  ] = React.useState(false);
  const [securityAnalyzerHasChanged, setSecurityAnalyzerHasChanged] =
    React.useState(false);

  // Track confirmation mode state to control security analyzer visibility
  const [confirmationModeEnabled, setConfirmationModeEnabled] = React.useState(
    settings?.CONFIRMATION_MODE ?? DEFAULT_SETTINGS.CONFIRMATION_MODE,
  );

  // Track selected security analyzer for form submission
  const [selectedSecurityAnalyzer, setSelectedSecurityAnalyzer] =
    React.useState(
      settings?.SECURITY_ANALYZER === null
        ? "none"
        : (settings?.SECURITY_ANALYZER ?? DEFAULT_SETTINGS.SECURITY_ANALYZER),
    );

  // Update confirmation mode state when settings change
  React.useEffect(() => {
    if (settings?.CONFIRMATION_MODE !== undefined) {
      setConfirmationModeEnabled(settings.CONFIRMATION_MODE);
    }
  }, [settings?.CONFIRMATION_MODE]);

  // Update selected security analyzer state when settings change
  React.useEffect(() => {
    if (settings?.SECURITY_ANALYZER !== undefined) {
      setSelectedSecurityAnalyzer(settings.SECURITY_ANALYZER || "none");
    }
  }, [settings?.SECURITY_ANALYZER]);

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

    const enableSolvabilityAnalysis =
      formData.get("enable-solvability-analysis-switch")?.toString() === "on";

    const maxBudgetPerTaskValue = formData
      .get("max-budget-per-task-input")
      ?.toString();
    const maxBudgetPerTask = parseMaxBudgetPerTask(maxBudgetPerTaskValue || "");

    const gitUserName =
      formData.get("git-user-name-input")?.toString() ||
      DEFAULT_SETTINGS.GIT_USER_NAME;
    const gitUserEmail =
      formData.get("git-user-email-input")?.toString() ||
      DEFAULT_SETTINGS.GIT_USER_EMAIL;

    const confirmationMode =
      formData.get("enable-confirmation-mode-switch")?.toString() === "on";
    const securityAnalyzer = formData
      .get("security-analyzer-input")
      ?.toString();

    saveSettings(
      {
        LANGUAGE: language,
        user_consents_to_analytics: enableAnalytics,
        ENABLE_SOUND_NOTIFICATIONS: enableSoundNotifications,
        ENABLE_PROACTIVE_CONVERSATION_STARTERS: enableProactiveConversations,
        ENABLE_SOLVABILITY_ANALYSIS: enableSolvabilityAnalysis,
        MAX_BUDGET_PER_TASK: maxBudgetPerTask,
        GIT_USER_NAME: gitUserName,
        GIT_USER_EMAIL: gitUserEmail,
        CONFIRMATION_MODE: confirmationMode,
        SECURITY_ANALYZER:
          securityAnalyzer === "none"
            ? null
            : securityAnalyzer || DEFAULT_SETTINGS.SECURITY_ANALYZER,
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
          setSolvabilityAnalysisSwitchHasChanged(false);
          setMaxBudgetPerTaskHasChanged(false);
          setGitUserNameHasChanged(false);
          setGitUserEmailHasChanged(false);
          setConfirmationModeSwitchHasChanged(false);
          setSecurityAnalyzerHasChanged(false);
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

  const checkIfSolvabilityAnalysisSwitchHasChanged = (checked: boolean) => {
    const currentSolvabilityAnalysis = !!settings?.ENABLE_SOLVABILITY_ANALYSIS;
    setSolvabilityAnalysisSwitchHasChanged(
      checked !== currentSolvabilityAnalysis,
    );
  };

  const checkIfMaxBudgetPerTaskHasChanged = (value: string) => {
    const newValue = parseMaxBudgetPerTask(value);
    const currentValue = settings?.MAX_BUDGET_PER_TASK;
    setMaxBudgetPerTaskHasChanged(newValue !== currentValue);
  };

  const checkIfGitUserNameHasChanged = (value: string) => {
    const currentValue = settings?.GIT_USER_NAME;
    setGitUserNameHasChanged(value !== currentValue);
  };

  const checkIfGitUserEmailHasChanged = (value: string) => {
    const currentValue = settings?.GIT_USER_EMAIL;
    setGitUserEmailHasChanged(value !== currentValue);
  };

  const checkIfConfirmationModeSwitchHasChanged = (checked: boolean) => {
    const currentConfirmationMode = !!settings?.CONFIRMATION_MODE;
    setConfirmationModeSwitchHasChanged(checked !== currentConfirmationMode);
    setConfirmationModeEnabled(checked);

    // When confirmation mode is enabled, set default security analyzer to "llm" if not already set
    if (checked && !selectedSecurityAnalyzer) {
      setSelectedSecurityAnalyzer(DEFAULT_SETTINGS.SECURITY_ANALYZER);
      setSecurityAnalyzerHasChanged(true);
    }
  };

  const checkIfSecurityAnalyzerHasChanged = (value: string) => {
    const currentValue = settings?.SECURITY_ANALYZER || "none";
    setSecurityAnalyzerHasChanged(value !== currentValue);
  };

  const getSecurityAnalyzerOptions = () => {
    const analyzers = resources?.securityAnalyzers || [];
    const orderedItems = [];

    // Add LLM analyzer first
    if (analyzers.includes("llm")) {
      orderedItems.push({
        key: "llm",
        label: t(I18nKey.SETTINGS$SECURITY_ANALYZER_LLM_DEFAULT),
      });
    }

    // Add None option second
    orderedItems.push({
      key: "none",
      label: t(I18nKey.SETTINGS$SECURITY_ANALYZER_NONE),
    });

    // Add Invariant analyzer third
    if (analyzers.includes("invariant")) {
      orderedItems.push({
        key: "invariant",
        label: t(I18nKey.SETTINGS$SECURITY_ANALYZER_INVARIANT),
      });
    }

    // Add any other analyzers that might exist
    analyzers.forEach((analyzer) => {
      if (!["llm", "invariant", "none"].includes(analyzer)) {
        // For unknown analyzers, use the analyzer name as fallback
        // In the future, add specific i18n keys for new analyzers
        orderedItems.push({
          key: analyzer,
          label: analyzer, // TODO: Add i18n support for new analyzers
        });
      }
    });

    return orderedItems;
  };

  const formIsClean =
    !languageInputHasChanged &&
    !analyticsSwitchHasChanged &&
    !soundNotificationsSwitchHasChanged &&
    !proactiveConversationsSwitchHasChanged &&
    !solvabilityAnalysisSwitchHasChanged &&
    !maxBudgetPerTaskHasChanged &&
    !gitUserNameHasChanged &&
    !gitUserEmailHasChanged &&
    !confirmationModeSwitchHasChanged &&
    !securityAnalyzerHasChanged;

  const shouldBeLoading = !settings || isLoading || isPending;

  return (
    <form
      data-testid="app-settings-screen"
      action={formAction}
      className="flex flex-col h-full justify-between"
    >
      {shouldBeLoading && <AppSettingsInputsSkeleton />}
      {!shouldBeLoading && (
        <div className="flex flex-col gap-6">
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

          {/* Confirmation mode and security analyzer */}
          <div className="flex items-center gap-2">
            <SettingsSwitch
              testId="enable-confirmation-mode-switch"
              name="enable-confirmation-mode-switch"
              onToggle={checkIfConfirmationModeSwitchHasChanged}
              defaultIsToggled={settings.CONFIRMATION_MODE}
              isBeta
            >
              {t(I18nKey.SETTINGS$CONFIRMATION_MODE)}
            </SettingsSwitch>
            <TooltipButton
              tooltip={t(I18nKey.SETTINGS$CONFIRMATION_MODE_TOOLTIP)}
              ariaLabel={t(I18nKey.SETTINGS$CONFIRMATION_MODE)}
              className="text-[#9099AC] hover:text-white cursor-help"
            >
              <QuestionCircleIcon width={16} height={16} />
            </TooltipButton>
          </div>

          {confirmationModeEnabled && (
            <>
              <div className="w-full max-w-[680px]">
                <SettingsDropdownInput
                  testId="security-analyzer-input"
                  name="security-analyzer-display"
                  label={t(I18nKey.SETTINGS$SECURITY_ANALYZER)}
                  items={getSecurityAnalyzerOptions()}
                  placeholder={t(
                    I18nKey.SETTINGS$SECURITY_ANALYZER_PLACEHOLDER,
                  )}
                  selectedKey={selectedSecurityAnalyzer || "none"}
                  isClearable={false}
                  onSelectionChange={(key) => {
                    const newValue = key?.toString() || "";
                    setSelectedSecurityAnalyzer(newValue);
                    checkIfSecurityAnalyzerHasChanged(newValue);
                  }}
                  onInputChange={(value) => {
                    // Handle when input is cleared
                    if (!value) {
                      setSelectedSecurityAnalyzer("");
                      checkIfSecurityAnalyzerHasChanged("");
                    }
                  }}
                  wrapperClassName="w-full"
                />
                {/* Hidden input to store the actual key value for form submission */}
                <input
                  type="hidden"
                  name="security-analyzer-input"
                  value={selectedSecurityAnalyzer || ""}
                />
              </div>
              <p className="text-xs text-tertiary-alt max-w-[680px]">
                {t(I18nKey.SETTINGS$SECURITY_ANALYZER_DESCRIPTION)}
              </p>
            </>
          )}

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

          {config?.APP_MODE === "saas" && (
            <SettingsSwitch
              testId="enable-solvability-analysis-switch"
              name="enable-solvability-analysis-switch"
              defaultIsToggled={!!settings.ENABLE_SOLVABILITY_ANALYSIS}
              onToggle={checkIfSolvabilityAnalysisSwitchHasChanged}
            >
              {t(I18nKey.SETTINGS$SOLVABILITY_ANALYSIS)}
            </SettingsSwitch>
          )}

          <SettingsInput
            testId="max-budget-per-task-input"
            name="max-budget-per-task-input"
            type="number"
            label={t(I18nKey.SETTINGS$MAX_BUDGET_PER_CONVERSATION)}
            defaultValue={settings.MAX_BUDGET_PER_TASK?.toString() || ""}
            onChange={checkIfMaxBudgetPerTaskHasChanged}
            placeholder={t(I18nKey.SETTINGS$MAXIMUM_BUDGET_USD)}
            min={1}
            step={1}
            className="w-full max-w-[680px]" // Match the width of the language field
          />

          <div className="border-t border-t-tertiary pt-6 mt-2">
            <h3 className="text-lg font-medium mb-2">
              {t(I18nKey.SETTINGS$GIT_SETTINGS)}
            </h3>
            <p className="text-xs mb-4">
              {t(I18nKey.SETTINGS$GIT_SETTINGS_DESCRIPTION)}
            </p>
            <div className="flex flex-col gap-6">
              <SettingsInput
                testId="git-user-name-input"
                name="git-user-name-input"
                type="text"
                label={t(I18nKey.SETTINGS$GIT_USERNAME)}
                defaultValue={settings.GIT_USER_NAME || ""}
                onChange={checkIfGitUserNameHasChanged}
                placeholder="Username for git commits"
                className="w-full max-w-[680px]"
              />
              <SettingsInput
                testId="git-user-email-input"
                name="git-user-email-input"
                type="email"
                label={t(I18nKey.SETTINGS$GIT_EMAIL)}
                defaultValue={settings.GIT_USER_EMAIL || ""}
                onChange={checkIfGitUserEmailHasChanged}
                placeholder="Email for git commits"
                className="w-full max-w-[680px]"
              />
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-6 p-6 justify-end">
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
