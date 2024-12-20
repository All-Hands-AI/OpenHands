import { useLocation } from "react-router";
import { useTranslation } from "react-i18next";
import React from "react";
import posthog from "posthog-js";
import { organizeModelsAndProviders } from "#/utils/organize-models-and-providers";
import { getDefaultSettings, Settings } from "#/services/settings";
import { extractModelAndProvider } from "#/utils/extract-model-and-provider";
import { DangerModal } from "../confirmation-modals/danger-modal";
import { I18nKey } from "#/i18n/declaration";
import {
  extractSettings,
  saveSettingsView,
  updateSettingsVersion,
} from "#/utils/settings-utils";
import { useEndSession } from "#/hooks/use-end-session";
import { useUserPrefs } from "#/context/user-prefs-context";
import { ModalButton } from "../../buttons/modal-button";
import { AdvancedOptionSwitch } from "../../inputs/advanced-option-switch";
import { AgentInput } from "../../inputs/agent-input";
import { APIKeyInput } from "../../inputs/api-key-input";
import { BaseUrlInput } from "../../inputs/base-url-input";
import { ConfirmationModeSwitch } from "../../inputs/confirmation-mode-switch";
import { CustomModelInput } from "../../inputs/custom-model-input";
import { SecurityAnalyzerInput } from "../../inputs/security-analyzers-input";
import { ModalBackdrop } from "../modal-backdrop";
import { ModelSelector } from "./model-selector";
import { useAuth } from "#/context/auth-context";

interface SettingsFormProps {
  disabled?: boolean;
  settings: Settings;
  models: string[];
  agents: string[];
  securityAnalyzers: string[];
  onClose: () => void;
}

