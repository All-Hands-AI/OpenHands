import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { BrandButton } from "#/components/features/settings/brand-button";
import { LlmSettingsInputsSkeleton } from "#/components/features/settings/llm-settings/llm-settings-inputs-skeleton";
import { SchemaField } from "#/components/features/settings/sdk-settings/schema-field";
import { I18nKey } from "#/i18n/declaration";
import {
  useSaveSettingsDocument,
  useSettingsDocument,
  useSettingsDocumentSchema,
} from "#/hooks/query/use-settings-document";
import { DEFAULT_SETTINGS } from "#/services/settings";
import type { Settings } from "#/types/settings";
import type { SettingsDocumentPatch } from "#/types/settings-document";
import {
  buildInitialSettingsFormValues,
  buildSdkSettingsPayload,
  type SettingsDirtyState,
  type SettingsFormValues,
} from "#/utils/sdk-settings-schema";

const isManagedResourceField = (key: string) =>
  key.startsWith("resources.") && key !== "resources.pointers";

export default function SettingsDocumentRoute() {
  const { t } = useTranslation("openhands");
  const documentQuery = useSettingsDocument();
  const schemaQuery = useSettingsDocumentSchema();
  const saveMutation = useSaveSettingsDocument();
  const [values, setValues] = useState<SettingsFormValues>({});
  const [dirty, setDirty] = useState<SettingsDirtyState>({});

  const formSettings = useMemo(() => {
    if (!documentQuery.data) return null;
    return {
      ...DEFAULT_SETTINGS,
      agent_settings: documentQuery.data,
    } as unknown as Settings;
  }, [documentQuery.data]);

  useEffect(() => {
    if (!formSettings || !schemaQuery.data) return;
    setValues(
      buildInitialSettingsFormValues(
        formSettings,
        schemaQuery.data,
        "agent_settings",
      ),
    );
    setDirty({});
  }, [formSettings, schemaQuery.data]);

  if (documentQuery.isLoading || schemaQuery.isLoading) {
    return <LlmSettingsInputsSkeleton />;
  }

  if (!documentQuery.data || !schemaQuery.data) {
    return (
      <div className="text-danger p-6" data-testid="settings-document-error">
        {t(I18nKey.ERROR$GENERIC)}
      </div>
    );
  }

  const isDirty = Object.values(dirty).some(Boolean);
  const save = () => {
    const patch = buildSdkSettingsPayload(
      schemaQuery.data,
      values,
      dirty,
    ) as SettingsDocumentPatch;
    saveMutation.mutate(patch, {
      onSuccess: () => setDirty({}),
    });
  };

  return (
    <div
      className="flex flex-col gap-8 p-6"
      data-testid="settings-document-page"
    >
      <h1 className="text-2xl font-semibold">{t(I18nKey.SETTINGS$TITLE)}</h1>

      {schemaQuery.data.sections.map((section) => (
        <section key={section.key} className="flex flex-col gap-4">
          <h2 className="text-lg font-medium">{section.label}</h2>
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            {section.fields.map((field) => (
              <SchemaField
                key={field.key}
                field={field}
                value={values[field.key] ?? ""}
                isDisabled={
                  saveMutation.isPending || isManagedResourceField(field.key)
                }
                onChange={(value) => {
                  setValues((current) => ({
                    ...current,
                    [field.key]: value,
                  }));
                  setDirty((current) => ({
                    ...current,
                    [field.key]: true,
                  }));
                }}
              />
            ))}
          </div>
        </section>
      ))}

      <div className="flex justify-start">
        <BrandButton
          testId="settings-document-save"
          type="button"
          variant="primary"
          isDisabled={!isDirty || saveMutation.isPending}
          onClick={save}
        >
          {saveMutation.isPending
            ? t(I18nKey.SETTINGS$SAVING)
            : t(I18nKey.SETTINGS$SAVE_CHANGES)}
        </BrandButton>
      </div>
    </div>
  );
}
