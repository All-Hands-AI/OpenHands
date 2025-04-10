import { render, screen } from "@testing-library/react";
import { describe, it } from "vitest";
import HomeScreen from "#/routes/new-home";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

describe("HomeScreen", () => {
  it("should render", () => {
    render(<HomeScreen />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });
    screen.getByTestId("home-screen");
  });
});
