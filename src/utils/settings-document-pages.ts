import type { SettingsSchema, SettingsSectionSchema } from "#/types/settings";

const SETTINGS_EXTENSION_BOUNDARY = "resources";
const SETTINGS_DOCUMENT_PATH = "/settings/document";

export const getDynamicSettingsSections = (
  schema: SettingsSchema | undefined,
): SettingsSectionSchema[] => {
  if (!schema) return [];
  const boundaryIndex = schema.sections.findIndex(
    (section) => section.key === SETTINGS_EXTENSION_BOUNDARY,
  );
  return boundaryIndex === -1 ? [] : schema.sections.slice(boundaryIndex + 1);
};

export const getSettingsDocumentSectionPath = (sectionKey: string) =>
  `${SETTINGS_DOCUMENT_PATH}/${encodeURIComponent(sectionKey)}`;
