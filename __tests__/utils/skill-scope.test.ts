import { describe, expect, it } from "vitest";
import type { SkillInfo } from "#/types/settings";
import {
  getSkillKey,
  getSkillScope,
  groupSkillsByScope,
} from "#/utils/skill-scope";

function buildSkill(overrides: Partial<SkillInfo> = {}): SkillInfo {
  return {
    name: "test-skill",
    type: "knowledge",
    source: null,
    ...overrides,
  };
}

describe("getSkillScope", () => {
  it("classifies public catalog skills", () => {
    expect(
      getSkillScope(
        buildSkill({
          source:
            "/Users/test/.openhands/cache/skills/public-skills/skills/deno/SKILL.md",
        }),
      ),
    ).toBe("public");
    expect(getSkillScope(buildSkill({ source: "public" }))).toBe("public");
  });

  it("classifies personal user skills from home directories", () => {
    expect(
      getSkillScope(
        buildSkill({
          source: "/Users/test/.agents/skills/my-skill/SKILL.md",
        }),
      ),
    ).toBe("personal");
    expect(getSkillScope(buildSkill({ source: "user" }))).toBe("personal");
  });

  it("classifies project skills from the workspace", () => {
    const projectDir = "/workspace/project/agent-canvas";
    expect(
      getSkillScope(
        buildSkill({
          source: `${projectDir}/.agents/skills/default-tools/SKILL.md`,
        }),
        projectDir,
      ),
    ).toBe("project");
    expect(getSkillScope(buildSkill({ source: "project" }))).toBe("project");
  });
});

describe("groupSkillsByScope", () => {
  it("groups and sorts skills by scope", () => {
    const grouped = groupSkillsByScope(
      [
        buildSkill({ name: "beta", source: "public" }),
        buildSkill({ name: "alpha", source: "user" }),
        buildSkill({
          name: "gamma",
          source: "/workspace/project/.agents/skills/gamma/SKILL.md",
        }),
      ],
      "/workspace/project",
    );

    expect(grouped.public.map((skill) => skill.name)).toEqual(["beta"]);
    expect(grouped.personal.map((skill) => skill.name)).toEqual(["alpha"]);
    expect(grouped.project.map((skill) => skill.name)).toEqual(["gamma"]);
  });
});

describe("getSkillKey", () => {
  it("produces unique stable keys for skills with the same name from different sources", () => {
    const local = buildSkill({
      name: "skill-creator",
      source: "/Users/test/.agents/skills/skill-creator/SKILL.md",
      type: "knowledge",
    });
    const bundled = buildSkill({
      name: "skill-creator",
      source: "public",
      type: "knowledge",
    });

    const localKey = getSkillKey(local);
    const bundledKey = getSkillKey(bundled);

    expect(localKey).not.toBe(bundledKey);
    expect(localKey).toBe(
      "skill-creator::/Users/test/.agents/skills/skill-creator/SKILL.md::knowledge",
    );
    expect(bundledKey).toBe("skill-creator::public::knowledge");
  });

  it("handles null or empty source by defaulting to public", () => {
    const skill = buildSkill({
      name: "my-skill",
      source: null,
      type: "agentskills",
    });

    expect(getSkillKey(skill)).toBe("my-skill::public::agentskills");
  });
});
