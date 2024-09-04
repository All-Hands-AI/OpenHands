import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, it } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import RootLayout from "./RootLayout";

const router = createMemoryRouter([
  {
    path: "/",
    element: <RootLayout />,
  },
]);

const renderRootLayout = () => render(<RouterProvider router={router} />);

describe("RootLayout", () => {
  it.todo("should render the home screen by default");
  it.todo("should display user details");
  it.todo("should display an error if the user did not enter the gh token");
  it.todo("should display an error if unable to fetch models or agents");

  it("should display the GH token form on initial start", () => {
    renderRootLayout();
    screen.getByTestId("gh-token-form");
  });
});
