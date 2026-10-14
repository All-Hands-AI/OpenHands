import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { MCPAppArtifacts, MCPAppHost, MCPAppScope } from "#/types/mcp-app";
import { MCPAppHostProvider, useMCPAppHost } from "./mcp-app-host-context";

const host: MCPAppHost = {
  sandboxUrl: "https://apps.example.com/sandbox.html",
  open: vi.fn(),
};

const scope: MCPAppScope = {
  backendId: "local-backend",
  orgId: null,
  connectionRevision: 1,
  conversationId: "conversation-main",
  planningConversationId: "conversation-plan",
  writableConversationId: "conversation-main",
};

// @spec MCA-004 — MCP app host access requires an explicit conversation scope
describe("MCPAppHostProvider", () => {
  it("defaults to no host and no scope outside a provider", () => {
    const { result } = renderHook(useMCPAppHost);

    expect(result.current).toEqual({
      host: null,
      scope: null,
      artifacts: new Map(),
    });
    expect(host.open).not.toHaveBeenCalled();
  });

  it("exposes the injected host and replaces the conversation scope when plan mode changes", () => {
    let currentScope = scope;
    const { result, rerender } = renderHook(useMCPAppHost, {
      wrapper: ({ children }) => (
        <MCPAppHostProvider host={host} scope={currentScope}>
          {children}
        </MCPAppHostProvider>
      ),
    });

    expect(result.current.host).toBe(host);
    expect(result.current.scope?.writableConversationId).toBe(
      "conversation-main",
    );

    currentScope = { ...scope, writableConversationId: "conversation-plan" };
    rerender();

    expect(result.current.scope?.writableConversationId).toBe(
      "conversation-plan",
    );
  });

  it("allows a nested read-only scope to block a shared view from inheriting a live host", () => {
    const sharedScope = {
      ...scope,
      writableConversationId: null,
      readOnly: true,
    };
    const { result } = renderHook(useMCPAppHost, {
      wrapper: ({ children }) => (
        <MCPAppHostProvider host={host} scope={scope}>
          <MCPAppHostProvider host={null} scope={sharedScope}>
            {children}
          </MCPAppHostProvider>
        </MCPAppHostProvider>
      ),
    });

    expect(result.current).toEqual({
      host: null,
      scope: sharedScope,
      artifacts: new Map(),
    });
  });

  it("replaces presentation data and prevents a nested provider from inheriting it", () => {
    const artifacts: MCPAppArtifacts = new Map([
      [
        "event-1",
        {
          tool: { name: "chart", _meta: { ui: { resourceUri: "ui://chart" } } },
          toolInput: {},
          toolResult: { content: [] },
        },
      ],
    ]);
    let shared = false;
    let currentArtifacts = artifacts;
    const { result, rerender } = renderHook(useMCPAppHost, {
      wrapper: ({ children }) => (
        <MCPAppHostProvider
          host={host}
          scope={scope}
          artifacts={currentArtifacts}
        >
          {shared ? (
            <MCPAppHostProvider host={null} scope={null}>
              {children}
            </MCPAppHostProvider>
          ) : (
            children
          )}
        </MCPAppHostProvider>
      ),
    });

    expect(result.current.artifacts).toBe(artifacts);
    currentArtifacts = new Map();
    rerender();
    expect(result.current.artifacts.size).toBe(0);

    currentArtifacts = artifacts;
    shared = true;
    rerender();
    expect(result.current.artifacts.size).toBe(0);
  });
});
