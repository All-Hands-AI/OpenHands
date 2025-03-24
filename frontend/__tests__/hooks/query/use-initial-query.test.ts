import { useInitialQuery } from "#/hooks/query/use-initial-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

// Mock the query-redux-bridge
vi.mock("#/utils/query-redux-bridge", () => ({
  getQueryReduxBridge: vi.fn(),
}));

describe("useInitialQuery", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should initialize with default state when Redux bridge is not available", () => {
    // Mock the bridge to throw an error
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockImplementation(() => {
      throw new Error("Bridge not initialized");
    });

    const { result } = renderHook(() => useInitialQuery());

    expect(result.current.files).toEqual([]);
    expect(result.current.initialPrompt).toBe(null);
    expect(result.current.selectedRepository).toBe(null);
    expect(result.current.isLoading).toBe(false);
  });

  it("should initialize with Redux state when available", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        files: ["file1", "file2"],
        initialPrompt: "Test prompt",
        selectedRepository: "test/repo",
      }),
    });

    const { result } = renderHook(() => useInitialQuery());

    expect(result.current.files).toEqual(["file1", "file2"]);
    expect(result.current.initialPrompt).toBe("Test prompt");
    expect(result.current.selectedRepository).toBe("test/repo");
  });

  it("should add a file when addFile is called", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        files: [],
        initialPrompt: null,
        selectedRepository: null,
      }),
    });

    const { result } = renderHook(() => useInitialQuery());

    // Initial state
    expect(result.current.files).toEqual([]);

    // Add a file
    act(() => {
      result.current.addFile("newfile");
    });

    // Check updated state
    expect(result.current.files).toEqual(["newfile"]);
  });

  it("should remove a file when removeFile is called", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        files: ["file1", "file2", "file3"],
        initialPrompt: null,
        selectedRepository: null,
      }),
    });

    const { result } = renderHook(() => useInitialQuery());

    // Initial state
    expect(result.current.files).toEqual(["file1", "file2", "file3"]);

    // Remove a file
    act(() => {
      result.current.removeFile(1);
    });

    // Check updated state
    expect(result.current.files).toEqual(["file1", "file3"]);
  });

  it("should clear files when clearFiles is called", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        files: ["file1", "file2", "file3"],
        initialPrompt: null,
        selectedRepository: null,
      }),
    });

    const { result } = renderHook(() => useInitialQuery());

    // Initial state
    expect(result.current.files).toEqual(["file1", "file2", "file3"]);

    // Clear files
    act(() => {
      result.current.clearFiles();
    });

    // Check updated state
    expect(result.current.files).toEqual([]);
  });

  it("should set initial prompt when setInitialPrompt is called", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        files: [],
        initialPrompt: null,
        selectedRepository: null,
      }),
    });

    const { result } = renderHook(() => useInitialQuery());

    // Initial state
    expect(result.current.initialPrompt).toBe(null);

    // Set initial prompt
    act(() => {
      result.current.setInitialPrompt("New prompt");
    });

    // Check updated state
    expect(result.current.initialPrompt).toBe("New prompt");
  });

  it("should set selected repository when setSelectedRepository is called", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        files: [],
        initialPrompt: null,
        selectedRepository: null,
      }),
    });

    const { result } = renderHook(() => useInitialQuery());

    // Initial state
    expect(result.current.selectedRepository).toBe(null);

    // Set selected repository
    act(() => {
      result.current.setSelectedRepository("new/repo");
    });

    // Check updated state
    expect(result.current.selectedRepository).toBe("new/repo");
  });
});
