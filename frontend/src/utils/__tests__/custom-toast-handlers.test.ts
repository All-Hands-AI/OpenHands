import { describe, it, expect, vi, beforeEach } from "vitest";
import { toasterMessages } from "@openhands/ui";
import {
  displaySuccessToast,
  displayErrorToast,
  displayWarningToast,
  displayInfoToast,
} from "../custom-toast-handlers";

// Mock react-hot-toast
vi.mock("@openhands/ui", () => ({
  toasterMessages: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}));

describe("custom-toast-handlers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("displaySuccessToast", () => {
    it("should call toasterMessages.success", () => {
      const shortMessage = "Settings saved";
      displaySuccessToast(shortMessage);

      expect(toasterMessages.success).toHaveBeenCalledWith(
        shortMessage,
        expect.objectContaining({
          duration: 5_000,
          position: "top-right",
        }),
      );
    });
  });
  describe("displayInfoToast", () => {
    it("should call toasterMessages.info", () => {
      const shortMessage = "Settings saved";
      displayInfoToast(shortMessage);

      expect(toasterMessages.info).toHaveBeenCalledWith(
        shortMessage,
        expect.objectContaining({
          duration: 4_000,
          position: "top-right",
        }),
      );
    });
  });
  describe("displayWarningToast", () => {
    it("should call toasterMessages.warning", () => {
      const shortMessage = "Settings saved";
      displayWarningToast(shortMessage);

      expect(toasterMessages.warning).toHaveBeenCalledWith(
        shortMessage,
        expect.objectContaining({
          duration: 4_000,
          position: "top-right",
        }),
      );
    });
  });
  describe("displayErrorToast", () => {
    it("should call toasterMessages.error", () => {
      const shortMessage = "Settings saved";
      displayErrorToast(shortMessage);

      expect(toasterMessages.error).toHaveBeenCalledWith(
        shortMessage,
        expect.objectContaining({
          duration: 5_000,
          position: "top-right",
        }),
      );
    });
  });
});
