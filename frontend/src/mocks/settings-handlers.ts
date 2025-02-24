import { delay, http, HttpResponse } from "msw";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { ApiSettings, PostApiSettings } from "#/types/settings";

export const MOCK_DEFAULT_USER_SETTINGS: ApiSettings | PostApiSettings = {
  llm_model: DEFAULT_SETTINGS.LLM_MODEL,
  llm_base_url: DEFAULT_SETTINGS.LLM_BASE_URL,
  llm_api_key: DEFAULT_SETTINGS.LLM_API_KEY,
  agent: DEFAULT_SETTINGS.AGENT,
  language: DEFAULT_SETTINGS.LANGUAGE,
  confirmation_mode: DEFAULT_SETTINGS.CONFIRMATION_MODE,
  security_analyzer: DEFAULT_SETTINGS.SECURITY_ANALYZER,
  remote_runtime_resource_factor:
    DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
  github_token_is_set: DEFAULT_SETTINGS.GITHUB_TOKEN_IS_SET,
  enable_default_condenser: DEFAULT_SETTINGS.ENABLE_DEFAULT_CONDENSER,
  user_consents_to_analytics: DEFAULT_SETTINGS.USER_CONSENTS_TO_ANALYTICS,
};

const MOCK_USER_PREFERENCES: {
  settings: ApiSettings | PostApiSettings;
} = {
  settings: MOCK_DEFAULT_USER_SETTINGS,
};

export const SETTINGS_HANDLERS = [
  http.get("/api/settings", async () => {
    await delay();
    const settings: ApiSettings = {
      ...MOCK_USER_PREFERENCES.settings,
    };
    // @ts-expect-error - mock types
    if (settings.github_token) settings.github_token_is_set = true;

    return HttpResponse.json(settings);
  }),
  http.post("/api/settings", async ({ request }) => {
    const body = await request.json();

    if (body) {
      let newSettings: Partial<PostApiSettings> = {};
      if (typeof body === "object") {
        newSettings = { ...body };
        if (newSettings.unset_github_token) {
          newSettings.github_token = undefined;
          newSettings.github_token_is_set = false;
          delete newSettings.unset_github_token;
        }
      }

      MOCK_USER_PREFERENCES.settings = {
        ...MOCK_USER_PREFERENCES.settings,
        ...newSettings,
      };

      return HttpResponse.json(null, { status: 200 });
    }

    return HttpResponse.json(null, { status: 400 });
  }),
  http.post("/api/settings/reset", async () => {
    MOCK_USER_PREFERENCES.settings = MOCK_DEFAULT_USER_SETTINGS;
    return HttpResponse.json(null, { status: 200 });
  }),
];
