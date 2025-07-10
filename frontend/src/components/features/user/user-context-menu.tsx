import React from "react";
import ReactDOM from "react-dom";
import { useNavigate } from "react-router";
import {
  IoCardOutline,
  IoLogOutOutline,
  IoPersonAddOutline,
  IoPersonOutline,
} from "react-icons/io5";
import { FaCog } from "react-icons/fa";
import { FaPlus } from "react-icons/fa6";
import { useQuery } from "@tanstack/react-query";
import { useLogout } from "#/hooks/mutation/use-logout";
import { CreateNewOrganizationModal } from "../org/create-new-organization-modal";
import { OrganizationUserRole } from "#/types/org";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { InviteOrganizationMemberModal } from "../org/invite-organization-member-modal";
import { useSelectedOrganizationId } from "#/context/use-selected-organization";
import { useOrganization } from "#/hooks/query/use-organization";
import { organizationService } from "#/api/organization-service/organization-service.api";

const useOrganizations = () =>
  useQuery({
    queryKey: ["organizations"],
    queryFn: organizationService.getOrganizations,
  });

interface TempButtonProps {
  start: React.ReactNode;
  onClick: () => void;
}

function TempButton({
  start,
  children,
  onClick,
}: React.PropsWithChildren<TempButtonProps>) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-1 cursor-pointer hover:text-white w-full"
    >
      {start}
      {children}
    </button>
  );
}

function TempDivider() {
  return <div className="h-[1px] w-full bg-tertiary my-1.5" />;
}

interface UserContextMenuProps {
  type: OrganizationUserRole;
  onClose: () => void;
}

export function UserContextMenu({ type, onClose }: UserContextMenuProps) {
  const navigate = useNavigate();
  const { orgId, setOrgId } = useSelectedOrganizationId();
  const { data: organizations } = useOrganizations();
  const { data: organization } = useOrganization();
  const { mutate: logout } = useLogout();
  const ref = useClickOutsideElement<HTMLDivElement>(onClose);

  const [orgModalIsOpen, setOrgModalIsOpen] = React.useState(false);
  const [inviteMemberModalIsOpen, setInviteMemberModalIsOpen] =
    React.useState(false);

  const isUser = type === "user";
  const isSuperAdmin = type === "superadmin";

  const handleLogout = () => {
    logout();
    onClose();
  };

  const handleSettingsClick = () => {
    navigate("/settings");
    onClose();
  };

  const handleInviteMemberClick = () => {
    setInviteMemberModalIsOpen(true);
  };

  const handleManageTeamClick = () => {
    navigate("/settings/team");
    onClose();
  };

  const handleManageAccountClick = () => {
    navigate("/settings/org");
    onClose();
  };

  const handleCreateNewOrgClick = () => {
    setOrgModalIsOpen(true);
    onClose();
  };

  return (
    <div
      data-testid="user-context-menu"
      ref={ref}
      className={cn(
        "w-full flex flex-col gap-3 bg-base border border-tertiary rounded-xl p-6",
        "text-sm text-basic",
      )}
    >
      {orgModalIsOpen &&
        ReactDOM.createPortal(
          <CreateNewOrganizationModal
            onCancel={() => setOrgModalIsOpen(false)}
          />,
          document.getElementById("portal-root") || document.body,
        )}
      {inviteMemberModalIsOpen &&
        ReactDOM.createPortal(
          <InviteOrganizationMemberModal
            onClose={() => setInviteMemberModalIsOpen(false)}
          />,
          document.getElementById("portal-root") || document.body,
        )}

      <h3 className="text-lg font-semibold text-white">Account</h3>

      <div className="flex flex-col items-start gap-2">
        <div data-testid="org-selector" className="w-full">
          {organization?.name || "User Organization"} {orgId}
        </div>
        {organizations?.map((org) => (
          <button
            key={org.id}
            type="button"
            onClick={async () => {
              setOrgId(org.id);
            }}
            className="w-full text-left hover:text-white"
          >
            {org.name}
          </button>
        ))}

        {!isUser && (
          <>
            <TempButton
              onClick={handleInviteMemberClick}
              start={<IoPersonAddOutline className="text-white" size={14} />}
            >
              Invite Team
            </TempButton>

            <TempDivider />

            <TempButton
              onClick={handleManageAccountClick}
              start={<IoCardOutline className="text-white" size={14} />}
            >
              Manage Account
            </TempButton>
            <TempButton
              onClick={handleManageTeamClick}
              start={<IoPersonOutline className="text-white" size={14} />}
            >
              Manage Team
            </TempButton>
          </>
        )}

        <TempDivider />

        <TempButton
          onClick={handleSettingsClick}
          start={<FaCog className="text-white" size={14} />}
        >
          Settings
        </TempButton>

        {isSuperAdmin && (
          <TempButton
            onClick={handleCreateNewOrgClick}
            start={<FaPlus className="text-white" size={14} />}
          >
            Create New Organization
          </TempButton>
        )}

        <TempButton
          onClick={handleLogout}
          start={<IoLogOutOutline className="text-white" size={14} />}
        >
          Logout
        </TempButton>
      </div>
    </div>
  );
}
