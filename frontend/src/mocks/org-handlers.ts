import { http, HttpResponse } from "msw";
import {
  Organization,
  OrganizationMember,
  OrganizationUserRole,
} from "#/types/org";

const MOCK_ME: OrganizationMember = {
  id: "99",
  email: "me@acme.org",
  role: "admin",
  status: "active",
};

export const INITIAL_MOCK_ORGS: Organization[] = [
  {
    id: "1",
    name: "Acme Corp",
    balance: 1000,
  },
  {
    id: "2",
    name: "Beta LLC",
    balance: 500,
  },
  {
    id: "3",
    name: "All Hands AI",
    balance: 750,
  },
];

export const ORGS_AND_MEMBERS: Record<string, OrganizationMember[]> = {
  "1": [
    {
      id: "1",
      email: "alice@acme.org",
      role: "superadmin",
      status: "active",
    },
    {
      id: "2",
      email: "bob@acme.org",
      role: "admin",
      status: "active",
    },
    {
      id: "3",
      email: "charlie@acme.org",
      role: "user",
      status: "active",
    },
  ],
  "2": [
    {
      id: "4",
      email: "tony@gamma.org",
      role: "user",
      status: "active",
    },
    {
      id: "5",
      email: "evan@gamma.org",
      role: "admin",
      status: "active",
    },
  ],
  "3": [
    {
      id: "6",
      email: "robert@all-hands.dev",
      role: "superadmin",
      status: "active",
    },
    {
      id: "7",
      email: "ray@all-hands.dev",
      role: "admin",
      status: "active",
    },
    {
      id: "8",
      email: "chuck@all-hands.dev",
      role: "user",
      status: "active",
    },
    {
      id: "9",
      email: "stephan@all-hands.dev",
      role: "user",
      status: "active",
    },
    {
      id: "10",
      email: "tim@all-hands.dev",
      role: "user",
      status: "invited",
    },
  ],
};

const orgs = new Map(INITIAL_MOCK_ORGS.map((org) => [org.id, org]));

export const ORG_HANDLERS = [
  http.get("/api/users/me", () => HttpResponse.json(MOCK_ME)),

  http.get("/api/organizations/:orgId/members", ({ params }) => {
    const orgId = params.orgId?.toString();
    if (!orgId || !ORGS_AND_MEMBERS[orgId]) {
      return HttpResponse.json(
        { error: "Organization not found" },
        { status: 404 },
      );
    }
    const members = ORGS_AND_MEMBERS[orgId];
    return HttpResponse.json(members);
  }),

  http.get("/api/organizations", () => {
    const organizations = Array.from(orgs.values());
    return HttpResponse.json(organizations);
  }),

  http.patch("/api/organizations/:orgId", async ({ request, params }) => {
    const { name } = (await request.json()) as {
      name: string;
    };
    const orgId = params.orgId?.toString();

    if (!name) {
      return HttpResponse.json({ error: "Name is required" }, { status: 400 });
    }

    if (!orgId) {
      return HttpResponse.json(
        { error: "Organization ID is required" },
        { status: 400 },
      );
    }

    const existingOrg = orgs.get(orgId);
    if (!existingOrg) {
      return HttpResponse.json(
        { error: "Organization not found" },
        { status: 404 },
      );
    }

    const updatedOrg: Organization = {
      ...existingOrg,
      name,
    };
    orgs.set(orgId, updatedOrg);

    return HttpResponse.json(updatedOrg, { status: 201 });
  }),

  http.get("/api/organizations/:orgId", ({ params }) => {
    const orgId = params.orgId?.toString();

    if (orgId) {
      const org = orgs.get(orgId);
      if (org) return HttpResponse.json(org);
    }

    return HttpResponse.json(
      { error: "Organization not found" },
      { status: 404 },
    );
  }),

  http.get("/api/organizations/:orgId/payment", ({ params }) => {
    const orgId = params.orgId?.toString();

    if (orgId) {
      const org = orgs.get(orgId);
      if (org) {
        return HttpResponse.json({
          cardNumber: "**** **** **** 1234", // Mocked payment info
        });
      }
    }

    return HttpResponse.json(
      { error: "Organization not found" },
      { status: 404 },
    );
  }),

  http.post("/api/organizations/:orgId/invite", async ({ request, params }) => {
    const { email } = (await request.json()) as { email: string };
    const orgId = params.orgId?.toString();

    if (!email) {
      return HttpResponse.json({ error: "Email is required" }, { status: 400 });
    }

    if (!orgId || !ORGS_AND_MEMBERS[orgId]) {
      return HttpResponse.json(
        { error: "Organization not found" },
        { status: 404 },
      );
    }

    const members = Array.from(ORGS_AND_MEMBERS[orgId]);
    const newMember: OrganizationMember = {
      id: String(members.length + 1),
      email,
      role: "user",
      status: "invited",
    };

    const newMembers = [...members, newMember];
    ORGS_AND_MEMBERS[orgId] = newMembers;

    return HttpResponse.json(newMember, { status: 201 });
  }),

  http.patch(
    "/api/organizations/:orgId/members",
    async ({ request, params }) => {
      const { userId, role } = (await request.json()) as {
        userId: string;
        role: OrganizationUserRole;
      };
      const orgId = params.orgId?.toString();

      if (!orgId || !ORGS_AND_MEMBERS[orgId]) {
        return HttpResponse.json(
          { error: "Organization not found" },
          { status: 404 },
        );
      }

      const member = ORGS_AND_MEMBERS[orgId].find((m) => m.id === userId);
      if (!member) {
        return HttpResponse.json(
          { error: "Member not found" },
          { status: 404 },
        );
      }

      // replace
      const newMember: OrganizationMember = {
        ...member,
        role,
      };
      const newMembers = ORGS_AND_MEMBERS[orgId].map((m) =>
        m.id === userId ? newMember : m,
      );
      ORGS_AND_MEMBERS[orgId] = newMembers;

      return HttpResponse.json(member, { status: 200 });
    },
  ),
];
