import { delay, http, HttpResponse } from "msw";
import { UserSettings } from "#/api/settings-service/settings-service.types";
import { DEFAULT_SETTINGS } from "#/services/settings";

const MOCK_USER_PREFERENCES: {
  settings: UserSettings | null;
} = {
  settings: null,
};

export const SETTINGS_HANDLERS = [
  http.get("/api/settings", async () => {
    await delay();
    const { settings } = MOCK_USER_PREFERENCES;

    if (!settings) return HttpResponse.json(null, { status: 404 });

    if (Object.keys(settings.provider_tokens).length > 0)
      settings.github_token_is_set = true;

    return HttpResponse.json(settings);
  }),

  http.post("/api/settings", async ({ request }) => {
    const body = await request.json();

    if (body) {
      let newSettings: Partial<UserSettings> = {};

      if (typeof body === "object") {
        newSettings = { ...body };
      }

      const fullSettings: UserSettings = {
        ...DEFAULT_SETTINGS,
        ...MOCK_USER_PREFERENCES.settings,
        ...newSettings,
      };

      MOCK_USER_PREFERENCES.settings = fullSettings;
      return HttpResponse.json(null, { status: 200 });
    }

    return HttpResponse.json(null, { status: 400 });
  }),

  http.post("/api/reset-settings", async () => {
    await delay();
    MOCK_USER_PREFERENCES.settings = { ...DEFAULT_SETTINGS };
    return HttpResponse.json(null, { status: 200 });
  }),
];
