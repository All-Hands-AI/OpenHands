import { describe, it, expect } from "vitest";
import { extractSettings } from "../../src/utils/settings-utils";

describe("extractSettings - Provider Mapping Integration", () => {
  it("should correctly convert Mistral AI display name to mistral provider key", () => {
    const formData = new FormData();
    formData.set("llm-provider-input", "Mistral AI");
    formData.set("llm-model-input", "devstral-small-2505");
    formData.set("llm-api-key-input", "test-api-key");

    const result = extractSettings(formData);

    expect(result.LLM_MODEL).toBe("mistral/devstral-small-2505");
    expect(result.llm_api_key).toBe("test-api-key");
    expect(result.LLM_API_KEY_SET).toBe(true);
  });

  it("should handle other providers correctly", () => {
    const testCases = [
      { display: "OpenAI", expected: "openai" },
      { display: "Anthropic", expected: "anthropic" },
      { display: "Azure", expected: "azure" },
      { display: "VertexAI", expected: "vertex_ai" },
    ];

    testCases.forEach(({ display, expected }) => {
      const formData = new FormData();
      formData.set("llm-provider-input", display);
      formData.set("llm-model-input", "test-model");

      const result = extractSettings(formData);

      expect(result.LLM_MODEL).toBe(`${expected}/test-model`);
    });
  });

  it("should handle missing provider gracefully", () => {
    const formData = new FormData();
    formData.set("llm-model-input", "test-model");

    const result = extractSettings(formData);

    expect(result.LLM_MODEL).toBeUndefined();
  });

  it("should handle missing model gracefully", () => {
    const formData = new FormData();
    formData.set("llm-provider-input", "Mistral AI");
    // No model set

    const result = extractSettings(formData);

    expect(result.LLM_MODEL).toBeUndefined();
  });

  it("should handle unknown provider by returning as-is", () => {
    const formData = new FormData();
    formData.set("llm-provider-input", "CustomProvider");
    formData.set("llm-model-input", "custom-model");

    const result = extractSettings(formData);

    expect(result.LLM_MODEL).toBe("customprovider/custom-model");
  });

  it("should preserve other settings while fixing provider mapping", () => {
    const formData = new FormData();
    formData.set("llm-provider-input", "Mistral AI");
    formData.set("llm-model-input", "devstral-small-2505");
    formData.set("agent", "CodeActAgent");
    formData.set("language", "en");
    formData.set("use-advanced-options", "true");
    formData.set("confirmation-mode", "true");
    formData.set("security-analyzer", "test-analyzer");

    const result = extractSettings(formData);

    expect(result.LLM_MODEL).toBe("mistral/devstral-small-2505");
    expect(result.AGENT).toBe("CodeActAgent");
    expect(result.LANGUAGE).toBe("en");
    expect(result.CONFIRMATION_MODE).toBe(true);
    expect(result.SECURITY_ANALYZER).toBe("test-analyzer");
  });
});
