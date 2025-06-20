import React from "react";
import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import { cn } from "#/utils/utils";
import { FiUsers, FiSettings, FiKey, FiLogOut, FiPlus, FiUser, FiShield, FiLayers, FiBox, FiChevronDown } from "react-icons/fi";
import { EventCarousel } from "#/components/features/settings/event-carousel";
import { InviteTeamModal } from "#/components/shared/modals/invite-team-modal";
import { NewOrganizationModal } from "#/components/shared/modals/new-organization-modal";

interface UserSettingsPopoverProps {
  isVisible: boolean;
  onLogout: () => void;
}

interface OrganizationDropdownProps {
  selectedOrg: string;
  onOrgChange: (org: string) => void;
  onCreateNewOrg: () => void;
}

function OrganizationDropdown({ selectedOrg, onOrgChange, onCreateNewOrg }: OrganizationDropdownProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const organizations = [
    { id: "personal", name: "Personal" },
    { id: "acme", name: "Acme Inc." },
  ];

  return (
    <div className="relative w-full" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full bg-transparent border border-border rounded-md px-3 py-2 text-sm text-content-secondary focus:outline-none focus:text-content focus:border-border focus:ring-1 focus:ring-border flex items-center justify-between"
      >
        <span>{selectedOrg}</span>
        <FiChevronDown className={cn("w-4 h-4 transition-transform", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-base border border-border rounded-md shadow-lg z-20">
          {organizations.map((org) => (
            <button
              key={org.id}
              onClick={() => {
                onOrgChange(org.name);
                setIsOpen(false);
              }}
              className="w-full px-3 py-2 text-sm text-content-secondary hover:bg-tertiary hover:text-content text-left first:rounded-t-md last:rounded-b-md"
            >
              {org.name}
            </button>
          ))}
          <hr className="border-border my-1" />
          <button
            onClick={() => {
              onCreateNewOrg();
              setIsOpen(false);
            }}
            className="w-full px-3 py-2 text-sm text-content-secondary hover:bg-tertiary hover:text-content text-left flex items-center gap-2"
          >
            <FiPlus className="w-4 h-4" />
            Create New Organization
          </button>
        </div>
      )}
    </div>
  );
}

export function UserSettingsPopover({
  isVisible,
  onLogout,
}: UserSettingsPopoverProps) {
  const { t } = useTranslation();
  const [selectedOrg, setSelectedOrg] = React.useState("Personal");
  const [isInviteModalOpen, setIsInviteModalOpen] = React.useState(false);
  const [isNewOrgModalOpen, setIsNewOrgModalOpen] = React.useState(false);
  const [isAnimating, setIsAnimating] = React.useState(false);

  React.useEffect(() => {
    if (isVisible) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isVisible]);

  const handleInviteSubmit = (invites: Array<{ email: string; role: string }>) => {
    // Handle invite submission here
    console.log("Sending invites:", invites);
    setIsInviteModalOpen(false);
  };

  const handleNewOrgSubmit = (organizationData: { name: string; description: string }) => {
    // Handle new organization creation here
    console.log("Creating organization:", organizationData);
    setIsNewOrgModalOpen(false);
  };

  if (!isVisible) return null;

  return (
    <>
      <div
        data-testid="user-settings-popover"
        className={`absolute bottom-full right-full md:left-full z-10 w-auto min-w-[56rem] bg-base rounded-2xl shadow-xl p-8 text-content mb-2 border border-border transition-all duration-300 ease-out ${
          isAnimating ? "opacity-0 translate-y-2" : "opacity-100 translate-y-0"
        }`}
      >
        <div className="flex gap-10 h-full">
          {/* Left Column - Account Settings */}
          <div className="w-[23rem] flex flex-col gap-4">
            {/* Heading */}
            <h2 className="text-xl font-semibold mb-1 text-content">Account</h2>
            {/* Org Dropdown */}
            <div className="w-full">
              <OrganizationDropdown
                selectedOrg={selectedOrg}
                onOrgChange={setSelectedOrg}
                onCreateNewOrg={() => setIsNewOrgModalOpen(true)}
              />
            </div>
            {/* Invite Team */}
            <button
              onClick={() => setIsInviteModalOpen(true)}
              className="flex items-center gap-3 text-content-secondary text-sm py-2 px-1 hover:bg-tertiary hover:text-content rounded transition-colors"
            >
              <FiUsers className="w-4 h-4" /> Invite Team
            </button>
            <hr className="border-border my-2" />
            {/* Main Menu */}
            <div className="flex flex-col gap-1">
              <Link to="/settings/account" className="flex items-center gap-3 text-content-secondary text-sm py-2 px-1 hover:bg-tertiary hover:text-content rounded transition-colors">
                <FiBox className="w-4 h-4" /> Manage Account
              </Link>
              <Link to="/settings/team" className="flex items-center gap-3 text-content-secondary text-sm py-2 px-1 hover:bg-tertiary hover:text-content rounded transition-colors">
                <FiUsers className="w-4 h-4" /> Manage Team
              </Link>
              <Link to="/settings/integrations" className="flex items-center gap-3 text-content-secondary text-sm py-2 px-1 hover:bg-tertiary hover:text-content rounded transition-colors">
                <FiLayers className="w-4 h-4" /> Integrations
              </Link>
              <Link to="/settings/api-keys" className="flex items-center gap-3 text-content-secondary text-sm py-2 px-1 hover:bg-tertiary hover:text-content rounded transition-colors">
                <FiKey className="w-4 h-4" /> API Keys
              </Link>
              <Link to="/settings/secrets" className="flex items-center gap-3 text-content-secondary text-sm py-2 px-1 hover:bg-tertiary hover:text-content rounded transition-colors">
                <FiShield className="w-4 h-4" /> Secrets
              </Link>
            </div>
            <hr className="border-border my-2" />
            {/* Secondary Menu */}
            <div className="flex flex-col gap-1">
              <Link to="/settings" className="flex items-center gap-3 text-content-secondary text-sm py-2 px-1 hover:bg-tertiary hover:text-content rounded transition-colors">
                <FiSettings className="w-4 h-4" /> Settings
              </Link>
              <button
                onClick={onLogout}
                className="flex items-center gap-3 text-content-secondary text-sm py-2 px-1 hover:bg-tertiary hover:text-content rounded transition-colors w-full text-left"
              >
                <FiLogOut className="w-4 h-4" /> Logout
              </button>
            </div>
          </div>

          {/* Right Column - Event Carousel */}
          <div className="hidden lg:block flex-1 h-full min-h-full">
            <EventCarousel />
          </div>
        </div>
      </div>

      {/* Invite Team Modal */}
      <InviteTeamModal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        onSubmit={handleInviteSubmit}
      />

      {/* New Organization Modal */}
      <NewOrganizationModal
        isOpen={isNewOrgModalOpen}
        onClose={() => setIsNewOrgModalOpen(false)}
        onSubmit={handleNewOrgSubmit}
      />
    </>
  );
}
