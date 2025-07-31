import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { useCreateOrganization } from "#/hooks/mutation/use-create-organization";
import { useSelectedOrganizationId } from "#/context/use-selected-organization";

interface CreateNewOrganizationModalProps {
  onClose: () => void;
}

export function CreateNewOrganizationModal({
  onClose,
}: CreateNewOrganizationModalProps) {
  const { mutate: createOrganization } = useCreateOrganization();
  const { setOrgId } = useSelectedOrganizationId();

  const formAction = (formData: FormData) => {
    const orgName = formData.get("org-name")?.toString();
    if (orgName) {
      createOrganization(
        { name: orgName },
        {
          onSuccess: (newOrg) => {
            setOrgId(newOrg.id);
            onClose();
          },
        }
      );
    }
  };

  return (
    <ModalBackdrop onClose={onClose}>
      <div
        data-testid="create-org-modal"
        className="bg-base rounded-xl p-4 border w-sm border-tertiary items-start"
        onClick={(e) => e.stopPropagation()}
      >
        <form action={formAction}>
          <label>
            Organization Name
            <input data-testid="org-name-input" name="org-name" type="text" />
          </label>

          <button type="submit">Save</button>
          <button type="button" onClick={onClose}>
            Cancel
          </button>
        </form>
      </div>
    </ModalBackdrop>
  );
}
