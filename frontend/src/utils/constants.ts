function loadFeatureFlags() {
  try {
    const item = localStorage.getItem("FEATURE_FLAGS");
    if (!item) {
      return {};
    }
    const featureFlags = JSON.parse(item);
    return featureFlags;
  } catch (e) {
    return {};
  }
}

const featureFlags = loadFeatureFlags();
export const { MULTI_CONVO_UI_IS_ENABLED } = featureFlags;
