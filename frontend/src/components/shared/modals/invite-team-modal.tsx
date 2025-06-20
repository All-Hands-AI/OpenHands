import React from "react";
import { ModalBackdrop } from "./modal-backdrop";
import { BrandButton } from "#/components/features/settings/brand-button";
import { FiX, FiPlus, FiTrash2 } from "react-icons/fi";
import { cn } from "#/utils/utils";

interface InviteTeamModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (invites: InviteData[]) => void;
}

interface InviteData {
  email: string;
  role: string;
}

export function InviteTeamModal({ isOpen, onClose, onSubmit }: InviteTeamModalProps) {
  const [invites, setInvites] = React.useState<InviteData[]>([
    { email: "", role: "member" }
  ]);

  const roles = [
    { value: "admin", label: "Admin" },
    { value: "member", label: "Member" },
    { value: "viewer", label: "Viewer" }
  ];

  const addInvite = () => {
    setInvites([...invites, { email: "", role: "member" }]);
  };

  const removeInvite = (index: number) => {
    if (invites.length > 1) {
      setInvites(invites.filter((_, i) => i !== index));
    }
  };

  const updateInvite = (index: number, field: keyof InviteData, value: string) => {
    const newInvites = [...invites];
    newInvites[index] = { ...newInvites[index], [field]: value };
    setInvites(newInvites);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validInvites = invites.filter(invite => invite.email.trim() !== "");
    onSubmit(validInvites);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <ModalBackdrop onClose={onClose}>
      <div
        data-testid="invite-team-modal"
        className="bg-base border border-border rounded-xl shadow-xl w-full max-w-2xl mx-4"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6">
          <h2 className="text-xl font-semibold text-content">Invite Team Members</h2>
          <button
            onClick={onClose}
            className="text-content-secondary hover:text-content transition-colors"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 pb-6 pt-0">
          <div className="space-y-4">
            {invites.map((invite, index) => (
              <div key={index} className="flex gap-3 items-end">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-content mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    placeholder="Enter email address"
                    value={invite.email}
                    onChange={(e) => updateInvite(index, "email", e.target.value)}
                    className="w-full bg-input border border-border rounded-md px-3 py-2 text-sm text-content focus:outline-none focus:text-content focus:border-border focus:ring-1 focus:ring-border"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-content mb-2">
                    Role
                  </label>
                  <select
                    value={invite.role}
                    onChange={(e) => updateInvite(index, "role", e.target.value)}
                    className="bg-input border border-border rounded-md px-3 py-2 pr-10 text-sm text-content focus:outline-none focus:border-border focus:ring-1 focus:ring-border min-w-[120px]"
                  >
                    {roles.map((role) => (
                      <option key={role.value} value={role.value}>
                        {role.label}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="button"
                  onClick={() => removeInvite(index)}
                  className="p-2 text-content-secondary hover:text-content transition-colors"
                  disabled={invites.length === 1}
                >
                  <FiX className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex gap-3 justify-start mt-6">
            <button
              type="button"
              onClick={onClose}
              data-testid="cancel-invite-button"
              className="w-fit p-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-white text-black border border-border hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              data-testid="send-invite-button"
              className="w-fit p-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-black text-white hover:bg-gray-800"
            >
              Send Invites
            </button>
          </div>
        </form>
      </div>
    </ModalBackdrop>
  );
}
