import { render, screen } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { InteractiveChatBox } from "#/components/features/chat/interactive-chat-box";
import { ChatInput } from "#/components/features/chat/chat-input";
import path from 'path';
import { scanDirectoryForUnlocalizedStrings } from "#/utils/scan-unlocalized-strings";

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
    const results = scanDirectoryForUnlocalizedStrings(srcPath);
    
    // Filter out CSS classes and styling strings
    const filteredResults = new Map();
    
    for (const [file, strings] of results.entries()) {
      // Only include files with actual English text strings (not CSS/styling)
      const actualTextStrings = strings.filter(str => {
        // Skip CSS classes, styling, and other non-user-facing strings
        const isCssClass = /^[a-zA-Z0-9-]+(\s+[a-zA-Z0-9-]+)*$/.test(str) || 
                          str.includes('px') || 
                          str.includes('rem') || 
                          str.includes('em') || 
                          str.includes('#') ||
                          str.includes('border') ||
                          str.includes('rounded') ||
                          str.includes('flex') ||
                          str.includes('transition') ||
                          str.includes('duration') ||
                          str.includes('ease') ||
                          str.includes('hover:') ||
                          str.includes('focus:') ||
                          str.includes('active:') ||
                          str.includes('disabled:') ||
                          str.includes('placeholder:') ||
                          str.includes('text-') ||
                          str.includes('bg-') ||
                          str.includes('w-') ||
                          str.includes('h-') ||
                          str.includes('p-') ||
                          str.includes('m-') ||
                          str.includes('gap-') ||
                          str.includes('items-') ||
                          str.includes('justify-') ||
                          str.includes('self-') ||
                          str.includes('overflow-') ||
                          str.includes('cursor-') ||
                          str.includes('opacity-') ||
                          str.includes('z-') ||
                          str.includes('top-') ||
                          str.includes('right-') ||
                          str.includes('bottom-') ||
                          str.includes('left-') ||
                          str.includes('inset-') ||
                          str.includes('font-') ||
                          str.includes('tracking-') ||
                          str.includes('leading-') ||
                          str.includes('whitespace-') ||
                          str.includes('break-') ||
                          str.includes('truncate') ||
                          str.includes('shadow-') ||
                          str.includes('ring-') ||
                          str.includes('outline-') ||
                          str.includes('animate-') ||
                          str.includes('transform') ||
                          str.includes('rotate-') ||
                          str.includes('scale-') ||
                          str.includes('skew-') ||
                          str.includes('translate-') ||
                          str.includes('origin-');
        
        return !isCssClass;
      });
      
      if (actualTextStrings.length > 0) {
        filteredResults.set(file, actualTextStrings);
      }
    }
    
    // If we found any unlocalized strings, format them for output
    if (filteredResults.size > 0) {
      const formattedResults = Array.from(filteredResults.entries())
        .map(([file, strings]) => `\n${file}:\n  ${strings.join('\n  ')}`)
        .join('\n');
      
      throw new Error(
        `Found unlocalized strings in the following files:${formattedResults}`
      );
    }
  });
});
