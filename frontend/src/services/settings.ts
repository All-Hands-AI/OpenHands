export const LATEST_SETTINGS_VERSION = 4;

export type Settings = {
  LLM_MODEL: string;
  LLM_BASE_URL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string | null;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
};

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "anthropic/claude-3-5-sonnet-20241022",
  LLM_BASE_URL: "",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY: null,
  CONFIRMATION_MODE: false,
  SECURITY_ANALYZER: "",
};

const validKeys = Object.keys(DEFAULT_SETTINGS) as (keyof Settings)[];

/**
 * Get the default settings
 */
export const getDefaultSettings = (): Settings => DEFAULT_SETTINGS;

/**
 * Get the settings from the server or use the default settings if not found
 */
export const getSettings = async (): Promise<Settings> => {
  try {
    const response = await fetch('/api/settings');
    if (!response.ok) {
      throw new Error('Failed to load settings');
    }
    const settings = await response.json();
    return {
      ...DEFAULT_SETTINGS,
      ...settings,
    };
  } catch (error) {
    console.error('Error loading settings:', error);
    return DEFAULT_SETTINGS;
  }
};

/**
 * Save the settings to the server. Only valid settings are saved.
 * @param settings - the settings to save
 */
export const saveSettings = async (settings: Partial<Settings>): Promise<boolean> => {
  try {
    // Filter out invalid keys
    const validSettings = Object.fromEntries(
      Object.entries(settings).filter(([key]) => validKeys.includes(key as keyof Settings))
    );

    // Clean up values
    Object.entries(validSettings).forEach(([key, value]) => {
      if (value === undefined || value === null) {
        validSettings[key] = "";
      } else if (typeof value === 'string') {
        validSettings[key] = value.trim();
      }
    });

    // Get current settings to preserve API key if not provided
    const currentSettings = await getSettings();
    
    const response = await fetch('/api/settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...currentSettings,
        ...validSettings,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to save settings');
    }

    return await response.json();
  } catch (error) {
    console.error('Error saving settings:', error);
    return false;
  }
};
