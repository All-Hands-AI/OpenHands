import { extractModelAndProvider } from "./extract-model-and-provider";
import { organizeModelsAndProviders } from "./organize-models-and-providers";

/**
 * Check if a model is a custom model. A custom model is a model that is not part of the default models.
 * @param models Full list of models
 * @param model Model to check
 * @returns Whether the model is a custom model
 */
export const isCustomModel = (models: string[], model: string): boolean => {
  if (!model) return false;

  const organizedModels = organizeModelsAndProviders(models);
  const { provider: extractedProvider, model: extractedModel } =
    extractModelAndProvider(model);

  const isKnownModel =
    extractedProvider in organizedModels &&
    organizedModels[extractedProvider].models.includes(extractedModel);

  return !isKnownModel;
};
