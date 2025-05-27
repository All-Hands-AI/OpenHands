/**
 * Checks if a string is a translation key
 * Translation keys are in the format CATEGORY$KEY
 */
export function isTranslationKey(str: string): boolean {
  return typeof str === "string" && /^[A-Z_]+\$[A-Z_]+$/.test(str);
}
