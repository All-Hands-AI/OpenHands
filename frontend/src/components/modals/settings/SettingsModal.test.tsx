import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
  saveSettings,
} from "#/services/settingsService";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { renderWithProviders } from "test-utils";
import { Mock } from "vitest";
import SettingsModal from "./SettingsModal";

vi.mock("../../services/settingsService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("#/services/settingsService")>()),
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
    renderWithProviders(<SettingsModal isOpen onOpenChange={vi.fn()} />);

    await waitFor(() => {
      expect(fetchModels).toHaveBeenCalledTimes(1);
      expect(fetchAgents).toHaveBeenCalledTimes(1);
    });
  });

  it.todo(
    "should display a loading spinner when fetching the models and agents",
  );

  it("should close the modal when the cancel button is clicked", async () => {
    const onOpenChange = vi.fn();
    await act(async () =>
      renderWithProviders(<SettingsModal isOpen onOpenChange={onOpenChange} />),
    );

    const cancelButton = screen.getByRole("button", {
      name: /MODAL_CLOSE_BUTTON_LABEL/i, // i18n key
    });

    act(() => {
      userEvent.click(cancelButton);
    });

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("should call saveSettings (and close) with the new values", async () => {
    const onOpenChangeMock = vi.fn();
    await act(async () =>
      renderWithProviders(
        <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
      ),
    );

    const saveButton = screen.getByRole("button", { name: /save/i });

    const modelInput = screen.getByRole("combobox", { name: "model" });

    act(() => {
      userEvent.click(modelInput);
    });

    const model3 = screen.getByText("model3");

    act(() => {
      userEvent.click(model3);
    });

    act(() => {
      userEvent.click(saveButton);
    });

    expect(saveSettings).toHaveBeenCalledWith({
      LLM_MODEL: "model3",
    });
    expect(onOpenChangeMock).toHaveBeenCalledWith(false);
  });

  // This test does not seem to rerender the component correctly
  // Therefore, we cannot test the reset of the state
  it.skip("should reset state when the cancel button is clicked", async () => {
    (getCurrentSettings as Mock).mockReturnValue({
      LLM_MODEL: "model1",
      AGENT: "agent1",
      LANGUAGE: "English",
    });

    const onOpenChange = vi.fn();
    const { rerender } = renderWithProviders(
      <SettingsModal isOpen onOpenChange={onOpenChange} />,
    );

    await waitFor(() => {
      expect(screen.getByRole("combobox", { name: "model" })).toHaveValue(
        "model1",
      );
    });

    const cancelButton = screen.getByRole("button", { name: /cancel/i });

    const modelInput = screen.getByRole("combobox", { name: "model" });
    act(() => {
      userEvent.click(modelInput);
    });

    const model3 = screen.getByText("model3");
    act(() => {
      userEvent.click(model3);
    });

    expect(modelInput).toHaveValue("model3");

    act(() => {
      userEvent.click(cancelButton);
    });

    rerender(<SettingsModal isOpen onOpenChange={onOpenChange} />);

    await waitFor(() => {
      expect(screen.getByRole("combobox", { name: "model" })).toHaveValue(
        "model1",
      );
    });
  });
});
