import { describe, expect, it, vi } from "vitest";
import { cmdClickAndExpectNewTab } from "../../tests/e2e/mock-llm/utils/cmd-click-new-tab";

describe("cmdClickAndExpectNewTab", () => {
  it.each([false, true])(
    "records final defaultPrevented when propagation is stopped: %s",
    async (stopPropagation) => {
      const anchor = document.createElement("a");
      anchor.href = "/conversations/123";
      anchor.dataset.testid = "conversation-card";
      document.body.append(anchor);
      anchor.addEventListener("click", (event) => {
        event.preventDefault();
        if (stopPropagation) event.stopPropagation();
      });
      // Only the Playwright transport is substituted; evaluate runs the real listener.
      const page = { evaluate: async (callback: () => unknown) => callback() };
      let rejectTabWait: (error: Error) => void;
      const card = {
        page: () => page,
        click: async () => {
          anchor.dispatchEvent(
            new MouseEvent("click", {
              bubbles: true,
              cancelable: true,
              ctrlKey: true,
            }),
          );
          setTimeout(() => rejectTabWait(new Error("Timeout exceeded")), 0);
        },
      };
      const context = {
        waitForEvent: () =>
          new Promise((_, reject) => {
            rejectTabWait = reject;
          }),
      };
      try {
        await expect(
          cmdClickAndExpectNewTab(context as any, card as any, { timeout: 30 }),
        ).rejects.toThrow(/"defaultPrevented":true/);
      } finally {
        anchor.remove();
      }
    },
  );
  it("resolves the newly opened tab when waitForEvent succeeds", async () => {
    const mockPage = {
      evaluate: vi.fn().mockResolvedValue(null),
    };
    const mockCard = {
      page: vi.fn().mockReturnValue(mockPage),
      click: vi.fn().mockResolvedValue(undefined),
    };
    const mockNewTab = { url: () => "https://example.com/conversation" };
    const mockContext = {
      waitForEvent: vi.fn().mockResolvedValue(mockNewTab),
    };

    const result = await cmdClickAndExpectNewTab(
      mockContext as any,
      mockCard as any,
      {
        timeout: 5000,
      },
    );

    expect(result).toBe(mockNewTab);
    expect(mockCard.click).toHaveBeenCalledWith({
      modifiers: ["ControlOrMeta"],
    });
    expect(mockContext.waitForEvent).toHaveBeenCalledWith("page", {
      timeout: 5000,
    });
  });

  it("fails fast with recorded click diagnostics when no tab opens within timeout", async () => {
    const diagnostics = {
      targetTag: "A",
      targetTestId: "conversation-card",
      anchorHref: "/conversations/123?backend=b1",
      ctrlKey: true,
      metaKey: false,
      defaultPrevented: false,
    };
    const mockPage = {
      evaluate: vi
        .fn()
        .mockResolvedValueOnce(undefined) // setup click listener
        .mockResolvedValueOnce(diagnostics), // read diagnostics on error
    };
    const mockCard = {
      page: vi.fn().mockReturnValue(mockPage),
      click: vi.fn().mockResolvedValue(undefined),
    };
    const mockContext = {
      waitForEvent: vi
        .fn()
        .mockRejectedValue(new Error("Timeout 5000ms exceeded")),
    };

    await expect(
      cmdClickAndExpectNewTab(mockContext as any, mockCard as any, {
        timeout: 5000,
      }),
    ).rejects.toThrowError(
      /cmd-click opened no new tab within 5000ms\. Recorded click diagnostics: .*conversation-card/,
    );
  });
});