export function SettingsForm({
  disabled,
  settings,
  models,
  agents,
  securityAnalyzers,
  onClose,
}: SettingsFormProps) {
  const { saveSettings } = useUserPrefs();
  const endSession = useEndSession();
  const { logout } = useAuth();

  const location = useLocation();
  const { t } = useTranslation();

  const formRef = React.useRef<HTMLFormElement>(null);

  const advancedAlreadyInUse = React.useMemo(() => {
    if (models.length > 0) {
      const organizedModels = organizeModelsAndProviders(models);
      const { provider, model } = extractModelAndProvider(
        settings.LLM_MODEL || "",
      );
      const isKnownModel =
        provider in organizedModels &&
        organizedModels[provider].models.includes(model);

      const isUsingSecurityAnalyzer = !!settings.SECURITY_ANALYZER;
      const isUsingConfirmationMode = !!settings.CONFIRMATION_MODE;
      const isUsingBaseUrl = !!settings.LLM_BASE_URL;
      const isUsingCustomModel = !!settings.LLM_MODEL && !isKnownModel;

      return (
        isUsingSecurityAnalyzer ||
        isUsingConfirmationMode ||
        isUsingBaseUrl ||
        isUsingCustomModel
      );
    }

    return false;
  }, [settings, models]);

  const [showAdvancedOptions, setShowAdvancedOptions] =
    React.useState(advancedAlreadyInUse);
  const [confirmResetDefaultsModalOpen, setConfirmResetDefaultsModalOpen] =
    React.useState(false);
  const [confirmEndSessionModalOpen, setConfirmEndSessionModalOpen] =
    React.useState(false);
  const [showWarningModal, setShowWarningModal] = React.useState(false);

  const resetOngoingSession = () => {
    if (location.pathname.startsWith("/conversations/")) {
      endSession();
      onClose();
    }
  };

  const handleFormSubmission = (formData: FormData) => {
    const keys = Array.from(formData.keys());
    const isUsingAdvancedOptions = keys.includes("use-advanced-options");
    const newSettings = extractSettings(formData);

    saveSettingsView(isUsingAdvancedOptions ? "advanced" : "basic");
    updateSettingsVersion(logout);
    saveSettings(newSettings);
    resetOngoingSession();

    posthog.capture("settings_saved", {
      LLM_MODEL: newSettings.LLM_MODEL,
      LLM_API_KEY: newSettings.LLM_API_KEY ? "SET" : "UNSET",
    });
  };

  const handleConfirmResetSettings = () => {
    saveSettings(getDefaultSettings());
    resetOngoingSession();
    posthog.capture("settings_reset");

    onClose();
  };

  const handleConfirmEndSession = () => {
    const formData = new FormData(formRef.current ?? undefined);
    handleFormSubmission(formData);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const apiKey = formData.get("api-key");

    if (!apiKey) {
      setShowWarningModal(true);
    } else if (location.pathname.startsWith("/conversations/")) {
      setConfirmEndSessionModalOpen(true);
    } else {
      handleFormSubmission(formData);
      onClose();
    }
  };

  const handleCloseClick = () => {
    const formData = new FormData(formRef.current ?? undefined);
    const apiKey = formData.get("api-key");

    if (!apiKey) setShowWarningModal(true);
    else onClose();
  };

  const handleWarningConfirm = () => {
    setShowWarningModal(false);
    const formData = new FormData(formRef.current ?? undefined);
    formData.set("api-key", ""); // Set null value for API key
    handleFormSubmission(formData);
    onClose();
  };

  const handleWarningCancel = () => {
    setShowWarningModal(false);
  };

  return (
    <div>
      <form
        ref={formRef}
        data-testid="settings-form"
        className="flex flex-col gap-6"
        onSubmit={handleSubmit}
      >
        <div className="flex flex-col gap-2">
          <AdvancedOptionSwitch
            isDisabled={!!disabled}
            showAdvancedOptions={showAdvancedOptions}
            setShowAdvancedOptions={setShowAdvancedOptions}
          />

          {showAdvancedOptions && (
            <>
              <CustomModelInput
                isDisabled={!!disabled}
                defaultValue={settings.LLM_MODEL}
              />

              <BaseUrlInput
                isDisabled={!!disabled}
                defaultValue={settings.LLM_BASE_URL}
              />
            </>
          )}

          {!showAdvancedOptions && (
            <ModelSelector
              isDisabled={disabled}
              models={organizeModelsAndProviders(models)}
              currentModel={settings.LLM_MODEL}
            />
          )}

          <APIKeyInput
            isDisabled={!!disabled}
            defaultValue={settings.LLM_API_KEY}
          />

          {showAdvancedOptions && (
            <AgentInput
              isDisabled={!!disabled}
              defaultValue={settings.AGENT}
              agents={agents}
            />
          )}

          {showAdvancedOptions && (
            <>
              <SecurityAnalyzerInput
                isDisabled={!!disabled}
                defaultValue={settings.SECURITY_ANALYZER}
                securityAnalyzers={securityAnalyzers}
              />

              <ConfirmationModeSwitch
                isDisabled={!!disabled}
                defaultSelected={settings.CONFIRMATION_MODE}
              />
            </>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <ModalButton
              disabled={disabled}
              type="submit"
              text={t(I18nKey.SETTINGS_FORM$SAVE_LABEL)}
              className="bg-[#4465DB] w-full"
            />
            <ModalButton
              text={t(I18nKey.SETTINGS_FORM$CLOSE_LABEL)}
              className="bg-[#737373] w-full"
              onClick={handleCloseClick}
            />
          </div>
          <ModalButton
            disabled={disabled}
            text={t(I18nKey.SETTINGS_FORM$RESET_TO_DEFAULTS_LABEL)}
            variant="text-like"
            className="text-danger self-start"
            onClick={() => {
              setConfirmResetDefaultsModalOpen(true);
            }}
          />
        </div>
      </form>

      {confirmResetDefaultsModalOpen && (
        <ModalBackdrop>
          <DangerModal
            title={t(I18nKey.SETTINGS_FORM$ARE_YOU_SURE_LABEL)}
            description={t(
              I18nKey.SETTINGS_FORM$ALL_INFORMATION_WILL_BE_DELETED_MESSAGE,
            )}
            buttons={{
              danger: {
                text: t(I18nKey.SETTINGS_FORM$RESET_TO_DEFAULTS_LABEL),
                onClick: handleConfirmResetSettings,
              },
              cancel: {
                text: t(I18nKey.SETTINGS_FORM$CANCEL_LABEL),
                onClick: () => setConfirmResetDefaultsModalOpen(false),
              },
            }}
          />
        </ModalBackdrop>
      )}
      {confirmEndSessionModalOpen && (
        <ModalBackdrop>
          <DangerModal
            title={t(I18nKey.SETTINGS_FORM$END_SESSION_LABEL)}
            description={t(
              I18nKey.SETTINGS_FORM$CHANGING_WORKSPACE_WARNING_MESSAGE,
            )}
            buttons={{
              danger: {
                text: t(I18nKey.SETTINGS_FORM$END_SESSION_LABEL),
                onClick: handleConfirmEndSession,
              },
              cancel: {
                text: t(I18nKey.SETTINGS_FORM$CANCEL_LABEL),
                onClick: () => setConfirmEndSessionModalOpen(false),
              },
            }}
          />
        </ModalBackdrop>
      )}
      {showWarningModal && (
        <ModalBackdrop>
          <DangerModal
            title="Are you sure?"
            description="You haven't set an API key. Without an API key, you won't be able to use the AI features. Are you sure you want to close the settings?"
            buttons={{
              danger: {
                text: "Yes, close settings",
                onClick: handleWarningConfirm,
              },
              cancel: {
                text: "Cancel",
                onClick: handleWarningCancel,
              },
            }}
          />
        </ModalBackdrop>
      )}
    </div>
  );
}
