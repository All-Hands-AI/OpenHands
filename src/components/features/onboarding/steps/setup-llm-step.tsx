import React from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { BrandButton } from "#/components/features/settings/brand-button";
import { I18nKey } from "#/i18n/declaration";
import { LlmSettingsScreen } from "#/routes/llm-settings";
import type { SdkSectionSaveControl } from "#/components/features/settings/sdk-settings/sdk-section-page";
import { useActiveBackend } from "#/contexts/active-backend-context";
import { useSaveLlmProfile } from "#/hooks/mutation/use-save-llm-profile";
import { useActivateLlmProfile } from "#/hooks/mutation/use-activate-llm-profile";
import { useApplyOnboardingAgentProfile } from "#/hooks/mutation/use-apply-onboarding-agent-profile";
import { useLlmProfiles } from "#/hooks/query/use-llm-profiles";
import { useSettings } from "#/hooks/query/use-settings";
import { useAgentSettingsSchema } from "#/hooks/query/use-agent-settings-schema";
import {
  CONFIG_CACHE_OPTIONS,
  LLM_PROFILES_QUERY_KEYS,
} from "#/hooks/query/query-keys";
import {
  useDefaultModel,
  useDefaultModelReady,
} from "#/hooks/query/use-free-models";
import { LlmSettingsInputsSkeleton } from "#/components/features/settings/llm-settings/llm-settings-inputs-skeleton";
import { deriveProfileNameFromModel } from "#/utils/derive-profile-name";
import ProfilesService, {
  type SaveProfileRequest,
} from "#/api/profiles-service/profiles-service.api";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import {
  profileToFormValues,
  freshProfileFormValues,
  buildProfileLlmConfig,
} from "#/components/features/settings/llm-profiles";

interface SetupLlmStepProps {
  onBack: () => void;
  onNext: () => void;
}

/**
 * Fallback when the backend has not exposed a DB-selected OpenHands default.
 * The onboarding override still marks the model dirty so Next persists the
 * suggested model immediately.
 */
export const ONBOARDING_DEFAULT_LLM_MODEL = "openai/gpt-5.6-sol";

/**
 * Step 2: embed the LLM settings form.
 *
 * On a local backend, onboarding's LLM step is profile-first:
 * - It fills the form from the active profile (with encrypted secrets) or fresh schema defaults.
 * - Clicking Next directly creates, saves, activates, and points the default agent profile at it,
 *   without calling PATCH /api/settings or reading agent_settings.llm.
 *
 * On cloud, it retains the existing raw settings save path.
 */
