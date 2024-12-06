import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SuggestionItem } from "#/components/features/suggestions/suggestion-item";

describe("SuggestionItem", () => {
  const suggestionItem = { label: "suggestion1", value: "a long text value" };
  const onClick = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render a suggestion", () => {
    render(<SuggestionItem suggestion={suggestionItem} onClick={onClick} />);

    expect(screen.getByTestId("suggestion")).toBeInTheDocument();
    expect(screen.getByText(/suggestion1/i)).toBeInTheDocument();
  });

  it("should call onClick when clicking a suggestion", async () => {
    const user = userEvent.setup();
    render(<SuggestionItem suggestion={suggestionItem} onClick={onClick} />);

    const suggestion = screen.getByTestId("suggestion");
    await user.click(suggestion);

    expect(onClick).toHaveBeenCalledWith("a long text value");
  });
});
