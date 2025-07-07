import { http, HttpResponse } from "msw";
import { OrganizationMember, OrganizationUserRole } from "#/types/org";

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

let orgMembers = new Map(
  INITIAL_MOCK_ORG_MEMBERS.map((member) => [member.id, member]),
);

export const resetOrgMembers = () => {
  orgMembers = new Map(
    INITIAL_MOCK_ORG_MEMBERS.map((member) => [member.id, member]),
  );
};

export const ORG_HANDLERS = [
  http.get("/api/users/me", () => HttpResponse.json(MOCK_ME)),

  http.get("/api/organizations/members", () => {
    const members = Array.from(orgMembers.values());
    return HttpResponse.json(members);
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

  http.post("/api/organizations/members", async ({ request }) => {
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
