import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SettingsService from "#/api/settings-service/settings-service.api";
import SettingsDocumentRoute from "#/routes/settings-document";

vi.mock("#/hooks/query/use-is-authed", () => ({
  useIsAuthed: () => ({ data: true }),
}));

vi.mock("#/contexts/active-backend-context", () => ({
  useActiveBackend: () => ({
    backend: { id: "local", kind: "local", host: "http://localhost:3000" },
    orgId: null,
  }),
}));

vi.mock("#/api/backend-registry/active-store", () => ({
  isNoBackend: () => false,
}));

const booleanField = (key: string, label: string, section: string) => ({
  key,
  label,
  section,
  section_label: label,
  value_type: "boolean" as const,
  default: false,
  choices: [],
  depends_on: [],
  prominence: "major" as const,
  secret: false,
});

const document = {
  schema_version: 1 as const,
  agent: {},
  conversation: {},
  product: { ice_cream_flavor: true },
  resources: {
    llm_profiles: {},
    agent_profiles: {},
    provider_connections: {},
    model_routers: {},
    marketplaces: [],
    credentials: {},
    pointers: {},
  },
};

const schema = {
  model_name: "SettingsDocument",
  sections: [
    {
      key: "agent.general",
      label: "General",
      fields: [booleanField("agent.enabled", "Agent enabled", "agent.general")],
    },
    { key: "resources", label: "Resources", fields: [] },
    {
      key: "product.prototype",
      label: "Prototype settings",
      fields: [
        booleanField(
          "product.ice_cream_flavor",
          "Ice cream flavor",
          "product.prototype",
        ),
      ],
    },
  ],
};

const renderRoute = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const RouterStub = createRoutesStub([
    {
      path: "/settings/document/:sectionKey",
      Component: SettingsDocumentRoute,
    },
  ]);

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterStub initialEntries={["/settings/document/product.prototype"]} />
    </QueryClientProvider>,
  );
};

describe("SettingsDocumentRoute", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(SettingsService, "getSettingsDocument").mockResolvedValue(
      document,
    );
    vi.spyOn(SettingsService, "getSettingsDocumentSchema").mockResolvedValue(
      schema,
    );
  });

  it("renders only the schema section selected by the route", async () => {
    renderRoute();

    expect(
      await screen.findByTestId("sdk-settings-product.ice_cream_flavor"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("sdk-settings-agent.enabled"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Settings" }),
    ).not.toBeInTheDocument();
  });
});
