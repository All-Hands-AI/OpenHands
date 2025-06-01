import { describe, expect, it } from "vitest";
import { FileService } from "#/api/file-service/file-service.api";
import {
  FILE_VARIANTS_1,
  FILE_VARIANTS_2,
} from "#/mocks/file-service-handlers";

/**
 * File service API tests. The actual API calls are mocked using MSW.
 * You can find the mock handlers in `frontend/src/mocks/file-service-handlers.ts`.
 */

describe("FileService", () => {
  it("should get a list of files", async () => {
    await expect(FileService.getFiles("test-conversation-id")).resolves.toEqual(
      FILE_VARIANTS_1,
    );

    await expect(
      FileService.getFiles("test-conversation-id-2"),
    ).resolves.toEqual(FILE_VARIANTS_2);
  });

  it("should get content of a file", async () => {
    await expect(
      FileService.getFile("test-conversation-id", "file1.txt"),
    ).resolves.toEqual("Content of file1.txt");
  });
});
