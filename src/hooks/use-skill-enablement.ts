import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import AgentProfilesService from "#/api/agent-profiles-service/agent-profiles-service.api";
import type { StoredOpenHandsProfile } from "#/api/agent-profiles-service/profile-behavior";
import { useActiveBackend } from "#/contexts/active-backend-context";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useAgentProfiles } from "#/hooks/query/use-agent-profiles";
import {
  AGENT_PROFILES_QUERY_KEYS,
  AGENT_PROFILES_RETRY_OPTIONS,
  CONFIG_CACHE_OPTIONS,
} from "#/hooks/query/query-keys";
import { useSettings } from "#/hooks/query/use-settings";
import { I18nKey } from "#/i18n/declaration";
import type { Settings, SkillInfo } from "#/types/settings";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import {
  buildSkillEnablementFilter,
  CATALOG_SKILL_NAMES,
  isCatalogSkill,
  profileSkillEnablement,
  resolveEnabledCatalogSkills,
  type SkillEnablement,
} from "#/utils/skill-enablement";

/**
 * Settings → the two lists. Cloud creates conversations from its own
 * server-side catalog and never reads `enabled_skills`, so the catalog stays
 * deny-list governed there.
 */
function readSkillEnablement(
  settings: Settings | undefined,
  usesCatalogAllowList: boolean,
): SkillEnablement {
  return {
    enabledSkills: usesCatalogAllowList
      ? settings?.enabled_skills
      : [...CATALOG_SKILL_NAMES],
    disabledSkills: settings?.disabled_skills ?? [],
  };
}

/** The stored OpenHands profile with this id, read only on a local backend. */
function useLocalOpenHandsProfile(
  agentProfileId: string | null | undefined,
): StoredOpenHandsProfile | null {
  const { backend, orgId } = useActiveBackend();
  const isLocal = backend.kind !== "cloud" && !!agentProfileId;
  const { data: list } = useAgentProfiles({ enabled: isLocal });
  const name = isLocal
    ? (list?.profiles?.find((profile) => profile.id === agentProfileId)?.name ??
      null)
    : null;
  const { data: detail } = useQuery({
    queryKey: AGENT_PROFILES_QUERY_KEYS.detail(backend.id, orgId, name ?? ""),
    queryFn: () => AgentProfilesService.getProfile(name!),
    enabled: name !== null,
    ...CONFIG_CACHE_OPTIONS,
    ...AGENT_PROFILES_RETRY_OPTIONS,
    meta: { disableToast: true },
  });
  return detail?.profile.agent_kind === "openhands"
    ? (detail.profile as StoredOpenHandsProfile)
    : null;
}

/**
 * Read-only view of the rule, for surfaces that list skills without toggling.
 * Locally a conversation loads its agent profile's selection, so pass the
 * profile it launched with.
 */
export function useSkillEnabledFilter(
  agentProfileId?: string | null,
): (skill: SkillInfo) => boolean {
  const { backend } = useActiveBackend();
  const { data: settings } = useSettings();
  const usesCatalogAllowList = backend.kind !== "cloud";
  const profile = useLocalOpenHandsProfile(agentProfileId);

  return React.useMemo(() => {
    const isEnabled = buildSkillEnablementFilter(
      profile
        ? profileSkillEnablement(profile)
        : readSkillEnablement(settings, usesCatalogAllowList),
    );
    return (skill: SkillInfo) => isEnabled(skill.name);
  }, [
    profile,
    settings?.enabled_skills,
    settings?.disabled_skills,
    usesCatalogAllowList,
  ]);
}

export interface SkillEnablementController {
  isEnabled: (skill: SkillInfo) => boolean;
  setEnabled: (skillName: string, enabled: boolean) => void;
}

/** Stable form of both lists, so an unchanged set can skip the save. */
function snapshot(enablement: SkillEnablement): string {
  return JSON.stringify([
    [...resolveEnabledCatalogSkills(enablement)].sort(),
    [...(enablement.disabledSkills ?? [])].sort(),
  ]);
}

/** Same array reference when the membership already matches, to skip a save. */
function withMembership(
  list: string[],
  name: string,
  present: boolean,
): string[] {
  if (list.includes(name) === present) return list;
  return present ? [...list, name] : list.filter((entry) => entry !== name);
}

/**
 * Shared toggle state for every surface that switches skills on and off.
 *
 * Which of the two lists a skill belongs to is decided here alone, so one
 * surface cannot write a preference another cannot see.
 */
export function useSkillEnablement(): SkillEnablementController {
  const { t } = useTranslation("openhands");
  const { backend } = useActiveBackend();
  const usesCatalogAllowList = backend.kind !== "cloud";
  const { data: settings, isLoading: settingsLoading } = useSettings();
  const { mutate: saveSettings } = useSaveSettings();

  const [enablement, setEnablement] = React.useState<SkillEnablement>({});
  const savedRef = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (settingsLoading || !settings) return;
    const hydrated = readSkillEnablement(settings, usesCatalogAllowList);
    savedRef.current = snapshot(hydrated);
    setEnablement(hydrated);
  }, [
    settingsLoading,
    settings?.enabled_skills,
    settings?.disabled_skills,
    usesCatalogAllowList,
  ]);

  React.useEffect(() => {
    // Writing the hydrated value straight back would race the one-shot
    // migration and could narrow a workspace it had just preserved.
    const next = snapshot(enablement);
    if (savedRef.current === null || savedRef.current === next) return;
    savedRef.current = next;

    const disabledSkills = enablement.disabledSkills ?? [];
    saveSettings(
      usesCatalogAllowList
        ? {
            enabled_skills: resolveEnabledCatalogSkills(enablement),
            disabled_skills: disabledSkills,
          }
        : { disabled_skills: disabledSkills },
      {
        onError: (error) => {
          displayErrorToast(
            retrieveAxiosErrorMessage(error) || t(I18nKey.ERROR$GENERIC),
          );
        },
      },
    );
  }, [enablement, usesCatalogAllowList, saveSettings, t]);

  const isEnabled = React.useMemo(() => {
    const enabled = buildSkillEnablementFilter(enablement);
    return (skill: SkillInfo) => enabled(skill.name);
  }, [enablement]);

  const setEnabled = React.useCallback(
    (skillName: string, enabled: boolean) => {
      setEnablement((previous) => {
        const allowListed = usesCatalogAllowList && isCatalogSkill(skillName);
        return {
          enabledSkills: allowListed
            ? withMembership(
                resolveEnabledCatalogSkills(previous),
                skillName,
                enabled,
              )
            : previous.enabledSkills,
          // A catalog skill switched back on also leaves the deny-list, where
          // an unmigrated workspace may still hold it.
          disabledSkills: withMembership(
            previous.disabledSkills ?? [],
            skillName,
            !enabled && !allowListed,
          ),
        };
      });
    },
    [usesCatalogAllowList],
  );

  return { isEnabled, setEnabled };
}
