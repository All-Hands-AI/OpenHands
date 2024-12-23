import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelSelector } from "#/components/shared/modals/settings/model-selector";

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
    render(<ModelSelector models={models} />);

    const selector = screen.getByLabelText("LLM Provider");
    expect(selector).toBeInTheDocument();

    await user.click(selector);

    await waitFor(() => {
      expect(screen.getByText("OpenAI")).toBeInTheDocument();
      expect(screen.getByText("Azure")).toBeInTheDocument();
      expect(screen.getByText("VertexAI")).toBeInTheDocument();
      expect(screen.getByText("cohere")).toBeInTheDocument();
    });
  });

  it("should disable the model selector if the provider is not selected", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const modelSelector = screen.getByLabelText("LLM Model");
    expect(modelSelector).toBeDisabled();

    const providerSelector = screen.getByLabelText("LLM Provider");
    await user.click(providerSelector);

    await waitFor(() => {
      const vertexAI = screen.getByText("VertexAI");
      expect(vertexAI).toBeInTheDocument();
      return vertexAI;
    }).then((vertexAI) => user.click(vertexAI));

    await waitFor(() => {
      expect(modelSelector).not.toBeDisabled();
    });
  });

  it("should display the model selector", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const providerSelector = screen.getByLabelText("LLM Provider");
    await user.click(providerSelector);

    await waitFor(() => {
      const azureProvider = screen.getByText("Azure");
      expect(azureProvider).toBeInTheDocument();
      return azureProvider;
    }, { timeout: 10000 }).then((azureProvider) => user.click(azureProvider));

    const modelSelector = screen.getByLabelText("LLM Model");
    await user.click(modelSelector);

    await waitFor(() => {
      expect(screen.getByText("ada")).toBeInTheDocument();
      expect(screen.getByText("gpt-35-turbo")).toBeInTheDocument();
    }, { timeout: 10000 });

    await user.click(providerSelector);
    await waitFor(() => {
      const vertexProvider = screen.getByText("VertexAI");
      expect(vertexProvider).toBeInTheDocument();
      return vertexProvider;
    }, { timeout: 10000 }).then((vertexProvider) => user.click(vertexProvider));

    await user.click(modelSelector);

    await waitFor(() => {
      console.log("Checking for chat-bison models");
      console.log("Document body:", document.body.innerHTML);
      console.log("All text content:", screen.getByTestId("model-selector").textContent);
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
      
      const options = screen.getAllByRole("option");
      console.log("Available options:", options.map(option => option.textContent));
      
      // Use a more flexible matching approach
      const chatBisonOption = options.find(option => option.textContent?.toLowerCase().includes("chat-bison") && !option.textContent?.toLowerCase().includes("32k"));
      const chatBison32kOption = options.find(option => option.textContent?.toLowerCase().includes("chat-bison-32k"));
      
      console.log("chatBisonOption:", chatBisonOption);
      console.log("chatBison32kOption:", chatBison32kOption);
      
      expect(chatBisonOption).toBeTruthy();
      expect(chatBison32kOption).toBeTruthy();
    }, { timeout: 10000 });
  }, 30000);

  it("should display the correct models for each provider", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const providerSelector = screen.getByLabelText("LLM Provider");
    const modelSelector = screen.getByLabelText("LLM Model");

    // Helper function to log the current state
    const logState = () => {
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
      console.log("Document body:", document.body.innerHTML);
    };

    // Helper function to get options
    const getOptions = async () => {
      await user.click(modelSelector);
      return screen.getAllByRole("option");
    };

    // Check Azure models
    await user.click(providerSelector);
    await waitFor(() => {
      const azureOption = screen.getByText("Azure");
      expect(azureOption).toBeInTheDocument();
      return azureOption;
    }).then(azureOption => user.click(azureOption));
    
    await waitFor(async () => {
      logState();
      const options = await getOptions();
      console.log("Azure options:", options.map(option => option.textContent));
      expect(options.some(option => option.textContent?.includes("ada"))).toBe(true);
      expect(options.some(option => option.textContent?.includes("gpt-35-turbo"))).toBe(true);
    }, { timeout: 5000 });

    // Check VertexAI models
    await user.click(providerSelector);
    await waitFor(() => {
      const vertexAIOption = screen.getByText("VertexAI");
      expect(vertexAIOption).toBeInTheDocument();
      return vertexAIOption;
    }).then(vertexAIOption => user.click(vertexAIOption));
    
    await waitFor(async () => {
      logState();
      const options = await getOptions();
      console.log("VertexAI options:", options.map(option => option.textContent));
      const chatBisonOption = options.find(option => option.textContent?.toLowerCase().includes("chat-bison") && !option.textContent?.toLowerCase().includes("32k"));
      const chatBison32kOption = options.find(option => option.textContent?.toLowerCase().includes("chat-bison-32k"));
      console.log("chatBisonOption:", chatBisonOption);
      console.log("chatBison32kOption:", chatBison32kOption);
      expect(chatBisonOption).toBeTruthy();
      expect(chatBison32kOption).toBeTruthy();
    }, { timeout: 5000 });

    // Check OpenAI models
    await user.click(providerSelector);
    await waitFor(() => {
      const openAIOption = screen.getByText("OpenAI");
      expect(openAIOption).toBeInTheDocument();
      return openAIOption;
    }).then(openAIOption => user.click(openAIOption));
    
    await waitFor(async () => {
      logState();
      const options = await getOptions();
      console.log("OpenAI options:", options.map(option => option.textContent));
      expect(options.some(option => option.textContent?.includes("gpt-4"))).toBe(true);
      expect(options.some(option => option.textContent?.includes("gpt-3.5-turbo"))).toBe(true);
    }, { timeout: 5000 });

    // Check Cohere models
    await user.click(providerSelector);
    await waitFor(() => {
      const cohereOption = screen.getByText("cohere");
      expect(cohereOption).toBeInTheDocument();
      return cohereOption;
    }).then(cohereOption => user.click(cohereOption));
    
    await waitFor(async () => {
      logState();
      const options = await getOptions();
      console.log("Cohere options:", options.map(option => option.textContent));
      expect(options.some(option => option.textContent?.includes("command"))).toBe(true);
    }, { timeout: 5000 });
  }, 60000);

  it("should call onModelChange when the model is changed", async () => {
    const user = userEvent.setup();
    const onModelChange = vi.fn();
    render(<ModelSelector models={models} onModelChange={onModelChange} />);

    const providerSelector = screen.getByLabelText("LLM Provider");
    const modelSelector = screen.getByLabelText("LLM Model");

    // Helper function to log the current state
    const logState = () => {
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
      console.log("onModelChange calls:", onModelChange.mock.calls);
    };

    // Select Azure provider
    await user.click(providerSelector);
    await waitFor(() => user.click(screen.getByText("Azure")));
    logState();

    await waitFor(() => {
      expect(onModelChange).toHaveBeenCalledWith(expect.stringMatching(/^azure\//));
    }, { timeout: 5000 });
    onModelChange.mockClear();

    // Select a model
    await user.click(modelSelector);
    await waitFor(() => user.click(screen.getByText("gpt-35-turbo")));
    logState();

    await waitFor(() => {
      expect(onModelChange).toHaveBeenCalledWith("azure/gpt-35-turbo");
    }, { timeout: 5000 });
    onModelChange.mockClear();

    // Change provider to OpenAI
    await user.click(providerSelector);
    await waitFor(() => user.click(screen.getByText("OpenAI")));
    logState();

    await waitFor(() => {
      expect(onModelChange).toHaveBeenCalledWith(expect.stringMatching(/^openai\//));
    }, { timeout: 5000 });
    onModelChange.mockClear();

    // Select a model
    await user.click(modelSelector);
    await waitFor(() => user.click(screen.getByText("gpt-4")));
    logState();

    await waitFor(() => {
      expect(onModelChange).toHaveBeenCalledWith("openai/gpt-4");
    }, { timeout: 5000 });

    // Change provider to Cohere
    await user.click(providerSelector);
    await waitFor(() => user.click(screen.getByText("cohere")));
    logState();

    await waitFor(() => {
      expect(onModelChange).toHaveBeenCalledWith(expect.stringMatching(/^cohere\./));
    }, { timeout: 5000 });
    onModelChange.mockClear();

    // Select a model
    await user.click(modelSelector);
    await waitFor(() => user.click(screen.getByText(/command/i)));
    logState();

    await waitFor(() => {
      expect(onModelChange).toHaveBeenCalledWith(expect.stringMatching(/^cohere\.command/));
    }, { timeout: 5000 });
  }, 60000);

  it("should display the correct models for each provider", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const providerSelector = screen.getByLabelText("LLM Provider");
    const modelSelector = screen.getByLabelText("LLM Model");

    // Helper function to log the current state
    const logState = () => {
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
    };

    // Helper function to get options
    const getOptions = async () => {
      await user.click(modelSelector);
      return screen.getAllByRole("option");
    };

    // Check Azure models
    await user.click(providerSelector);
    await waitFor(() => user.click(screen.getByText("Azure")));
    logState();
    
    await waitFor(async () => {
      const options = await getOptions();
      console.log("Azure options:", options.map(option => option.textContent));
      expect(options.some(option => option.textContent?.includes("ada"))).toBe(true);
      expect(options.some(option => option.textContent?.includes("gpt-35-turbo"))).toBe(true);
    }, { timeout: 5000 });

    // Check VertexAI models
    await user.click(providerSelector);
    await waitFor(() => user.click(screen.getByText("VertexAI")));
    logState();
    
    await waitFor(async () => {
      const options = await getOptions();
      console.log("VertexAI options:", options.map(option => option.textContent));
      const chatBisonOption = options.find(option => option.textContent?.toLowerCase().includes("chat-bison") && !option.textContent?.toLowerCase().includes("32k"));
      const chatBison32kOption = options.find(option => option.textContent?.toLowerCase().includes("chat-bison-32k"));
      console.log("chatBisonOption:", chatBisonOption);
      console.log("chatBison32kOption:", chatBison32kOption);
      expect(chatBisonOption).toBeTruthy();
      expect(chatBison32kOption).toBeTruthy();
    }, { timeout: 5000 });

    // Check OpenAI models
    await user.click(providerSelector);
    await waitFor(() => user.click(screen.getByText("OpenAI")));
    logState();
    
    await waitFor(async () => {
      const options = await getOptions();
      console.log("OpenAI options:", options.map(option => option.textContent));
      expect(options.some(option => option.textContent?.includes("gpt-4"))).toBe(true);
      expect(options.some(option => option.textContent?.includes("gpt-3.5-turbo"))).toBe(true);
    }, { timeout: 5000 });

    // Check Cohere models
    await user.click(providerSelector);
    await waitFor(() => user.click(screen.getByText("cohere")));
    logState();
    
    await waitFor(async () => {
      const options = await getOptions();
      console.log("Cohere options:", options.map(option => option.textContent));
      expect(options.some(option => option.textContent?.includes("command"))).toBe(true);
    }, { timeout: 5000 });
  }, 60000);

  it("should call onModelChange when the model is changed", async () => {
    const user = userEvent.setup();
    const onModelChange = vi.fn();
    render(<ModelSelector models={models} onModelChange={onModelChange} />);

    const providerSelector = screen.getByLabelText("LLM Provider");
    const modelSelector = screen.getByLabelText("LLM Model");

    await user.click(providerSelector);
    await waitFor(() => {
      const azureProvider = screen.getByText("Azure");
      expect(azureProvider).toBeInTheDocument();
      return azureProvider;
    }, { timeout: 10000 }).then((azureProvider) => user.click(azureProvider));

    expect(onModelChange).toHaveBeenCalledWith("azure/");
    onModelChange.mockClear();

    await user.click(modelSelector);
    await waitFor(() => {
      const adaModel = screen.getByText("ada");
      expect(adaModel).toBeInTheDocument();
      return adaModel;
    }, { timeout: 10000 }).then((adaModel) => user.click(adaModel));

    await waitFor(() => {
      console.log("Checking onModelChange call");
      console.log("onModelChange mock calls:", onModelChange.mock.calls);
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
      expect(onModelChange).toHaveBeenCalledWith("azure/ada");
    }, { timeout: 10000 });

    onModelChange.mockClear();

    await user.click(modelSelector);
    await waitFor(() => {
      const gptModel = screen.getByText("gpt-35-turbo");
      expect(gptModel).toBeInTheDocument();
      return gptModel;
    }, { timeout: 10000 }).then((gptModel) => user.click(gptModel));

    await waitFor(() => {
      console.log("Checking onModelChange call for gpt-35-turbo");
      console.log("onModelChange mock calls:", onModelChange.mock.calls);
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
      expect(onModelChange).toHaveBeenCalledWith("azure/gpt-35-turbo");
    }, { timeout: 10000 });

    onModelChange.mockClear();

    await user.click(providerSelector);
    await waitFor(() => {
      const cohereProvider = screen.getByText("cohere");
      expect(cohereProvider).toBeInTheDocument();
      return cohereProvider;
    }, { timeout: 10000 }).then((cohereProvider) => user.click(cohereProvider));

    expect(onModelChange).toHaveBeenCalledWith("cohere.");
    onModelChange.mockClear();

    await user.click(modelSelector);
    await waitFor(() => {
      const options = screen.getAllByRole("option");
      console.log("Available options:", options.map(option => option.textContent));
      const commandModel = options.find(option => option.textContent?.includes("command-r-v1:0"));
      expect(commandModel).toBeTruthy();
      return commandModel;
    }, { timeout: 10000 }).then((commandModel) => user.click(commandModel));

    await waitFor(() => {
      console.log("Checking onModelChange call for cohere");
      console.log("onModelChange mock calls:", onModelChange.mock.calls);
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
      expect(onModelChange).toHaveBeenCalledWith("cohere.command-r-v1:0");
    }, { timeout: 10000 });
  }, 60000);

  it("should call onModelChange when the provider is changed", async () => {
    const user = userEvent.setup();
    const onModelChange = vi.fn();
    render(<ModelSelector models={models} onModelChange={onModelChange} />);

    const providerSelector = screen.getByLabelText("LLM Provider");

    await user.click(providerSelector);
    await waitFor(() => {
      const azureProvider = screen.getByText("Azure");
      expect(azureProvider).toBeInTheDocument();
      return azureProvider;
    }, { timeout: 10000 }).then((azureProvider) => user.click(azureProvider));

    await waitFor(() => {
      console.log("Checking onModelChange call after provider change");
      console.log("onModelChange mock calls:", onModelChange.mock.calls);
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
      expect(onModelChange).toHaveBeenCalledWith("azure/");
    }, { timeout: 10000 });

    onModelChange.mockClear();

    await user.click(providerSelector);
    await waitFor(() => {
      const cohereProvider = screen.getByText("cohere");
      expect(cohereProvider).toBeInTheDocument();
      return cohereProvider;
    }, { timeout: 10000 }).then((cohereProvider) => user.click(cohereProvider));

    await waitFor(() => {
      console.log("Checking onModelChange call after changing to cohere");
      console.log("onModelChange mock calls:", onModelChange.mock.calls);
      console.log("Provider value:", screen.getByLabelText("LLM Provider").getAttribute("value"));
      console.log("Model value:", screen.getByLabelText("LLM Model").getAttribute("value"));
      expect(onModelChange).toHaveBeenCalledWith("cohere.");
    }, { timeout: 10000 });
  }, 30000);

  it("should have a default value if passed", async () => {
    render(<ModelSelector models={models} currentModel="azure/ada" />);

    await waitFor(() => {
      expect(screen.getByLabelText("LLM Provider")).toHaveValue("Azure");
      expect(screen.getByLabelText("LLM Model")).toHaveValue("ada");
    });
  });

  it("should disable provider if isDisabled is true", async () => {
    render(<ModelSelector models={models} isDisabled={true} />);

    await waitFor(() => {
      expect(screen.getByLabelText("LLM Provider")).toBeDisabled();
      expect(screen.getByLabelText("LLM Model")).toBeDisabled();
    });
  });

  it("should display the verified models in the correct order", async () => {
    const user = userEvent.setup();
    render(<ModelSelector models={models} />);

    const providerSelector = screen.getByLabelText("LLM Provider");
    await user.click(providerSelector);

    await waitFor(() => {
      const verifiedProviders = screen.getAllByRole("option", { name: /OpenAI|Azure|VertexAI/ });
      expect(verifiedProviders.length).toBe(3);
      expect(verifiedProviders[0]).toHaveTextContent("OpenAI");
      expect(verifiedProviders[1]).toHaveTextContent("Azure");
      expect(verifiedProviders[2]).toHaveTextContent("VertexAI");
    });

    await waitFor(() => {
      const azureProvider = screen.getByText("Azure");
      expect(azureProvider).toBeInTheDocument();
      return azureProvider;
    }).then((azureProvider) => user.click(azureProvider));

    const modelSelector = screen.getByLabelText("LLM Model");
    await user.click(modelSelector);

    await waitFor(() => {
      const verifiedModels = screen.getAllByRole("option", { name: /ada|gpt-35-turbo/ });
      expect(verifiedModels.length).toBe(2);
      expect(verifiedModels[0]).toHaveTextContent("ada");
      expect(verifiedModels[1]).toHaveTextContent("gpt-35-turbo");
    });
  });
});
