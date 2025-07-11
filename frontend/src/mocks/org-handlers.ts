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

export const INITIAL_MOCK_ORG_MEMBERS: OrganizationMember[] = [
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
];

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
    name: "Gamma Inc",
    balance: 750,
  },
];

let orgMembers = new Map(
  INITIAL_MOCK_ORG_MEMBERS.map((member) => [member.id, member]),
);

const orgs = new Map(INITIAL_MOCK_ORGS.map((org) => [org.id, org]));

export const resetOrgMembers = () => {
  orgMembers = new Map(
    INITIAL_MOCK_ORG_MEMBERS.map((member) => [member.id, member]),
  );
};

export const ORG_HANDLERS = [
  http.get("/api/users/me", () => HttpResponse.json(MOCK_ME)),

  http.get("/api/organizations/:orgId/members", () => {
    const members = Array.from(orgMembers.values());
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

  http.post("/api/organizations/invite", async ({ request }) => {
    const { email } = (await request.json()) as { email: string };
    if (!email) {
      return HttpResponse.json({ error: "Email is required" }, { status: 400 });
    }

    const members = Array.from(orgMembers.values());
    const newMember: OrganizationMember = {
      id: String(members.length + 1),
      email,
      role: "user",
      status: "invited",
    };

    orgMembers.set(newMember.id, newMember);
    return HttpResponse.json(newMember, { status: 201 });
  }),

  http.post("/api/organizations/:orgId/members", async ({ request }) => {
    const { userId, role } = (await request.json()) as {
      userId: string;
      role: OrganizationUserRole;
    };

    const member = orgMembers.get(userId);
    if (!member) {
      return HttpResponse.json({ error: "Member not found" }, { status: 404 });
    }

    // replace
    const newMember: OrganizationMember = {
      ...member,
      role,
    };
    orgMembers.set(userId, newMember);

    return HttpResponse.json(member, { status: 200 });
  }),
];
