import { render, screen } from "@testing-library/react";
import { ChatInput } from "#/components/features/chat/chat-input";
import { describe, it, expect, vi } from "vitest";

// Mock TipTapEditor component
vi.mock("#/components/features/chat/tiptap-editor", () => ({
  TipTapEditor: ({ value, onChange, onSubmit, placeholder, disabled, className }: any) => (
    <div 
      data-testid="mock-tiptap-editor"
      data-value={value}
      data-disabled={disabled}
      data-placeholder={placeholder}
      className={className}
    >
      <button onClick={() => onChange("new value")}>Change</button>
      <button onClick={() => onSubmit()}>Submit</button>
    </div>
  ),
}));

describe("ChatInput with TipTap", () => {
  it("renders the TipTap editor", () => {
    const onSubmit = vi.fn();
    
    render(
      <ChatInput
        onSubmit={onSubmit}
      />
    );

    expect(screen.getByTestId("mock-tiptap-editor")).toBeInTheDocument();
  });

  it("passes the correct props to TipTapEditor", () => {
    const onSubmit = vi.fn();
    const onChange = vi.fn();
    
    render(
      <ChatInput
        value="Test value"
        onSubmit={onSubmit}
        onChange={onChange}
        disabled={true}
        className="test-class"
      />
    );

    const editor = screen.getByTestId("mock-tiptap-editor");
    expect(editor).toHaveAttribute("data-value", "Test value");
    expect(editor).toHaveAttribute("data-disabled", "true");
  });

  it("handles submit button click", () => {
    const onSubmit = vi.fn();
    
    render(
      <ChatInput
        value="Test value"
        onSubmit={onSubmit}
      />
    );

    // Click the submit button
    screen.getByText("Submit").click();
    
    expect(onSubmit).toHaveBeenCalled();
  });
});