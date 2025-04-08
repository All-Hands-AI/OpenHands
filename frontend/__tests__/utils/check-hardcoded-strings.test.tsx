import { render, screen } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { InteractiveChatBox } from "#/components/features/chat/interactive-chat-box";
import { ChatInput } from "#/components/features/chat/chat-input";
import path from 'path';
import { scanDirectoryForUnlocalizedStrings } from "#/utils/scan-unlocalized-strings-ast";

// Mock react-i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("Check for hardcoded English strings", () => {
  test("InteractiveChatBox should not have hardcoded English strings", () => {
    const { container } = render(
      <InteractiveChatBox
        onSubmit={() => {}}
        onStop={() => {}}
      />
    );

    // Get all text content
    const text = container.textContent;

    // List of English strings that should be translated
    const hardcodedStrings = [
      "What do you want to build?",
    ];

    // Check each string
    hardcodedStrings.forEach(str => {
      expect(text).not.toContain(str);
    });
  });

  test("ChatInput should use translation key for placeholder", () => {
    render(<ChatInput onSubmit={() => {}} />);
    screen.getByPlaceholderText("SUGGESTIONS$WHAT_TO_BUILD");
  });

  // Test "No unlocalized strings should exist in frontend code" has been moved to a pre-commit hook
  // See /frontend/scripts/check-unlocalized-strings.cjs
});