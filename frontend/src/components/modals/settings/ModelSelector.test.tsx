import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelSelector } from "./ModelSelector";

describe("ModelSelector", () => {
  const models = {
    openai: {
      separator: "/",
      models: ["gpt-4o", "gpt-4o-mini"],
    },
    azure: {
      separator: "/",
      models: ["ada", "gpt-35-turbo"],
    },
    vertex_ai: {
      separator: "/",
      models: ["chat-bison", "chat-bison-32k"],
    },
    cohere: {
      separator: ".",
      models: ["command-r-v1:0"],
    },
  };

  it("should display the provider selector", async () => {
    const user = userEvent.setup();
    const onModelChange = vi.fn();
    render(<ModelSelector models={models} onModelChange={onModelChange} />);

    const selector = screen.getByLabelText("LLM Provider");
    expect(selector).toBeInTheDocument();

    await user.click(selector);

    expect(screen.getByText("OpenAI")).toBeInTheDocument();
    expect(screen.getByText("Azure")).toBeInTheDocument();
    expect(screen.getByText("VertexAI")).toBeInTheDocument();
    expect(screen.getByText("cohere")).toBeInTheDocument();
  });

  it("should disable the model selector if the provider is not selected", async () => {
    const user = userEvent.setup();
    const onModelChange = vi.fn();
    render(<ModelSelector models={models} onModelChange={onModelChange} />);

    const modelSelector = screen.getByLabelText("LLM Model");
    expect(modelSelector).toBeDisabled();

    const providerSelector = screen.getByLabelText("LLM Provider");
    await user.click(providerSelector);

    const vertexAI = screen.getByText("VertexAI");
    await user.click(vertexAI);

    expect(modelSelector).not.toBeDisabled();
  });

  it("should display the model selector", async () => {
    const user = userEvent.setup();
    const onModelChange = vi.fn();
    render(<ModelSelector models={models} onModelChange={onModelChange} />);

    const providerSelector = screen.getByLabelText("LLM Provider");
    await user.click(providerSelector);

    const azureProvider = screen.getByText("Azure");
    await user.click(azureProvider);

    const modelSelector = screen.getByLabelText("LLM Model");
    await user.click(modelSelector);

    expect(screen.getByText("ada")).toBeInTheDocument();
    expect(screen.getByText("gpt-35-turbo")).toBeInTheDocument();

    await user.click(providerSelector);
    const vertexProvider = screen.getByText("VertexAI");
    await user.click(vertexProvider);

    await user.click(modelSelector);

    expect(screen.getByText("chat-bison")).toBeInTheDocument();
    expect(screen.getByText("chat-bison-32k")).toBeInTheDocument();
  });

  it("should call onModelChange when the model is changed", async () => {
    const user = userEvent.setup();
    const onModelChange = vi.fn();
    render(<ModelSelector models={models} onModelChange={onModelChange} />);

    const providerSelector = screen.getByLabelText("LLM Provider");
    const modelSelector = screen.getByLabelText("LLM Model");

    await user.click(providerSelector);
    await user.click(screen.getByText("Azure"));

    await user.click(modelSelector);
    await user.click(screen.getByText("ada"));

    expect(onModelChange).toHaveBeenCalledTimes(1);
    expect(onModelChange).toHaveBeenCalledWith("azure/ada");

    await user.click(modelSelector);
    await user.click(screen.getByText("gpt-35-turbo"));

    expect(onModelChange).toHaveBeenCalledTimes(2);
    expect(onModelChange).toHaveBeenCalledWith("azure/gpt-35-turbo");

    await user.click(providerSelector);
    await user.click(screen.getByText("cohere"));

    await user.click(modelSelector);
    await user.click(screen.getByText("command-r-v1:0"));

    expect(onModelChange).toHaveBeenCalledTimes(3);
    expect(onModelChange).toHaveBeenCalledWith("cohere.command-r-v1:0");
  });

  it("should have a default value if passed", async () => {
    const onModelChange = vi.fn();
    render(
      <ModelSelector
        models={models}
        onModelChange={onModelChange}
        defaultModel="azure/ada"
      />,
    );

    expect(screen.getByLabelText("LLM Provider")).toHaveValue("Azure");
    expect(screen.getByLabelText("LLM Model")).toHaveValue("ada");
  });

  it.todo("should disable provider if isDisabled is true");

  it.todo(
    "should display the verified models in the correct order",
    async () => {},
  );
});
