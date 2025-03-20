function loadFeatureFlag(
  flagName: string,
  defaultValue: boolean = false,
): boolean {
  try {
    const stringValue =
      localStorage.getItem(`FEATURE_${flagName}`) || defaultValue.toString();
    const value = !!JSON.parse(stringValue);
    return value;
  } catch (e) {
    return defaultValue;
  }
}

export const BILLING_SETTINGS = () =>
  true || loadFeatureFlag("BILLING_SETTINGS");
export const HIDE_LLM_SETTINGS = () =>
  true || loadFeatureFlag("HIDE_LLM_SETTINGS");
