import { render, screen, fireEvent } from "@testing-library/react";
import { Provider } from "react-redux";
import store from "../src/store";
import { describe, it, expect, vi } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

const mockNavigate = vi.fn();

// Mock the Remix components
vi.mock("@remix-run/react", async () => {
  const actual = await vi.importActual("@remix-run/react");
  return {
    ...actual,
    useLoaderData: () => ({
      repositories: null,
      githubAuthUrl: null,
    }),
    useRouteLoaderData: () => null,
    useNavigate: () => mockNavigate,
    Await: ({ children }) => children(null),
    Form: ({ children, onSubmit }: any) => (
      <form onSubmit={(e) => { e.preventDefault(); onSubmit?.(e); }}>
        {children}
      </form>
    ),
  };
});

// Mock the SuggestionBox component
vi.mock("../src/components/github-repositories-suggestion-box", () => ({
  GitHubRepositoriesSuggestionBox: () => null,
}));

// Mock the SuggestionBubble component
vi.mock("../src/components/suggestion-bubble", () => ({
  SuggestionBubble: () => null,
}));

// Mock the ChatInput component
vi.mock("../src/components/chat-input", () => ({
  ChatInput: () => null,
}));

describe("Import Project", () => {
  it("should not navigate immediately after selecting a zip file", async () => {
    // Import the component after mocking
    const { default: Home } = await import("../src/routes/_oh._index/route");

    const router = createMemoryRouter([
      {
        path: "/",
        element: (
          <Provider store={store}>
            <Home />
          </Provider>
        ),
      },
    ]);

    render(<RouterProvider router={router} />);

    // Find the file input
    const fileInput = screen.getByLabelText("Upload a .zip");
    
    // Create a mock file
    const file = new File(["dummy content"], "test.zip", { type: "application/zip" });
    
    // Simulate file selection
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // Verify that navigate was not called
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
