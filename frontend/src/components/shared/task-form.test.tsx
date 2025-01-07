import React from "react";
import { render, screen } from "@testing-library/react";
import { TaskForm } from "./task-form";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import initialQueryReducer from "#/state/initial-query-slice";



import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("react-router", () => ({
  useNavigation: () => ({ state: "idle" }),
  useNavigate: () => vi.fn(),
}));

vi.mock("#/context/auth-context", () => ({
  useAuth: () => ({
    gitHubToken: null,
  }),
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

describe("TaskForm", () => {
  beforeEach(() => {
    vi.mock("react-i18next", () => ({
      useTranslation: () => ({
        t: (key: string) => {
          if (key === "SUGGESTIONS$WHAT_TO_BUILD") {
            return "What do you want to build?";
          }
          return key;
        },
      }),
    }));
  });
  it("should use i18n key for placeholder text", () => {
    const store = configureStore({
      reducer: {
        initialQuery: initialQueryReducer,
      },
    });

    const ref = React.createRef<HTMLFormElement>();
    render(
      <Provider store={store}>

          <TaskForm ref={ref} />

      </Provider>
    );

    // The placeholder text should be translated
    const input = screen.getByPlaceholderText("What do you want to build?");
    expect(input).toBeInTheDocument();
  });
});