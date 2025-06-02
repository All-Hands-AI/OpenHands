import { render, screen } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { InteractiveChatBox } from "#/components/features/chat/interactive-chat-box";
import { ChatInput } from "#/components/features/chat/chat-input";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("Check for hardcoded English strings", () => {
  test("InteractiveChatBox should not have hardcoded English strings", () => {
    const { container } = render(
      <InteractiveChatBox onSubmit={() => {}} onStop={() => {}} />,
    );

    // Get all text content
    const text = container.textContent;

    // List of English strings that should be translated
    const hardcodedStrings = [
      "What do you want to build?",
      "Launch from Scratch",
      "Read this"
    ];

    // Check each string
    hardcodedStrings.forEach((str) => {
      expect(text).not.toContain(str);
    });
  });

  test("ChatInput should use translation key for placeholder", () => {
    render(<ChatInput onSubmit={() => {}} />);
    screen.getByPlaceholderText("SUGGESTIONS$WHAT_TO_BUILD");
  });
});
