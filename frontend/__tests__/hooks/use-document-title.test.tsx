import { renderHook } from "@testing-library/react";
import { useDocumentTitle } from "#/hooks/use-document-title";

// Define the type for our test props
type TitleProps = {
  title?: string | null;
};

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

  it("should set only the suffix when title is null and no previous title exists", () => {
    renderHook(() => useDocumentTitle(null));
    expect(document.title).toBe("OpenHands");
  });

  it("should set only the suffix when title is undefined and no previous title exists", () => {
    renderHook(() => useDocumentTitle(undefined));
    expect(document.title).toBe("OpenHands");
  });

  it("should set only the suffix when title is empty string and no previous title exists", () => {
    renderHook(() => useDocumentTitle(""));
    expect(document.title).toBe("OpenHands");
  });

  it("should update the document title when the title changes", () => {
    const { rerender } = renderHook(({ title }: TitleProps) => useDocumentTitle(title), {
      initialProps: { title: "Initial Title" },
    });
    expect(document.title).toBe("Initial Title - OpenHands");

    rerender({ title: "Updated Title" });
    expect(document.title).toBe("Updated Title - OpenHands");
  });

  it("should maintain the last valid title when a null title is provided", () => {
    const { rerender } = renderHook(({ title }: TitleProps) => useDocumentTitle(title), {
      initialProps: { title: "Valid Title" },
    });
    expect(document.title).toBe("Valid Title - OpenHands");

    // When title becomes null, it should keep the last valid title
    rerender({ title: null });
    expect(document.title).toBe("Valid Title - OpenHands");

    // When a new valid title is provided, it should update
    rerender({ title: "New Valid Title" });
    expect(document.title).toBe("New Valid Title - OpenHands");
  });

  it("should maintain the last valid title when an empty title is provided", () => {
    const { rerender } = renderHook(({ title }: TitleProps) => useDocumentTitle(title), {
      initialProps: { title: "Valid Title" },
    });
    expect(document.title).toBe("Valid Title - OpenHands");

    // When title becomes empty, it should keep the last valid title
    rerender({ title: "" });
    expect(document.title).toBe("Valid Title - OpenHands");
  });

  it("should reset the document title when the component unmounts", () => {
    const { unmount } = renderHook(() => useDocumentTitle("Test Title"));
    expect(document.title).toBe("Test Title - OpenHands");

    unmount();
    expect(document.title).toBe("OpenHands");
  });
});