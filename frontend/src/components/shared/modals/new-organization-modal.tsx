import React from "react";
import { ModalBackdrop } from "./modal-backdrop";
import { BrandButton } from "#/components/features/settings/brand-button";
import { FiX } from "react-icons/fi";

interface NewOrganizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (organizationData: OrganizationData) => void;
}

interface OrganizationData {
  name: string;
  description: string;
}

export function NewOrganizationModal({ isOpen, onClose, onSubmit }: NewOrganizationModalProps) {
  const [formData, setFormData] = React.useState<OrganizationData>({
    name: "",
    description: ""
  });

  const handleInputChange = (field: keyof OrganizationData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name.trim()) {
      onSubmit(formData);
      onClose();
      // Reset form
      setFormData({ name: "", description: "" });
    }
  };

  const handleClose = () => {
    onClose();
    // Reset form
    setFormData({ name: "", description: "" });
  };

  if (!isOpen) return null;

  return (
    <ModalBackdrop onClose={handleClose}>
      <div
        data-testid="new-organization-modal"
        className="bg-base border border-border rounded-xl shadow-xl w-full max-w-md mx-4"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6">
          <h2 className="text-xl font-semibold text-content">Create New Organization</h2>
          <button
            onClick={handleClose}
            className="text-content-secondary hover:text-content transition-colors"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 pb-6 pt-0">
          <div className="space-y-4">
            <div>
              <label htmlFor="org-name" className="block text-sm font-medium text-content mb-2">
                Organization Name
              </label>
              <input
                id="org-name"
                type="text"
                placeholder="Enter organization name"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                className="w-full bg-input border border-border rounded-md px-3 py-2 text-sm text-content focus:outline-none focus:text-content focus:border-border focus:ring-1 focus:ring-border"
                required
              />
            </div>

            <div>
              <label htmlFor="org-description" className="block text-sm font-medium text-content mb-2">
                Description (Optional)
              </label>
              <textarea
                id="org-description"
                placeholder="Enter organization description"
                value={formData.description}
                onChange={(e) => handleInputChange("description", e.target.value)}
                rows={3}
                className="w-full bg-input border border-border rounded-md px-3 py-2 text-sm text-content focus:outline-none focus:text-content focus:border-border focus:ring-1 focus:ring-border resize-none"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex gap-3 justify-start mt-6">
            <BrandButton
              testId="cancel-organization-button"
              type="button"
              onClick={handleClose}
              variant="secondary"
            >
              Cancel
            </BrandButton>
            <BrandButton
              testId="create-organization-button"
              type="submit"
              variant="primary"
            >
              Create Organization
            </BrandButton>
          </div>
        </form>
      </div>
    </ModalBackdrop>
  );
}
