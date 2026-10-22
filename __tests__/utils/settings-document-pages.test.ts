import { describe, expect, it } from "vitest";
import {
  getDynamicSettingsSections,
  getSettingsDocumentSectionPath,
} from "#/utils/settings-document-pages";
import type { SettingsSchema } from "#/types/settings";

const schema = {
  model_name: "SettingsDocument",
  sections: [
    { key: "product.general", label: "General", fields: [] },
    { key: "resources", label: "Resources", fields: [] },
    {
      key: "product.prototype",
      label: "Prototype settings",
      fields: [],
    },
  ],
} satisfies SettingsSchema;

describe("settings document pages", () => {
  it("exposes schema extension sections after the canonical resources boundary", () => {
    expect(getDynamicSettingsSections(schema)).toEqual([schema.sections[2]]);
  });

  it("does not expose sections when the canonical boundary is absent", () => {
    expect(
      getDynamicSettingsSections({
        ...schema,
        sections: schema.sections.slice(0, 1),
      }),
    ).toEqual([]);
  });

  it("builds a route-safe settings section path", () => {
    expect(getSettingsDocumentSectionPath("product.team preferences")).toBe(
      "/settings/document/product.team%20preferences",
    );
  });
});
