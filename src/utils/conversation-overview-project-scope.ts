import type { SkillInfo } from "#/types/settings";
import {
  getSkillScope,
  SKILL_SCOPE_ORDER,
  type SkillScope,
} from "#/utils/skill-scope";

export const CONVERSATION_OVERVIEW_PROJECT_SCOPE = {
  project: "project",
  all: "all",
} as const;

export type ConversationOverviewProjectScope =
  (typeof CONVERSATION_OVERVIEW_PROJECT_SCOPE)[keyof typeof CONVERSATION_OVERVIEW_PROJECT_SCOPE];

export function isSkillForProject(
  skill: SkillInfo,
  projectDir?: string | null,
): boolean {
  return getSkillScope(skill, projectDir) === "project";
}

export function filterSkillsByProjectScope(
  skills: SkillInfo[],
  scope: ConversationOverviewProjectScope,
  projectDir?: string | null,
): SkillInfo[] {
  if (scope === CONVERSATION_OVERVIEW_PROJECT_SCOPE.all) {
    return skills;
  }
  return skills.filter((skill) => isSkillForProject(skill, projectDir));
}

export function sortSkillsByProjectRelevance(
  skills: SkillInfo[],
  projectDir?: string | null,
): SkillInfo[] {
  return [...skills].sort((left, right) => {
    const leftScope = getSkillScope(left, projectDir);
    const rightScope = getSkillScope(right, projectDir);
    const leftOrder = SKILL_SCOPE_ORDER.indexOf(leftScope as SkillScope);
    const rightOrder = SKILL_SCOPE_ORDER.indexOf(rightScope as SkillScope);
    if (leftOrder !== rightOrder) {
      return leftOrder - rightOrder;
    }
    return left.name.localeCompare(right.name);
  });
}
