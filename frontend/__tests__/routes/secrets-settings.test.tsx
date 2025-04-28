import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import SecretsSettingsScreen from "#/routes/secrets-settings";
import { SecretsService } from "#/api/secrets-service";

const renderSecretsSettings = () =>
  render(<SecretsSettingsScreen />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    ),
  });

describe("Content", () => {
  it("should render the secrets settings screen", () => {
    renderSecretsSettings();
    screen.getByTestId("secrets-settings-screen");
  });

  it("should render a message if there are no existing secrets", async () => {
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    getSecretsSpy.mockResolvedValue([]);
    renderSecretsSettings();

    await screen.findByTestId("no-secrets-message");
  });

  it("should render existing secrets", async () => {
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    getSecretsSpy.mockResolvedValue(["My_Secret_1", "My_Secret_2"]);
    renderSecretsSettings();

    const secrets = await screen.findAllByTestId("secret-item");
    expect(secrets).toHaveLength(2);
    expect(screen.queryByTestId("no-secrets-message")).not.toBeInTheDocument();
  });
});

describe("Secret actions", () => {
  it("should create a new secret", async () => {
    const createSecretSpy = vi.spyOn(SecretsService, "createSecret");
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    createSecretSpy.mockResolvedValue(true);
    renderSecretsSettings();

    // render form & hide items
    expect(screen.queryByTestId("add-secret-form")).not.toBeInTheDocument();
    const button = screen.getByTestId("add-secret-button");
    await userEvent.click(button);

    const secretForm = screen.getByTestId("add-secret-form");
    const secrets = screen.queryAllByTestId("secret-item");

    expect(screen.queryByTestId("add-secret-button")).not.toBeInTheDocument();
    expect(secretForm).toBeInTheDocument();
    expect(secrets).toHaveLength(0);

    // enter details
    const nameInput = within(secretForm).getByTestId("name-input");
    const valueInput = within(secretForm).getByTestId("value-input");
    const submitButton = within(secretForm).getByTestId("submit-button");

    vi.clearAllMocks(); // reset mocks to check for upcoming calls

    await userEvent.type(nameInput, "My_Custom_Secret");
    await userEvent.type(valueInput, "my-custom-secret-value");
    await userEvent.click(submitButton);

    // make POST request
    expect(createSecretSpy).toHaveBeenCalledWith(
      "My_Custom_Secret",
      "my-custom-secret-value",
    );

    // hide form & render items
    expect(screen.queryByTestId("add-secret-form")).not.toBeInTheDocument();
    expect(getSecretsSpy).toHaveBeenCalled();
  });

  it("should edit a secret", async () => {
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    const updateSecretSpy = vi.spyOn(SecretsService, "updateSecret");
    getSecretsSpy.mockResolvedValue(["My_Secret_1", "My_Secret_2"]);
    updateSecretSpy.mockResolvedValue(true);
    renderSecretsSettings();

    // render edit button within a secret list item
    const secrets = await screen.findAllByTestId("secret-item");
    const firstSecret = within(secrets[0]);
    const editButton = firstSecret.getByTestId("edit-secret-button");

    await userEvent.click(editButton);

    // render edit form
    const editForm = screen.getByTestId("edit-secret-form");

    expect(screen.queryByTestId("add-secret-button")).not.toBeInTheDocument();
    expect(editForm).toBeInTheDocument();
    expect(screen.queryAllByTestId("secret-item")).toHaveLength(0);

    // enter details
    const nameInput = within(editForm).getByTestId("name-input");
    const valueInput = within(editForm).getByTestId("value-input");
    const submitButton = within(editForm).getByTestId("submit-button");

    expect(nameInput).toHaveValue("My_Secret_1");

    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, "My_Edited_Secret");
    await userEvent.type(valueInput, "my-edited-secret-value");
    await userEvent.click(submitButton);

    // make POST request
    expect(updateSecretSpy).toHaveBeenCalledWith(
      "My_Secret_1",
      "My_Edited_Secret",
      "my-edited-secret-value",
    );

    // hide form
    expect(screen.queryByTestId("edit-secret-form")).not.toBeInTheDocument();

    // optimistic update
    const updatedSecrets = await screen.findAllByTestId("secret-item");
    expect(updatedSecrets).toHaveLength(2);
    expect(updatedSecrets[0]).toHaveTextContent(/my_edited_secret/i);
  });

  it("should be able to cancel the create or edit form", async () => {
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    getSecretsSpy.mockResolvedValue(["My_Secret_1", "My_Secret_2"]);
    renderSecretsSettings();

    // render form & hide items
    expect(screen.queryByTestId("add-secret-form")).not.toBeInTheDocument();
    const button = screen.getByTestId("add-secret-button");
    await userEvent.click(button);
    const secretForm = screen.getByTestId("add-secret-form");
    expect(secretForm).toBeInTheDocument();

    // cancel button
    const cancelButton = within(secretForm).getByTestId("cancel-button");
    await userEvent.click(cancelButton);
    expect(screen.queryByTestId("add-secret-form")).not.toBeInTheDocument();
    expect(screen.queryByTestId("add-secret-button")).toBeInTheDocument();

    // render edit button within a secret list item
    const secrets = await screen.findAllByTestId("secret-item");
    const firstSecret = within(secrets[0]);
    const editButton = firstSecret.getByTestId("edit-secret-button");
    await userEvent.click(editButton);

    // render edit form
    const editForm = screen.getByTestId("edit-secret-form");
    expect(editForm).toBeInTheDocument();
    expect(screen.queryAllByTestId("secret-item")).toHaveLength(0);

    // cancel button
    const cancelEditButton = within(editForm).getByTestId("cancel-button");
    await userEvent.click(cancelEditButton);
    expect(screen.queryByTestId("edit-secret-form")).not.toBeInTheDocument();
    expect(screen.queryAllByTestId("secret-item")).toHaveLength(2);
  });

  it("should undo the optimistic update if the request fails", async () => {
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    const updateSecretSpy = vi.spyOn(SecretsService, "updateSecret");
    getSecretsSpy.mockResolvedValue(["My_Secret_1", "My_Secret_2"]);
    updateSecretSpy.mockRejectedValue(new Error("Failed to update secret"));
    renderSecretsSettings();

    // render edit button within a secret list item
    const secrets = await screen.findAllByTestId("secret-item");
    const firstSecret = within(secrets[0]);
    const editButton = firstSecret.getByTestId("edit-secret-button");

    await userEvent.click(editButton);

    // render edit form
    const editForm = screen.getByTestId("edit-secret-form");

    expect(editForm).toBeInTheDocument();
    expect(screen.queryAllByTestId("secret-item")).toHaveLength(0);

    // enter details
    const nameInput = within(editForm).getByTestId("name-input");
    const valueInput = within(editForm).getByTestId("value-input");
    const submitButton = within(editForm).getByTestId("submit-button");

    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, "My_Edited_Secret");
    await userEvent.type(valueInput, "my-edited-secret-value");
    await userEvent.click(submitButton);

    // make POST request
    expect(updateSecretSpy).toHaveBeenCalledWith(
      "My_Secret_1",
      "My_Edited_Secret",
      "my-edited-secret-value",
    );

    // hide form
    expect(screen.queryByTestId("edit-secret-form")).not.toBeInTheDocument();

    // no optimistic update
    const updatedSecrets = await screen.findAllByTestId("secret-item");
    expect(updatedSecrets).toHaveLength(2);
    expect(updatedSecrets[0]).not.toHaveTextContent(/my edited secret/i);
  });

  it("should remove the secret from the list after deletion", async () => {
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    const deleteSecretSpy = vi.spyOn(SecretsService, "deleteSecret");
    getSecretsSpy.mockResolvedValue(["My_Secret_1", "My_Secret_2"]);
    deleteSecretSpy.mockResolvedValue(true);
    renderSecretsSettings();

    // render delete button within a secret list item
    const secrets = await screen.findAllByTestId("secret-item");
    const secondSecret = within(secrets[1]);
    const deleteButton = secondSecret.getByTestId("delete-secret-button");
    await userEvent.click(deleteButton);

    // confirmation modal
    const confirmationModal = screen.getByTestId("confirmation-modal");
    const confirmButton =
      within(confirmationModal).getByTestId("confirm-button");
    await userEvent.click(confirmButton);

    // make DELETE request
    expect(deleteSecretSpy).toHaveBeenCalledWith("My_Secret_2");
    expect(screen.queryByTestId("confirmation-modal")).not.toBeInTheDocument();

    // optimistic update
    expect(screen.queryAllByTestId("secret-item")).toHaveLength(1);
    expect(screen.queryByText("My_Secret_2")).not.toBeInTheDocument();
  });

  it("should revert the optimistic update if the request fails", async () => {
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    const deleteSecretSpy = vi.spyOn(SecretsService, "deleteSecret");
    getSecretsSpy.mockResolvedValue(["My_Secret_1", "My_Secret_2"]);
    deleteSecretSpy.mockRejectedValue(new Error("Failed to delete secret"));
    renderSecretsSettings();

    // render delete button within a secret list item
    const secrets = await screen.findAllByTestId("secret-item");
    const secondSecret = within(secrets[1]);
    const deleteButton = secondSecret.getByTestId("delete-secret-button");
    await userEvent.click(deleteButton);

    // confirmation modal
    const confirmationModal = screen.getByTestId("confirmation-modal");
    const confirmButton =
      within(confirmationModal).getByTestId("confirm-button");
    await userEvent.click(confirmButton);

    // make DELETE request
    expect(deleteSecretSpy).toHaveBeenCalledWith("My_Secret_2");
    expect(screen.queryByTestId("confirmation-modal")).not.toBeInTheDocument();

    // optimistic update
    expect(screen.queryAllByTestId("secret-item")).toHaveLength(2);
    expect(screen.queryByText("My_Secret_2")).toBeInTheDocument();
  });

  it("should hide the no items message when in form view", async () => {
    const getSecretsSpy = vi.spyOn(SecretsService, "getSecrets");
    getSecretsSpy.mockResolvedValue([]);
    renderSecretsSettings();

    // render form & hide items
    expect(screen.queryByTestId("no-secrets-message")).not.toBeInTheDocument();
    const button = screen.getByTestId("add-secret-button");
    await userEvent.click(button);

    const secretForm = screen.getByTestId("add-secret-form");
    expect(secretForm).toBeInTheDocument();
    expect(screen.queryByTestId("no-secrets-message")).not.toBeInTheDocument();
  });

  it("should not allow spaces in secret names", async () => {
    const createSecretSpy = vi.spyOn(SecretsService, "createSecret");
    renderSecretsSettings();

    // render form & hide items
    expect(screen.queryByTestId("add-secret-form")).not.toBeInTheDocument();
    const button = screen.getByTestId("add-secret-button");
    await userEvent.click(button);

    const secretForm = screen.getByTestId("add-secret-form");
    expect(secretForm).toBeInTheDocument();

    // enter details
    const nameInput = within(secretForm).getByTestId("name-input");
    const valueInput = within(secretForm).getByTestId("value-input");
    const submitButton = within(secretForm).getByTestId("submit-button");

    await userEvent.type(nameInput, "My Custom Secret With Spaces");
    await userEvent.type(valueInput, "my-custom-secret-value");
    await userEvent.click(submitButton);

    // make POST request
    expect(createSecretSpy).not.toHaveBeenCalled();

    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, "MyCustomSecret");
    await userEvent.click(submitButton);

    expect(createSecretSpy).toHaveBeenCalledWith(
      "MyCustomSecret",
      "my-custom-secret-value",
    );
  });
});
