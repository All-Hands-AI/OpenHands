import { useCreateOrganization } from "#/hooks/mutation/use-create-organization";

interface CreateNewOrganizationModalProps {
  onCancel: () => void;
}

export function CreateNewOrganizationModal({
  onCancel,
}: CreateNewOrganizationModalProps) {
  const { mutate: createOrganization } = useCreateOrganization();

  const formAction = (formData: FormData) => {
    const orgName = formData.get("org-name")?.toString();
    if (orgName) createOrganization({ name: orgName });
  };

  return (
    <div data-testid="create-org-modal">
      <form action={formAction}>
        <label>
          Organization Name
          <input data-testid="org-name-input" name="org-name" type="text" />
        </label>

        <button type="submit">Save</button>
        <button type="button" onClick={onCancel}>
          Cancel
        </button>
      </form>
    </div>
  );
}
