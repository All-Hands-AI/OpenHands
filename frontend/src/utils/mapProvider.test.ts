import { test, expect } from "vitest";

const MAP_PROVIDER = {
  azure: "Azure",
  azure_ai: "Azure AI Studio",
  vertex_ai: "VertexAI",
  palm: "PaLM",
  gemini: "Gemini",
  anthropic: "Anthropic",
  sagemaker: "AWS SageMaker",
  bedrock: "AWS Bedrock",
  mistral: "Mistral AI",
  anyscale: "Anyscale",
  databricks: "Databricks",
  ollama: "Ollama",
  perlexity: "Perplexity AI",
  friendliai: "FriendliAI",
  groq: "Groq",
  fireworks_ai: "Fireworks AI",
  cloudflare: "Cloudflare Workers AI",
  deepinfra: "DeepInfra",
  ai21: "AI21",
  replicate: "Replicate",
  voyage: "Voyage AI",
  openrouter: "OpenRouter",
};

const mapProvider = (provider: keyof typeof MAP_PROVIDER) =>
  MAP_PROVIDER[provider];

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
