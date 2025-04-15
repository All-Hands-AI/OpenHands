import OpenHands from "#/api/open-hands";

/**
 * Checks if the user has accepted the Terms of Service
 * @returns Promise<boolean> - True if the user has accepted the TOS, false otherwise
 */
export async function checkTosAcceptance(): Promise<boolean> {
  try {
    const settings = await OpenHands.getSettings();
    return !!settings.accepted_tos;
  } catch (error) {
    console.error("Failed to check TOS acceptance:", error);
    return false;
  }
}