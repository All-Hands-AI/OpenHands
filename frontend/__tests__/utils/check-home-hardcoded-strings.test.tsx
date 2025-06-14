import { render } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { HomeHeader } from "#/components/features/home/home-header";

// Mock dependencies
vi.mock("#/hooks/mutation/use-create-conversation", () => ({
  useCreateConversation: () => ({
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
  }),
}));

vi.mock("#/hooks/use-is-creating-conversation", () => ({
  useIsCreatingConversation: () => false,
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("Check for hardcoded English strings in Home components", () => {
  test("HomeHeader should not have hardcoded English strings", () => {
    const { container } = render(<HomeHeader />);

    // Get all text content
    const text = container.textContent;

    // List of English strings that should be translated
    const hardcodedStrings = [
      "Launch from Scratch",
      "Read this",
    ];

    // Check each string
    hardcodedStrings.forEach((str) => {
      expect(text).not.toContain(str);
    });
  });
});
