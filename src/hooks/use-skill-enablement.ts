import React from "react";
import { useTranslation } from "react-i18next";
import { useActiveBackend } from "#/contexts/active-backend-context";
import { useActiveProfileBehavior } from "#/hooks/use-active-profile-behavior";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useSettings } from "#/hooks/query/use-settings";
import { useSkillCatalog } from "#/hooks/query/use-skill-catalog";
import { I18nKey } from "#/i18n/declaration";
import type { Settings, SkillInfo } from "#/types/settings";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import {
  buildSkillEnablementFilter,
  CATALOG_SKILL_NAMES,
  defaultSkillEnablement,
  profileSkillEnablement,
  publicSkillTest,
  resolveEnabledCatalogSkills,
  sameSkillSelection,
  toggleSkill,
  type SkillEnablement,
} from "#/utils/skill-enablement";

/**
 * Which skills the allow-list governs: the server's catalog skills locally.
 * Cloud keeps every skill deny-list governed.
 */
export function usePublicSkillTest(): (name: string) => boolean {
  const { backend } = useActiveBackend();
  const { data: catalog } = useSkillCatalog();
  return React.useMemo(
    () => (backend.kind === "cloud" ? () => false : publicSkillTest(catalog)),
    [backend.kind, catalog],
  );
}

/** Read-only view of a profile's selection, the active one unless `agentProfileId` names another. */
export function useSkillEnabledFilter(
  agentProfileId?: string | null,
): (skill: SkillInfo) => boolean {
  const { data: settings } = useSettings();
  const active = useActiveProfileBehavior(agentProfileId);
  const { data: catalog } = useSkillCatalog();
  const isPublic = usePublicSkillTest();
  const cloudDisabled = settings?.disabled_skills;
  const { profile } = active;

  const enablement = React.useMemo<SkillEnablement>(() => {
    if (!active.isLocal) return { disabledSkills: cloudDisabled ?? [] };
    if (!profile) return {};
    const publicNames = catalog
      ?.filter((skill) => skill.origin === "public")
      .map((skill) => skill.name);
    return profileSkillEnablement(profile, publicNames ?? CATALOG_SKILL_NAMES);
  }, [active.isLocal, cloudDisabled, profile, catalog]);

  return React.useMemo(() => {
    const isEnabled = buildSkillEnablementFilter(enablement, isPublic);
    return (skill: SkillInfo) => isEnabled(skill.name);
  }, [enablement, isPublic]);
}

export interface SkillEnablementController {
  isEnabled: (skill: SkillInfo) => boolean;
  setEnabled: (skillName: string, enabled: boolean) => void;
}

function readGlobalEnablement(
  settings: Settings,
  isCloud: boolean,
): SkillEnablement {
  return isCloud
    ? { disabledSkills: settings.disabled_skills ?? [] }
    : defaultSkillEnablement(settings);
}

/**
 * The default skill selection: the one new agent profiles start from
 * locally, and the account's deny-list on Cloud.
 */
export function useSkillEnablement(): SkillEnablementController {
  const { t } = useTranslation("openhands");
  const { backend } = useActiveBackend();
  const isCloud = backend.kind === "cloud";
  const { data: settings, isLoading: settingsLoading } = useSettings();
  const { mutate: saveSettings } = useSaveSettings();
  const isPublic = usePublicSkillTest();

  const [enablement, setEnablement] = React.useState<SkillEnablement>({});
  const savedRef = React.useRef<SkillEnablement | null>(null);

  React.useEffect(() => {
    if (settingsLoading || !settings) return;
    const hydrated = readGlobalEnablement(settings, isCloud);
    savedRef.current = hydrated;
    setEnablement(hydrated);
  }, [
    settingsLoading,
    settings?.enabled_skills,
    settings?.disabled_skills,
    isCloud,
  ]);

  React.useEffect(() => {
    // Writing the hydrated value straight back would persist a migration the
    // user never confirmed.
    const saved = savedRef.current;
    if (saved === null || sameSkillSelection(saved, enablement)) return;
    savedRef.current = enablement;

    const disabledSkills = enablement.disabledSkills ?? [];
    saveSettings(
      isCloud
        ? { disabled_skills: disabledSkills }
        : {
            enabled_skills: resolveEnabledCatalogSkills(enablement),
            disabled_skills: disabledSkills,
          },
      {
        onError: (error) => {
          displayErrorToast(
            retrieveAxiosErrorMessage(error) || t(I18nKey.ERROR$GENERIC),
          );
        },
      },
    );
  }, [enablement, isCloud, saveSettings, t]);

  const isEnabled = React.useMemo(() => {
    const enabled = buildSkillEnablementFilter(enablement, isPublic);
    return (skill: SkillInfo) => enabled(skill.name);
  }, [enablement, isPublic]);

  const setEnabled = React.useCallback(
    (skillName: string, enabled: boolean) => {
      setEnablement((previous) =>
        toggleSkill(previous, skillName, enabled, isPublic),
      );
    },
    [isPublic],
  );

  return { isEnabled, setEnabled };
}
