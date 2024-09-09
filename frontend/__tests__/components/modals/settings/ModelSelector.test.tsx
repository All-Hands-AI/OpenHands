import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelSelector } from "#/components/modals/settings/ModelSelector";

describe("ModelSelector", () => {
  const models = {
    openai: {
      separator: "/",
      models: ["gpt-4o", "gpt-3.5-turbo"],
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
    render(<ModelSelector models={models} />);

    const selector = screen.getByLabelText("Provider");
    expect(selector).toBeInTheDocument();

    await user.click(selector);

    expect(screen.getByText("OpenAI")).toBeInTheDocument();
    expect(screen.getByText("Azure")).toBeInTheDocument();
    expect(screen.getByText("VertexAI")).toBeInTheDocument();
    expect(screen.getByText("cohere")).toBeInTheDocument();
  });

  it("should disable the model selector if the provider is not selected", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const modelSelector = screen.getByLabelText("Model");
    expect(modelSelector).toBeDisabled();

    const providerSelector = screen.getByLabelText("Provider");
    await user.click(providerSelector);

    const vertexAI = screen.getByText("VertexAI");
    await user.click(vertexAI);

    expect(modelSelector).not.toBeDisabled();
  });

  it("should display the model selector", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const providerSelector = screen.getByLabelText("Provider");
    await user.click(providerSelector);

    const azureProvider = screen.getByText("Azure");
    await user.click(azureProvider);

    const modelSelector = screen.getByLabelText("Model");
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

  it("should display the actual litellm model ID as the user is making the selections", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const id = screen.getByTestId("model-id");
    const providerSelector = screen.getByLabelText("Provider");
    const modelSelector = screen.getByLabelText("Model");

    expect(id).toHaveTextContent("No model selected");

    await user.click(providerSelector);
    await user.click(screen.getByText("Azure"));

    expect(id).toHaveTextContent("azure/");

    await user.click(modelSelector);
    await user.click(screen.getByText("ada"));
    expect(id).toHaveTextContent("azure/ada");

    await user.click(providerSelector);
    await user.click(screen.getByText("cohere"));
    expect(id).toHaveTextContent("cohere.");

    await user.click(modelSelector);
    await user.click(screen.getByText("command-r-v1:0"));
    expect(id).toHaveTextContent("cohere.command-r-v1:0");
  });

  it("should call onModelChange when the model is changed", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const providerSelector = screen.getByLabelText("Provider");
    const modelSelector = screen.getByLabelText("Model");

    await user.click(providerSelector);
    await user.click(screen.getByText("Azure"));

    await user.click(modelSelector);
    await user.click(screen.getByText("ada"));

    await user.click(modelSelector);
    await user.click(screen.getByText("gpt-35-turbo"));

    await user.click(providerSelector);
    await user.click(screen.getByText("cohere"));

    await user.click(modelSelector);
    await user.click(screen.getByText("command-r-v1:0"));
  });

  it("should clear the model ID when the provider is cleared", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const providerSelector = screen.getByLabelText("Provider");
    const modelSelector = screen.getByLabelText("Model");

    await user.click(providerSelector);
    await user.click(screen.getByText("Azure"));

    await user.click(modelSelector);
    await user.click(screen.getByText("ada"));

    expect(screen.getByTestId("model-id")).toHaveTextContent("azure/ada");

    await user.clear(providerSelector);

    expect(screen.getByTestId("model-id")).toHaveTextContent(
      "No model selected",
    );
  });

  it("should have a default value if passed", async () => {
    render(<ModelSelector models={models} currentModel="azure/ada" />);

    expect(screen.getByTestId("model-id")).toHaveTextContent("azure/ada");
    expect(screen.getByLabelText("Provider")).toHaveValue("Azure");
    expect(screen.getByLabelText("Model")).toHaveValue("ada");
  });

  it.todo("should disable provider if isDisabled is true");

  it.todo(
    "should display the verified models in the correct order",
    async () => {},
  );
});
