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

  test("No unlocalized strings should exist in frontend code", () => {
    const srcPath = path.resolve(__dirname, '../../src');
    
    // Get unlocalized strings using the AST scanner
    // The scanner now properly handles CSS classes using AST information
    const results = scanDirectoryForUnlocalizedStrings(srcPath);
    
    // If we found any unlocalized strings, format them for output
    if (results.size > 0) {
      const formattedResults = Array.from(results.entries())
        .map(([file, strings]) => `\n${file}:\n  ${strings.join('\n  ')}`)
        .join('\n');
      
      throw new Error(
        `Found unlocalized strings in the following files:${formattedResults}`
      );
    }
  });
});