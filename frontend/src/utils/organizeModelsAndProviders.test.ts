import { test } from "vitest";
import { organizeModelsAndProviders } from "./organizeModelsAndProviders";

test("organizeModelsAndProviders", () => {
  const models = [
    "azure/ada",
    "azure/gpt-35-turbo",
    "azure/gpt-3-turbo",
    "azure/standard/1024-x-1024/dall-e-2",
    "vertex_ai_beta/chat-bison",
    "vertex_ai_beta/chat-bison-32k",
    "sagemaker/meta-textgeneration-llama-2-13b",
    "cohere.command-r-v1:0",
    "cloudflare/@cf/mistral/mistral-7b-instruct-v0.1",
    "gpt-4o",
    "together-ai-21.1b-41b",
    "gpt-3.5-turbo",
  ];

  const object = organizeModelsAndProviders(models);

  expect(object).toEqual({
    azure: {
      separator: "/",
      models: [
        "ada",
        "gpt-35-turbo",
        "gpt-3-turbo",
        "standard/1024-x-1024/dall-e-2",
      ],
    },
    vertex_ai_beta: {
      separator: "/",
      models: ["chat-bison", "chat-bison-32k"],
    },
    sagemaker: { separator: "/", models: ["meta-textgeneration-llama-2-13b"] },
    cohere: { separator: ".", models: ["command-r-v1:0"] },
    cloudflare: {
      separator: "/",
      models: ["@cf/mistral/mistral-7b-instruct-v0.1"],
    },
    openai: {
      separator: "/",
      models: ["gpt-4o", "gpt-3.5-turbo"],
    },
    other: {
      separator: "",
      models: ["together-ai-21.1b-41b"],
    },
  });
});
