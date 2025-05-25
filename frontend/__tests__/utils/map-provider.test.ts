import { test, expect } from "vitest";
import { mapProvider, getProviderKey } from "../../src/utils/map-provider";

test("mapProvider", () => {
  expect(mapProvider("azure")).toBe("Azure");
  expect(mapProvider("azure_ai")).toBe("Azure AI Studio");
  expect(mapProvider("vertex_ai")).toBe("VertexAI");
  expect(mapProvider("palm")).toBe("PaLM");
  expect(mapProvider("gemini")).toBe("Gemini");
  expect(mapProvider("anthropic")).toBe("Anthropic");
  expect(mapProvider("sagemaker")).toBe("AWS SageMaker");
  expect(mapProvider("bedrock")).toBe("AWS Bedrock");
  expect(mapProvider("mistral")).toBe("Mistral AI");
  expect(mapProvider("anyscale")).toBe("Anyscale");
  expect(mapProvider("databricks")).toBe("Databricks");
  expect(mapProvider("ollama")).toBe("Ollama");
  expect(mapProvider("perlexity")).toBe("Perplexity AI");
  expect(mapProvider("friendliai")).toBe("FriendliAI");
  expect(mapProvider("groq")).toBe("Groq");
  expect(mapProvider("fireworks_ai")).toBe("Fireworks AI");
  expect(mapProvider("cloudflare")).toBe("Cloudflare Workers AI");
  expect(mapProvider("deepinfra")).toBe("DeepInfra");
  expect(mapProvider("ai21")).toBe("AI21");
  expect(mapProvider("replicate")).toBe("Replicate");
  expect(mapProvider("voyage")).toBe("Voyage AI");
  expect(mapProvider("openrouter")).toBe("OpenRouter");
});

test("getProviderKey - reverse mapping from display name to provider key", () => {
  // Test all known providers
  expect(getProviderKey("OpenAI")).toBe("openai");
  expect(getProviderKey("Azure")).toBe("azure");
  expect(getProviderKey("Azure AI Studio")).toBe("azure_ai");
  expect(getProviderKey("VertexAI")).toBe("vertex_ai");
  expect(getProviderKey("PaLM")).toBe("palm");
  expect(getProviderKey("Gemini")).toBe("gemini");
  expect(getProviderKey("Anthropic")).toBe("anthropic");
  expect(getProviderKey("AWS SageMaker")).toBe("sagemaker");
  expect(getProviderKey("AWS Bedrock")).toBe("bedrock");
  expect(getProviderKey("Mistral AI")).toBe("mistral");  // Our main fix
  expect(getProviderKey("Anyscale")).toBe("anyscale");
  expect(getProviderKey("Databricks")).toBe("databricks");
  expect(getProviderKey("Ollama")).toBe("ollama");
  expect(getProviderKey("Perplexity AI")).toBe("perlexity");
  expect(getProviderKey("FriendliAI")).toBe("friendliai");
  expect(getProviderKey("Groq")).toBe("groq");
  expect(getProviderKey("Fireworks AI")).toBe("fireworks_ai");
  expect(getProviderKey("Cloudflare Workers AI")).toBe("cloudflare");
  expect(getProviderKey("DeepInfra")).toBe("deepinfra");
  expect(getProviderKey("AI21")).toBe("ai21");
  expect(getProviderKey("Replicate")).toBe("replicate");
  expect(getProviderKey("Voyage AI")).toBe("voyage");
  expect(getProviderKey("OpenRouter")).toBe("openrouter");
});

test("getProviderKey - handles unknown providers gracefully", () => {
  // Should return the input as-is for unknown providers
  expect(getProviderKey("Unknown Provider")).toBe("Unknown Provider");
  expect(getProviderKey("custom-provider")).toBe("custom-provider");
  expect(getProviderKey("")).toBe("");
});

test("getProviderKey - case sensitivity", () => {
  expect(getProviderKey("mistral ai")).toBe("mistral ai");
  expect(getProviderKey("MISTRAL AI")).toBe("MISTRAL AI");
  expect(getProviderKey("Mistral AI")).toBe("mistral");
});

test("mapProvider and getProviderKey are inverse operations", () => {
  const testProviders = ["openai", "mistral", "anthropic", "azure", "vertex_ai"];
  
  testProviders.forEach(providerKey => {
    const displayName = mapProvider(providerKey);
    const reversedKey = getProviderKey(displayName);
    expect(reversedKey).toBe(providerKey);
  });
});
