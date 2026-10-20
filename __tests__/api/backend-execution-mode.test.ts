import { describe, expect, it } from "vitest";

import {
  type AgentServerInfo,
  getBackendExecutionMode,
  getRequestedExecutionMode,
} from "#/api/agent-server-compatibility";

// @spec BM-005 — Display the active backend's execution mode
describe("getBackendExecutionMode", () => {
  it("reads the shipped conversation_runtime field", () => {
    // Arrange
    const serverInfo = {
      version: "1.50.0",
      conversation_runtime: "docker",
    } as AgentServerInfo;

    // Act / Assert
    expect(getBackendExecutionMode(serverInfo)).toBe("docker");
  });

  it("prefers execution_runtime when both fields are present", () => {
    // Arrange
    const serverInfo = {
      version: "1.50.0",
      execution_runtime: "local",
      conversation_runtime: "docker",
    } as AgentServerInfo;

    // Act / Assert
    expect(getBackendExecutionMode(serverInfo)).toBe("local");
  });

  it.each([null, undefined])(
    "returns null when the server info is %s",
    (serverInfo) => {
      // Act / Assert
      expect(getBackendExecutionMode(serverInfo)).toBeNull();
    },
  );

  it("returns null when the server omits the runtime field", () => {
    // Arrange
    const serverInfo = { version: "1.44.0" } as AgentServerInfo;

    // Act / Assert
    expect(getBackendExecutionMode(serverInfo)).toBeNull();
  });

  it("returns null for an unrecognized runtime value", () => {
    // Arrange
    const serverInfo = {
      version: "1.50.0",
      conversation_runtime: "podman",
    } as unknown as AgentServerInfo;

    // Act / Assert
    expect(getBackendExecutionMode(serverInfo)).toBeNull();
  });
});

// @spec BM-005 — Display the active backend's execution mode
describe("getRequestedExecutionMode", () => {
  it("returns docker only from the forward-looking execution_runtime field", () => {
    // Arrange: the shipped server reports the boundary as `conversation_runtime`,
    // which the Docker router rejects as a workspace kind (422), so it must not
    // drive the create request.
    const serverInfo = {
      version: "1.50.0",
      conversation_runtime: "docker",
    } as AgentServerInfo;

    // Act / Assert
    expect(getRequestedExecutionMode(serverInfo)).toBeNull();
  });

  it("requests docker when the server reports execution_runtime", () => {
    // Arrange
    const serverInfo = {
      version: "1.50.0",
      execution_runtime: "docker",
    } as AgentServerInfo;

    // Act / Assert
    expect(getRequestedExecutionMode(serverInfo)).toBe("docker");
  });

  it("prefers execution_runtime over conversation_runtime", () => {
    // Arrange
    const serverInfo = {
      version: "1.50.0",
      execution_runtime: "local",
      conversation_runtime: "docker",
    } as AgentServerInfo;

    // Act / Assert
    expect(getRequestedExecutionMode(serverInfo)).toBe("local");
  });

  it.each([null, undefined])(
    "returns null when the server info is %s",
    (serverInfo) => {
      // Act / Assert
      expect(getRequestedExecutionMode(serverInfo)).toBeNull();
    },
  );
});
