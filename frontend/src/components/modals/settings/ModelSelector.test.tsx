import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelSelector } from "./ModelSelector";

describe("ModelSelector", () => {
  const models = {
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

  it("should display the provider selector", () => {
    render(<ModelSelector models={models} />);

    const selector = screen.getByLabelText("Provider");
    expect(selector).toBeInTheDocument();

    expect(screen.getByText("azure")).toBeInTheDocument();
    expect(screen.getByText("vertex_ai")).toBeInTheDocument();
    expect(screen.getByText("cohere")).toBeInTheDocument();
  });

  it("should disable the model selector if the provider is not selected", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const modelSelector = screen.getByLabelText("Model");
    expect(modelSelector).toBeDisabled();

    const providerSelector = screen.getByLabelText("Provider");
    await user.selectOptions(providerSelector, "vertex_ai");

    expect(modelSelector).not.toBeDisabled();
  });

  it("should display the model selector", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const providerSelector = screen.getByLabelText("Provider");
    await user.selectOptions(providerSelector, "azure");

    expect(screen.getByText("ada")).toBeInTheDocument();
    expect(screen.getByText("gpt-35-turbo")).toBeInTheDocument();

    await user.selectOptions(providerSelector, "vertex_ai");

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

    await user.selectOptions(providerSelector, "azure");
    expect(id).toHaveTextContent("azure/");

    await user.selectOptions(modelSelector, "ada");
    expect(id).toHaveTextContent("azure/ada");

    await user.selectOptions(providerSelector, "cohere");
    expect(id).toHaveTextContent("cohere.");

    await user.selectOptions(modelSelector, "command-r-v1:0");
    expect(id).toHaveTextContent("cohere.command-r-v1:0");
  });
});
