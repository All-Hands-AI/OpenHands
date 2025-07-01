import { http, HttpResponse } from "msw";
import { OrganizationMember } from "#/types/org";

export const MOCK_ORG_MEMBERS: OrganizationMember[] = [
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
    status: "invited",
  },
];

export const ORG_HANDLERS = [
  http.get("/api/organizations/members", () =>
    HttpResponse.json(MOCK_ORG_MEMBERS),
  ),

  http.post("/api/organizations/invite", async ({ request }) => {
    const { email } = (await request.json()) as { email: string };
    if (!email) {
      return HttpResponse.json({ error: "Email is required" }, { status: 400 });
    }

    const newMember: OrganizationMember = {
      id: String(MOCK_ORG_MEMBERS.length + 1),
      email,
      role: "user",
      status: "invited",
    };

    MOCK_ORG_MEMBERS.push(newMember);
    return HttpResponse.json(newMember, { status: 201 });
  }),
];
