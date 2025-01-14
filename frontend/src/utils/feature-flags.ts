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

export const MULTI_CONVERSATION_UI = loadFeatureFlag("MULTI_CONVERSATION_UI");
