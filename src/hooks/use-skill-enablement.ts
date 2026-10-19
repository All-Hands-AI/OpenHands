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
  const { mutateAsync: saveSettings } = useSaveSettings();
  const isPublic = usePublicSkillTest();

  const [enablement, setEnablement] = React.useState<SkillEnablement>({});
  // The newest selection, read by toggles so a save never sees stale state.
  const enablementRef = React.useRef<SkillEnablement | null>(null);
  const hydratedForRef = React.useRef<string | null>(null);
  // Each save replaces both lists, so saves must reach the server in order.
  const saveQueueRef = React.useRef<Promise<unknown>>(Promise.resolve());

  // Hydrate once per backend: after that the newest selection is this one,
  // and a refetch landing between two saves would roll it back.
  React.useEffect(() => {
    if (settingsLoading || !settings || hydratedForRef.current === backend.id)
      return;
    hydratedForRef.current = backend.id;
    const hydrated = readGlobalEnablement(settings, isCloud);
    enablementRef.current = hydrated;
    setEnablement(hydrated);
  }, [settingsLoading, settings, isCloud, backend.id]);

  const isEnabled = React.useMemo(() => {
    const enabled = buildSkillEnablementFilter(enablement, isPublic);
    return (skill: SkillInfo) => enabled(skill.name);
  }, [enablement, isPublic]);

  const setEnabled = React.useCallback(
    (skillName: string, enabled: boolean) => {
      const previous = enablementRef.current;
      if (!previous) return;
      const next = toggleSkill(previous, skillName, enabled, isPublic);
      if (sameSkillSelection(previous, next)) return;
      enablementRef.current = next;
      setEnablement(next);

      const disabledSkills = next.disabledSkills ?? [];
      const update = isCloud
        ? { disabled_skills: disabledSkills }
        : {
            enabled_skills: resolveEnabledCatalogSkills(next),
            disabled_skills: disabledSkills,
          };
      saveQueueRef.current = saveQueueRef.current
        .then(() => saveSettings(update))
        .catch((error) => {
          displayErrorToast(
            retrieveAxiosErrorMessage(error) || t(I18nKey.ERROR$GENERIC),
          );
        });
    },
    [isPublic, isCloud, saveSettings, t],
  );

  return { isEnabled, setEnabled };
}
