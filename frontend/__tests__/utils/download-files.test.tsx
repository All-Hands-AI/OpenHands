import { downloadFiles } from "../../src/utils/download-files";
import * as OpenHandsAPI from "../../src/api/open-hands";

jest.mock("../../src/api/open-hands");

describe("downloadFiles", () => {
  it("should not download node_modules", async () => {
    const mockGetFiles = OpenHandsAPI.OpenHands.getFiles as jest.Mock;
    mockGetFiles.mockResolvedValueOnce(["file1.txt", "node_modules/", "file2.txt"]);
    mockGetFiles.mockResolvedValueOnce(["file_in_node_modules.txt"]); // Should not be called due to exclusion
    mockGetFiles.mockResolvedValueOnce([]); // For file2.txt directory (not a directory in this test case)

    // Mock showDirectoryPicker and file system API
    const mockDirHandle = {
      getFileHandle: jest.fn().mockResolvedValue({
        createWritable: jest.fn().mockResolvedValue({
          write: jest.fn().mockResolvedValue(undefined),
          close: jest.fn().mockResolvedValue(undefined),
        }),
      }),
      getDirectoryHandle: jest.fn().mockResolvedValue({}),
    };
    global.window.showDirectoryPicker = jest.fn().mockResolvedValue(mockDirHandle);

    await downloadFiles("test-conversation-id");

    expect(mockGetFiles).toHaveBeenCalledTimes(2); // Should only call getFiles for root and file2.txt, not node_modules
    expect(mockGetFiles).toHaveBeenCalledWith("test-conversation-id", "");
    expect(mockGetFiles).not.toHaveBeenCalledWith("test-conversation-id", "node_modules/"); // Verify node_modules is skipped
  });
});