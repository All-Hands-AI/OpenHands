import type { SettingsSchema, SettingsValue } from "#/types/settings";

export type SettingsDocumentObject = Record<string, SettingsValue>;

export interface SettingsSecretReference {
  ref: string;
  is_set: boolean;
}

export interface SettingsDocument {
  schema_version: 1;
  agent: SettingsDocumentObject;
  conversation: SettingsDocumentObject;
  product: SettingsDocumentObject;
  resources: {
    llm_profiles: SettingsDocumentObject;
    agent_profiles: SettingsDocumentObject;
    provider_connections: SettingsDocumentObject;
    model_routers: SettingsDocumentObject;
    marketplaces: SettingsValue[];
    credentials: Record<string, SettingsSecretReference>;
    pointers: SettingsDocumentObject;
  };
}

export interface SettingsDocumentPatch {
  agent?: SettingsDocumentObject;
  conversation?: SettingsDocumentObject;
  product?: SettingsDocumentObject | null;
  resources?: { pointers?: SettingsDocumentObject };
}

export type SettingsDocumentSchema = SettingsSchema;
