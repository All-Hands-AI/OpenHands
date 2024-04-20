import { waitFor, screen, act, render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import {
  fetchModels,
  fetchAgents,
  saveSettings,
} from "../../services/settingsService";
import SettingsModal from "./SettingsModal";

vi.mock("../../services/settingsService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../services/settingsService")>()),
  getCurrentSettings: vi.fn().mockReturnValue({}),
  saveSettings: vi.fn(),
  fetchModels: vi
    .fn()
    .mockResolvedValue(Promise.resolve(["model1", "model2", "model3"])),
  fetchAgents: vi
    .fn()
    .mockResolvedValue(Promise.resolve(["agent1", "agent2", "agent3"])),
}));

describe("SettingsModal", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch existing agents and models from the API", async () => {
    render(<SettingsModal isOpen onOpenChange={vi.fn()} />);

    await waitFor(() => {
      expect(fetchModels).toHaveBeenCalledTimes(1);
      expect(fetchAgents).toHaveBeenCalledTimes(1);
    });
  });

  it("should close the modal when the cancel button is clicked", async () => {
    const onOpenChange = vi.fn();
    await act(async () =>
      render(<SettingsModal isOpen onOpenChange={onOpenChange} />),
    );

    const cancelButton = screen.getByRole("button", { name: /cancel/i });

    act(() => {
      userEvent.click(cancelButton);
    });

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it.todo("should reset state when the cancel button is clicked");

  it("should call saveSettings (and close) with the new values", async () => {
    const onOpenChangeMock = vi.fn();
    await act(async () =>
      render(<SettingsModal isOpen onOpenChange={onOpenChangeMock} />),
    );

    // due to the way the custom combobox is setup with nextui, the save button after selecting a value is "covered" by the dropdown
    // so we are directly checking that saveSettings executes, without testing the actual selection of values

    const saveButton = screen.getByRole("button", { name: /save/i });

    act(() => {
      userEvent.click(saveButton);
    });

    expect(saveSettings).toHaveBeenCalledWith({});
    expect(onOpenChangeMock).toHaveBeenCalledWith(false);
  });
});
