export type OrganizationUserRole = "user" | "admin" | "superadmin";

export interface OrganizationMember {
  id: string;
  email: string;
  role: OrganizationUserRole;
  status: "active" | "invited";
}