export function SetupLlmStep({ onBack, onNext }: SetupLlmStepProps) {
  const { t } = useTranslation("openhands");
  const { backend, orgId } = useActiveBackend();
  const isLocalBackend = backend.kind === "local";
  const saveProfile = useSaveLlmProfile();
  const activateProfile = useActivateLlmProfile();
  const applyAgentProfile = useApplyOnboardingAgentProfile();
  const dbDefaultLlmModel = useDefaultModel();
  const isDefaultModelReady = useDefaultModelReady();
  const defaultLlmModel = dbDefaultLlmModel ?? ONBOARDING_DEFAULT_LLM_MODEL;

  const [saveControl, setSaveControl] =
    React.useState<SdkSectionSaveControl | null>(null);
  const [isFinalizing, setIsFinalizing] = React.useState(false);
  const [hasFinalizationError, setHasFinalizationError] = React.useState(false);

  // Queries for profile-first initialization on local backend
  const { data: profilesData, isLoading: isProfilesLoading } = useLlmProfiles({
    enabled: isLocalBackend,
  });
  const { data: settings } = useSettings();
  const { data: schema } = useAgentSettingsSchema(
    settings?.agent_settings_schema,
  );

  const activeProfile = isLocalBackend
    ? profilesData?.profiles.find((p) => p.name === profilesData.active_profile)
    : undefined;

  const { data: activeProfileDetail, isLoading: isActiveProfileDetailLoading } =
    useQuery({
      queryKey: [
        ...LLM_PROFILES_QUERY_KEYS.all,
        backend.id,
        orgId,
        "encrypted-detail",
        activeProfile?.name,
      ],
      queryFn: () =>
        ProfilesService.getProfile(activeProfile!.name, "encrypted"),
      enabled: isLocalBackend && !!activeProfile?.name,
      ...CONFIG_CACHE_OPTIONS,
      meta: { disableToast: true },
    });

  const baseConfig = React.useMemo(() => {
    if (!isLocalBackend) return {};
    return (activeProfileDetail?.config ?? {}) as Record<string, unknown>;
  }, [isLocalBackend, activeProfileDetail]);

  const initialValueOverrides = React.useMemo(() => {
    if (!isLocalBackend) {
      return {
        "llm.model": defaultLlmModel,
      };
    }
    if (activeProfile) {
      return profileToFormValues(baseConfig, schema);
    }
    return freshProfileFormValues(defaultLlmModel, schema);
  }, [isLocalBackend, activeProfile, baseConfig, schema, defaultLlmModel]);

  const isFormReady =
    isDefaultModelReady &&
    (!isLocalBackend ||
      (!isProfilesLoading &&
        (!activeProfile || !isActiveProfileDetailLoading)));

  const saveAndActivateProfile = React.useCallback(async () => {
    if (!saveControl) return;

    setIsFinalizing(true);
    setHasFinalizationError(false);

    try {
      const dirtyPayload = saveControl.getDirtyPayload();
      let dirtyLlm: Record<string, unknown> = {};
      try {
        dirtyLlm = (dirtyPayload.llm ?? {}) as Record<string, unknown>;
      } catch (error) {
        displayErrorToast(
          error instanceof Error ? error.message : t(I18nKey.ERROR$GENERIC),
        );
        setIsFinalizing(false);
        return;
      }

      // If user did not change model explicitly, fallback to form's current model value
      if (!dirtyLlm.model && saveControl.values["llm.model"]) {
        dirtyLlm = {
          ...dirtyLlm,
          model: saveControl.values["llm.model"],
        };
      }

      const llmConfig = buildProfileLlmConfig({
        baseConfig,
        dirtyLlm,
        formValues: saveControl.values,
        view: saveControl.view,
        supportsConnections: isLocalBackend,
        isCloud: false,
      });

      const model = typeof llmConfig.model === "string" ? llmConfig.model : "";
      if (!model) {
        displayErrorToast(t(I18nKey.SETTINGS$MODEL_REQUIRED));
        setIsFinalizing(false);
        return;
      }

      const profileName = deriveProfileNameFromModel(model);

      await saveProfile.mutateAsync({
        name: profileName,
        request: {
          llm: llmConfig as SaveProfileRequest["llm"],
          include_secrets: true,
        },
      });

      await activateProfile.mutateAsync(profileName);

      await applyAgentProfile({
        agent_kind: "openhands",
        llm_profile_ref: profileName,
      });

      onNext();
    } catch {
      setHasFinalizationError(true);
      displayErrorToast(t(I18nKey.ERROR$GENERIC));
    } finally {
      setIsFinalizing(false);
    }
  }, [
    saveControl,
    baseConfig,
    isLocalBackend,
    saveProfile,
    activateProfile,
    applyAgentProfile,
    onNext,
    t,
  ]);

  const handleSaveSuccess = React.useCallback(async () => {
    setIsFinalizing(true);
    setHasFinalizationError(false);
    try {
      onNext();
    } catch {
      setHasFinalizationError(true);
      displayErrorToast(t(I18nKey.ERROR$GENERIC));
    } finally {
      setIsFinalizing(false);
    }
  }, [onNext, t]);

  const handleNext = () => {
    if (isLocalBackend) {
      if (!saveControl) {
        onNext();
        return;
      }
      if (activeProfile && !saveControl.isDirty && !hasFinalizationError) {
        setIsFinalizing(true);
        void (async () => {
          try {
            await applyAgentProfile({
              agent_kind: "openhands",
              llm_profile_ref: activeProfile.name,
            });
            onNext();
          } catch {
            setHasFinalizationError(true);
            displayErrorToast(t(I18nKey.ERROR$GENERIC));
          } finally {
            setIsFinalizing(false);
          }
        })();
        return;
      }
      void saveAndActivateProfile();
      return;
    }

    if (saveControl?.isDirty) {
      setHasFinalizationError(false);
      saveControl.save();
      return;
    }
    if (hasFinalizationError) {
      void handleSaveSuccess();
      return;
    }
    onNext();
  };

  return (
    <div
      data-testid="onboarding-step-setup-llm"
      className="flex flex-col gap-6 max-h-[calc(90vh-7rem)]"
    >
      <header className="flex flex-col gap-2">
        <h2 className="text-2xl font-medium text-contrast">
          {t(I18nKey.ONBOARDING$LLM_TITLE)}
        </h2>
        <p className="text-sm text-muted">
          {t(I18nKey.ONBOARDING$LLM_SUBTITLE)}
        </p>
      </header>

      <div
        data-testid="onboarding-llm-settings"
        className="flex min-h-0 flex-1 flex-col overflow-y-auto custom-scrollbar-always"
      >
        {isFormReady ? (
          <LlmSettingsScreen
            key={
              isLocalBackend
                ? activeProfile
                  ? `active-${activeProfile.name}`
                  : "fresh-profile"
                : "cloud"
            }
            embedded
            hideSaveButton
            suppressSuccessToast
            markInitialOverridesDirty={!isLocalBackend || !activeProfile}
            initialValueOverrides={initialValueOverrides}
            showProviderConnection={isLocalBackend}
            onSaveSuccess={handleSaveSuccess}
            onSaveControlChange={setSaveControl}
          />
        ) : (
          <LlmSettingsInputsSkeleton />
        )}
      </div>

      <div className="sticky bottom-0 flex items-center justify-between gap-2 bg-base-secondary pt-4 pb-7">
        <BrandButton
          testId="onboarding-llm-back"
          type="button"
          variant="secondary"
          onClick={onBack}
        >
          {t(I18nKey.ONBOARDING$BACK)}
        </BrandButton>
        <BrandButton
          testId="onboarding-llm-next"
          type="button"
          variant="primary"
          isDisabled={
            !isFormReady || isFinalizing || Boolean(saveControl?.isSaving)
          }
          aria-busy={isFinalizing || Boolean(saveControl?.isSaving)}
          onClick={handleNext}
        >
          {t(I18nKey.ONBOARDING$NEXT)}
        </BrandButton>
      </div>
    </div>
  );
}
