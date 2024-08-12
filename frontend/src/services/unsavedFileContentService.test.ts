import { describe, expect, it } from "vitest";
import { indexedDB } from "fake-indexeddb";
import {
  deleteAllUnsavedFileContent,
  deleteUnsavedFileContent,
  getUnsavedFileContent,
  listUnsavedFileNames,
  upsertUnsavedFileContent,
} from "./unsavedFileContentService";

describe("listUnsavedFileNames", () => {
  beforeAll(() => {
    globalThis.indexedDB = indexedDB;
  });
  afterEach(deleteAllUnsavedFileContent);
  it("Should list the names of files with unsaved content", async () => {
    const fileNames = await listUnsavedFileNames();
    expect(fileNames).toEqual([]);
  });
  it("Should add a file to the list of unsaved file names when unsaved content is persisted for it", async () => {
    await upsertUnsavedFileContent("some/file1.txt", "Some content");
    await upsertUnsavedFileContent("some/file2.txt", "More content");
    const fileNames = await listUnsavedFileNames();
    expect(fileNames).toEqual(["some/file1.txt", "some/file2.txt"]);
  });
  it("Should persist content for unsaved files", async () => {
    await upsertUnsavedFileContent("some/file3.txt", "Some content");
    await upsertUnsavedFileContent("some/file4.txt", "More content");
    const content3 = await getUnsavedFileContent("some/file3.txt");
    const content4 = await getUnsavedFileContent("some/file4.txt");
    expect(content3).toEqual("Some content");
    expect(content4).toEqual("More content");
  });
  it("Delete should remove content for unsaved files", async () => {
    await upsertUnsavedFileContent("some/file3.txt", "Some content");
    await upsertUnsavedFileContent("some/file4.txt", "More content");
    await deleteUnsavedFileContent("some/file3.txt");
    const content3 = await getUnsavedFileContent("some/file3.txt");
    const content4 = await getUnsavedFileContent("some/file4.txt");
    expect(content3).toBe(null);
    expect(content4).toEqual("More content");
  });
});
