import { openHands } from "../open-hands-axios";
import { UserSettings } from "./settings-service.types";

export class SettingsService {
  /**
   * Get the user's settings
   */
  static async getSettings(): Promise<UserSettings> {
    const { data } = await openHands.get<UserSettings>("/api/settings");
    return data;
  }

  /**
   * Save valid settings to the server
   * @param settings - The settings to save
   */
  static async saveSettings(settings: Partial<UserSettings>): Promise<boolean> {
    const data = await openHands.post("/api/settings", settings);
    return data.status === 200;
  }

  /**
   * Reset the user's settings
   */
  static async resetSettings(): Promise<boolean> {
    const response = await openHands.post("/api/reset-settings");
    return response.status === 200;
  }
}
