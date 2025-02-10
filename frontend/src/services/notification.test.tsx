import { describe, it, expect, vi, beforeEach } from "vitest";
import { sendNotification } from "./notification";

describe("sendNotification", () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear();
    // Reset mocks
    vi.clearAllMocks();
    // Reset Notification mock
    vi.unstubAllGlobals();
  });

  it("should not send notification when notifications are disabled", async () => {
    const NotificationMock = vi.fn();
    NotificationMock.permission = "granted";
    NotificationMock.requestPermission = vi.fn().mockResolvedValue("granted");
    vi.stubGlobal("Notification", NotificationMock);

    localStorage.setItem("notifications-enabled", "false");
    await sendNotification("Test notification");

    expect(NotificationMock).not.toHaveBeenCalled();
  });

  it("should send notification when notifications are enabled and permission is granted", async () => {
    const NotificationMock = vi.fn();
    NotificationMock.permission = "granted";
    NotificationMock.requestPermission = vi.fn().mockResolvedValue("granted");
    vi.stubGlobal("Notification", NotificationMock);

    localStorage.setItem("notifications-enabled", "true");
    await sendNotification("Test notification");

    expect(NotificationMock).toHaveBeenCalledWith(
      "Test notification",
      undefined,
    );
  });

  it("should request permission when notifications are enabled but permission is not granted", async () => {
    const NotificationMock = vi.fn();
    NotificationMock.permission = "default";
    NotificationMock.requestPermission = vi.fn().mockResolvedValue("granted");
    vi.stubGlobal("Notification", NotificationMock);

    localStorage.setItem("notifications-enabled", "true");
    await sendNotification("Test notification");

    expect(NotificationMock.requestPermission).toHaveBeenCalled();
    expect(NotificationMock).toHaveBeenCalledWith(
      "Test notification",
      undefined,
    );
  });

  it("should not send notification when permission is denied", async () => {
    const NotificationMock = vi.fn();
    NotificationMock.permission = "denied";
    NotificationMock.requestPermission = vi.fn().mockResolvedValue("denied");
    vi.stubGlobal("Notification", NotificationMock);

    localStorage.setItem("notifications-enabled", "true");
    await sendNotification("Test notification");

    expect(NotificationMock).not.toHaveBeenCalled();
  });

  it("should not request permission when permission is denied", async () => {
    const NotificationMock = vi.fn();
    NotificationMock.permission = "denied";
    NotificationMock.requestPermission = vi.fn().mockResolvedValue("denied");
    vi.stubGlobal("Notification", NotificationMock);

    localStorage.setItem("notifications-enabled", "true");
    await sendNotification("Test notification");

    expect(NotificationMock.requestPermission).not.toHaveBeenCalled();
  });
});
