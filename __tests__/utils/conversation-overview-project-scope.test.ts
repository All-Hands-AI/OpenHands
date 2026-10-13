import { describe, expect, it } from "vitest";
import type { SkillInfo } from "#/types/settings";
import {
  CONVERSATION_OVERVIEW_PROJECT_SCOPE,
  filterSkillsByProjectScope,
  sortSkillsByProjectRelevance,
} from "#/utils/conversation-overview-project-scope";

function buildSkill(
  overrides: Partial<SkillInfo> & Pick<SkillInfo, "name">,
): SkillInfo {
  return {
    type: "knowledge",
    source: "public",
    description: null,
    triggers: [],
    license: null,
    compatibility: null,
    metadata: null,
    allowed_tools: null,
    is_agentskills_format: true,
    disable_model_invocation: false,
    ...overrides,
  };
}

describe("conversation overview project scope", () => {
  it("filters and sorts skills with project skills first", () => {
    const skills = [
      buildSkill({ name: "public-z", source: "public" }),
      buildSkill({ name: "project-a", source: "project" }),
      buildSkill({ name: "personal-b", source: "user" }),
    ];

    expect(
      filterSkillsByProjectScope(
        skills,
        CONVERSATION_OVERVIEW_PROJECT_SCOPE.project,
        "/workspace/demo",
      ).map((skill) => skill.name),
    ).toEqual(["project-a"]);

    expect(
      sortSkillsByProjectRelevance(skills, "/workspace/demo").map(
        (skill) => skill.name,
      ),
    ).toEqual(["project-a", "personal-b", "public-z"]);
  });
});
