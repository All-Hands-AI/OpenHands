import { renderHook } from "@testing-library/react";
import { useDocumentTitle } from "#/hooks/use-document-title";

describe("useDocumentTitle", () => {
  const originalTitle = document.title;

  afterEach(() => {
    // Reset the document title after each test
    document.title = originalTitle;
  });

  it("should set the document title with the provided title and default suffix", () => {
    renderHook(() => useDocumentTitle("Test Title"));
    expect(document.title).toBe("Test Title - OpenHands");
  });

  it("should set the document title with the provided title and custom suffix", () => {
    renderHook(() => useDocumentTitle("Test Title", "Custom Suffix"));
    expect(document.title).toBe("Test Title - Custom Suffix");
  });

  it("should set only the suffix when title is null", () => {
    renderHook(() => useDocumentTitle(null));
    expect(document.title).toBe("OpenHands");
  });

  it("should set only the suffix when title is undefined", () => {
    renderHook(() => useDocumentTitle(undefined));
    expect(document.title).toBe("OpenHands");
  });

  it("should set only the suffix when title is empty string", () => {
    renderHook(() => useDocumentTitle(""));
    expect(document.title).toBe("OpenHands");
  });

  it("should update the document title when the title changes", () => {
    const { rerender } = renderHook(({ title }) => useDocumentTitle(title), {
      initialProps: { title: "Initial Title" },
    });
    expect(document.title).toBe("Initial Title - OpenHands");

    rerender({ title: "Updated Title" });
    expect(document.title).toBe("Updated Title - OpenHands");
  });

  it("should reset the document title when the component unmounts", () => {
    const { unmount } = renderHook(() => useDocumentTitle("Test Title"));
    expect(document.title).toBe("Test Title - OpenHands");

    unmount();
    expect(document.title).toBe("OpenHands");
  });
});