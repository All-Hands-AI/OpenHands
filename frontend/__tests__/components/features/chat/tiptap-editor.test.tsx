import { render, screen, within } from "@testing-library/react";
import { TipTapEditor } from "#/components/features/chat/tiptap-editor";
import { describe, it, expect, vi } from "vitest";

// Add a custom query to find elements by attribute
screen.getByAttribute = (attribute: string, value: string) => {
  return document.querySelector(`[${attribute}="${value}"]`);
};

// Mock fetch for microagents
global.fetch = vi.fn().mockImplementation(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve([
      {
        name: "PR Update",
        trigger: "/pr_update",
        description: "Update a pull request",
      },
      {
        name: "PR Comment",
        trigger: "/pr_comment",
        description: "Comment on a pull request",
      },
    ]),
  })
);

describe("TipTapEditor", () => {
  it("renders the editor", () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();

    render(
      <TipTapEditor
        value=""
        onChange={onChange}
        onSubmit={onSubmit}
        placeholder="Test placeholder"
      />
    );

    // Check that the editor is rendered
    const editorElement = screen.getByAttribute("contenteditable", "true");
    expect(editorElement).toBeInTheDocument();
  });

  it("passes the correct props", () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    const onFocus = vi.fn();
    const onBlur = vi.fn();

    render(
      <TipTapEditor
        value="Test value"
        onChange={onChange}
        onSubmit={onSubmit}
        onFocus={onFocus}
        onBlur={onBlur}
        placeholder="Test placeholder"
        disabled={true}
        className="test-class"
      />
    );

    // Check that the editor has the correct class
    const editorElement = screen.getByAttribute("contenteditable", "true");
    expect(editorElement?.classList.contains("test-class")).toBeTruthy();
  });
});