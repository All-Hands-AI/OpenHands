export type GitProvider = "github" | "gitlab";

export interface UserSettings {
  llm_model: string;
  llm_base_url: string;
  agent: string;
  language: string;
  llm_api_key: string | null;
  confirmation_mode: boolean;
  security_analyzer: string;
  remote_runtime_resource_factor: number | null;
  github_token_is_set: boolean;
  enable_default_condenser: boolean;
  enable_sound_notifications: boolean;
  user_consents_to_analytics: boolean | null;
  provider_tokens: Record<GitProvider, string>;
}

export interface ClientUserSettings extends UserSettings {
  is_new_user: boolean;
}
