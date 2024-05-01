import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { act } from "react-dom/test-utils";
import userEvent from "@testing-library/user-event";
import ChatInterface from "./ChatInterface";

describe("ChatInterface", () => {
  it("should render the messages and input", () => {
    render(<ChatInterface />);
    expect(screen.queryAllByTestId("message")).toHaveLength(0);
  });

  it("should render the new message the user has typed", () => {
    render(<ChatInterface />);

    const input = screen.getByRole("textbox");

    act(() => {
      userEvent.type(input, "my message{enter}");
    });

    expect(screen.getByText("my message")).toBeInTheDocument();
  });
});
