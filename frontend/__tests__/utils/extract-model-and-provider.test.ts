import { describe, it, expect } from "vitest";
import { extractModelAndProvider } from "../../src/utils/extract-model-and-provider";

describe("extractModelAndProvider", () => {
  it("should work", () => {
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
      extractModelAndProvider(
        "cloudflare/@cf/mistral/mistral-7b-instruct-v0.1",
      ),
    ).toEqual({
      provider: "cloudflare",
      model: "@cf/mistral/mistral-7b-instruct-v0.1",
      separator: "/",
    });

    expect(extractModelAndProvider("together-ai-21.1b-41b")).toEqual({
      provider: "",
      model: "together-ai-21.1b-41b",
      separator: "",
    });
  });

  it("should add provider for popular models", () => {
    expect(extractModelAndProvider("gpt-4o-mini")).toEqual({
      provider: "openai",
      model: "gpt-4o-mini",
      separator: "/",
    });

    expect(extractModelAndProvider("gpt-4o")).toEqual({
      provider: "openai",
      model: "gpt-4o",
      separator: "/",
    });

    expect(extractModelAndProvider("claude-3-5-sonnet-20240620")).toEqual({
      provider: "anthropic",
      model: "claude-3-5-sonnet-20240620",
      separator: "/",
    });

    expect(extractModelAndProvider("claude-3-haiku-20240307")).toEqual({
      provider: "anthropic",
      model: "claude-3-haiku-20240307",
      separator: "/",
    });

    expect(extractModelAndProvider("claude-2.1")).toEqual({
      provider: "anthropic",
      model: "claude-2.1",
      separator: "/",
    });
  });
});
