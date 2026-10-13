import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SecretsService } from "#/api/secrets-service";
import { SecretRequestModal } from "#/components/features/conversation/secret-request-modal";
import {
  type SecretRequest,
  useSecretRequestStore,
} from "#/stores/secret-request-store";
import { renderWithProviders } from "../../../../test-utils";

const { mockCompleteSecretRequest } = vi.hoisted(() => ({
  mockCompleteSecretRequest: vi.fn(),
}));

vi.mock("#/services/secret-request", () => ({
  completeSecretRequest: mockCompleteSecretRequest,
}));

// renderWithProviders navigates to this conversation by default.
const request: SecretRequest = {
  conversationId: "test-conversation-id",
  toolCallId: "tool-call-1",
  name: "GITHUB_TOKEN",
  reason: "Push the factory branch; needs repo scope.",
};

const renderModal = async (requests: SecretRequest[] = [request]) => {
  useSecretRequestStore.setState({ requests });
  renderWithProviders(<SecretRequestModal />);
  if (requests.some((r) => r.conversationId === request.conversationId)) {
    await screen.findByTestId("secret-request-modal");
  }
};

describe("SecretRequestModal", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockCompleteSecretRequest.mockReset();
    vi.spyOn(SecretsService, "getSecrets").mockResolvedValue([]);
  });

  it("asks for the requested secret with the agent's reason", async () => {
    await renderModal();

    expect(screen.getByText(request.reason!)).toBeInTheDocument();
    expect(screen.getByTestId("name-input")).toHaveValue("GITHUB_TOKEN");
    expect(screen.getByTestId("value-input")).toHaveValue("");
  });

  it("ignores requests from other conversations", async () => {
    await renderModal([{ ...request, conversationId: "other-conversation" }]);

    await waitFor(() => expect(SecretsService.getSecrets).toHaveBeenCalled());
    expect(
      screen.queryByTestId("secret-request-modal"),
    ).not.toBeInTheDocument();
  });

  it("saves the value to the secrets store and completes with the secret's identity", async () => {
    const user = userEvent.setup();
    const createSecret = vi
      .spyOn(SecretsService, "createSecret")
      .mockResolvedValue(undefined);
    await renderModal();

    await user.type(screen.getByTestId("value-input"), "ghp_example");
    await user.click(screen.getByTestId("submit-button"));

    await waitFor(() =>
      expect(mockCompleteSecretRequest).toHaveBeenCalledExactlyOnceWith(
        request,
        { name: "GITHUB_TOKEN", description: undefined },
      ),
    );
    expect(createSecret).toHaveBeenCalledWith(
      "GITHUB_TOKEN",
      "ghp_example",
      undefined,
    );
  });

  it("completes without a secret when the user cancels or the save fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(SecretsService, "createSecret").mockRejectedValue(
      new Error("Save failed"),
    );
    await renderModal();

    await user.type(screen.getByTestId("value-input"), "ghp_example");
    await user.click(screen.getByTestId("submit-button"));

    await waitFor(() =>
      expect(mockCompleteSecretRequest).toHaveBeenCalledExactlyOnceWith(
        request,
        null,
      ),
    );

    await user.click(screen.getByTestId("cancel-button"));

    expect(mockCompleteSecretRequest).toHaveBeenLastCalledWith(request, null);
  });

  it("edits an existing secret of the same name instead of duplicating it", async () => {
    vi.spyOn(SecretsService, "getSecrets").mockResolvedValue([
      { name: "GITHUB_TOKEN", description: "Old token" },
    ]);

    await renderModal();

    expect(screen.getByTestId("edit-secret-form")).toBeInTheDocument();
    expect(screen.getByTestId("name-input")).toHaveValue("GITHUB_TOKEN");
  });
});
