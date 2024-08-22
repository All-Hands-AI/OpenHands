import { extractModelAndProvider } from "./extractModelAndProvider";

test("extractModelAndProvider", () => {
  expect(extractModelAndProvider("azure/ada")).toEqual({
    provider: "azure",
    model: "ada",
    separator: "/",
  });

  expect(
    extractModelAndProvider("azure/standard/1024-x-1024/dall-e-2"),
  ).toEqual({
    provider: "azure",
    model: "standard/1024-x-1024/dall-e-2",
    separator: "/",
  });

  expect(extractModelAndProvider("vertex_ai_beta/chat-bison")).toEqual({
    provider: "vertex_ai_beta",
    model: "chat-bison",
    separator: "/",
  });

  expect(extractModelAndProvider("cohere.command-r-v1:0")).toEqual({
    provider: "cohere",
    model: "command-r-v1:0",
    separator: ".",
  });

  expect(
    extractModelAndProvider("cloudflare/@cf/mistral/mistral-7b-instruct-v0.1"),
  ).toEqual({
    provider: "cloudflare",
    model: "@cf/mistral/mistral-7b-instruct-v0.1",
    separator: "/",
  });

  expect(extractModelAndProvider("gpt-4o")).toEqual({
    provider: "",
    model: "gpt-4o",
    separator: "",
  });

  expect(extractModelAndProvider("together-ai-21.1b-41b")).toEqual({
    provider: "",
    model: "together-ai-21.1b-41b",
    separator: "",
  });

  expect(extractModelAndProvider("gpt-3.5-turbo")).toEqual({
    provider: "",
    model: "gpt-3.5-turbo",
    separator: "",
  });
});
