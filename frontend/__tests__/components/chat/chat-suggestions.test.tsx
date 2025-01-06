import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../../test-utils";
import { ChatSuggestions } from "#/components/features/chat/chat-suggestions";

describe("ChatSuggestions", () => {
  it("should display translated 'Let's start building!' text", () => {
    const mockOnClick = vi.fn();
    renderWithProviders(<ChatSuggestions onSuggestionsClick={mockOnClick} />);
    
    // This will fail if the translation is missing or not properly set up
    expect(screen.getByText("Let's start building!")).toBeInTheDocument();
  });
});