import { render, screen } from "@testing-library/react";
import { describe, it } from "vitest";
import HomeScreen from "#/routes/new-home";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "#/context/auth-context";

const renderHomeScreen = () =>
  render(<HomeScreen />, {
    wrapper: ({ children }) => (
      <AuthProvider>
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      </AuthProvider>
    ),
  });

describe("HomeScreen", () => {
  it("should render", () => {
    renderHomeScreen();
    screen.getByTestId("home-screen");
  });

  it.todo(
    "should render the repository connector and suggested tasks sections",
  );

  it.todo("should filter the suggested tasks based on the selected repository");
});
